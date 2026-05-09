"""Build a property MultiDiGraph from SQL claims.

Nodes  = entities (subject_text or object_text), normalized to lowercase key.
Edges  = one per claim. Attrs include claim_id, predicate, qualifiers, certainty,
         evidence_grade, status, supersedes_id, valid_from/until, source_id, ingested_at.
"""

from __future__ import annotations

from datetime import UTC, datetime

import networkx as nx
from sqlalchemy import select
from sqlalchemy.orm import Session

from medbrain.enums import ClaimStatus
from medbrain.models import Claim, Source


def _norm(name: str) -> str:
    return (name or "").strip().lower()


def build_graph(sess: Session, *, include_review: bool = False) -> nx.MultiDiGraph:
    """Read claims from SQL and build the property graph.

    By default excludes pending_review and rejected/archived claims so the
    retrieval graph reflects only auto-promoted (live) knowledge. Pass
    include_review=True to surface the queue in the graph for inspection.
    """
    g: nx.MultiDiGraph = nx.MultiDiGraph()

    statuses = [ClaimStatus.AUTO_PROMOTED]
    if include_review:
        statuses.append(ClaimStatus.PENDING_REVIEW)

    rows = sess.execute(
        select(Claim, Source)
        .join(Source, Claim.source_id == Source.source_id, isouter=True)
        .where(Claim.status.in_(statuses))
    ).all()

    for claim, src in rows:
        s_key = _norm(claim.subject_text)
        o_key = _norm(claim.object_text)
        if not s_key or not o_key:
            continue

        for key, label in ((s_key, claim.subject_text), (o_key, claim.object_text)):
            if key not in g.nodes:
                g.add_node(
                    key,
                    label=label,
                    first_seen=claim.ingested_at.isoformat() if claim.ingested_at else None,
                    last_updated=claim.ingested_at.isoformat() if claim.ingested_at else None,
                    claim_count=0,
                )
            else:
                if claim.ingested_at and (
                    g.nodes[key]["last_updated"] is None
                    or claim.ingested_at.isoformat() > g.nodes[key]["last_updated"]
                ):
                    g.nodes[key]["last_updated"] = claim.ingested_at.isoformat()
            g.nodes[key]["claim_count"] += 1

        g.add_edge(
            s_key,
            o_key,
            key=claim.claim_id,
            claim_id=claim.claim_id,
            predicate=claim.predicate.value,
            qualifiers=claim.qualifiers or {},
            certainty=claim.certainty.value,
            evidence_grade=claim.evidence_grade.value,
            status=claim.status.value,
            supersedes_id=claim.supersedes_id,
            valid_from=claim.valid_from.isoformat() if claim.valid_from else None,
            valid_until=claim.valid_until.isoformat() if claim.valid_until else None,
            current=(claim.valid_until is None),
            source_id=claim.source_id,
            source_external_id=src.external_id if src else None,
            source_url=src.url if src else None,
            ingested_at=claim.ingested_at.isoformat() if claim.ingested_at else None,
        )

    return g


def to_jsonable(g: nx.MultiDiGraph) -> dict:
    """Serialize MultiDiGraph to a plain JSON-able dict (link-data format)."""
    nodes = []
    for n, attrs in g.nodes(data=True):
        nodes.append({"id": n, **attrs})
    edges = []
    for u, v, k, attrs in g.edges(keys=True, data=True):
        edges.append({"source": u, "target": v, "key": k, **attrs})
    return {
        "directed": True,
        "multigraph": True,
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "node_count": g.number_of_nodes(),
            "edge_count": g.number_of_edges(),
            "generated_at": datetime.now(UTC).isoformat(),
        },
    }


def from_jsonable(data: dict) -> nx.MultiDiGraph:
    g: nx.MultiDiGraph = nx.MultiDiGraph()
    for node in data.get("nodes", []):
        n = node.pop("id")
        g.add_node(n, **node)
    for edge in data.get("edges", []):
        s = edge.pop("source")
        t = edge.pop("target")
        k = edge.pop("key", None)
        g.add_edge(s, t, key=k, **edge)
    return g
