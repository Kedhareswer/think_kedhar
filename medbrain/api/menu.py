"""Retrieval menu: 8 named primitives over the cached knowledge graph.

All primitives return a consistent envelope (see envelope() at the bottom).
Reads from brain/graph/* artifacts. The Graphify agent rebuilds them.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import networkx as nx
from sqlalchemy import select

from medbrain import config
from medbrain.db import session_scope
from medbrain.dream.decay import touch as _touch_salience
from medbrain.graph.persist import read_audit, read_communities, read_graph
from medbrain.models import Claim, Source
from medbrain.regen.slug import slugify

API_VERSION = "1.0"


class MenuError(Exception):
    pass


# ---------------- helpers ----------------


def _norm(name: str) -> str:
    return (name or "").strip().lower()


def _require_graph() -> nx.MultiDiGraph:
    g = read_graph()
    if g is None:
        raise MenuError("graph artifacts not built yet — run scripts/graphify_run.py")
    return g


def _node_payload(g: nx.MultiDiGraph, n: str) -> dict:
    if n not in g.nodes:
        return {"id": n, "missing": True}
    out = {"id": n, **dict(g.nodes[n])}
    out["concept_md"] = _concept_md_path(n)
    return out


def _edge_payload(u: str, v: str, k: Any, attrs: dict) -> dict:
    return {"source": u, "target": v, "key": k, **attrs}


def _concept_md_path(entity_key: str) -> str | None:
    label = entity_key
    p = config.CONCEPTS_DIR / f"{slugify(label)}.md"
    if p.exists():
        try:
            return str(p.relative_to(config.BRAIN_DIR)).replace("\\", "/")
        except ValueError:
            return str(p)
    return None


def envelope(primitive: str, args: dict, data: dict, *, derivative_included: bool = False) -> dict:
    return {
        "version": API_VERSION,
        "primitive": primitive,
        "args": args,
        "data": data,
        "derivative_included": derivative_included,
        "generated_at": datetime.now(UTC).isoformat(),
    }


# ---------------- primitives ----------------


def lookup(entity: str) -> dict:
    g = _require_graph()
    key = _norm(entity)
    _touch_salience(key)
    if key not in g.nodes:
        return envelope("lookup", {"entity": entity}, {"node": None, "neighbors": [], "edges": []})
    neighbors = sorted(set(list(g.successors(key)) + list(g.predecessors(key))))
    edges = []
    for u, v, k, a in g.in_edges(key, keys=True, data=True):
        edges.append(_edge_payload(u, v, k, a))
    for u, v, k, a in g.out_edges(key, keys=True, data=True):
        edges.append(_edge_payload(u, v, k, a))
    return envelope(
        "lookup",
        {"entity": entity},
        {
            "node": _node_payload(g, key),
            "neighbors": [_node_payload(g, n) for n in neighbors],
            "edges": edges,
        },
    )


def neighborhood(entity: str, hops: int = 1) -> dict:
    if hops < 1 or hops > 3:
        raise MenuError("hops must be between 1 and 3")
    g = _require_graph()
    key = _norm(entity)
    _touch_salience(key)
    if key not in g.nodes:
        return envelope(
            "neighborhood",
            {"entity": entity, "hops": hops},
            {"nodes": [], "edges": []},
        )
    h = nx.Graph(g)  # undirected for ego_graph
    sub = nx.ego_graph(h, key, radius=hops)
    nodes = [_node_payload(g, n) for n in sub.nodes()]
    seen_keys: set[tuple] = set()
    edges = []
    for n in sub.nodes():
        for u, v, k, a in g.in_edges(n, keys=True, data=True):
            if u in sub and v in sub and (u, v, k) not in seen_keys:
                edges.append(_edge_payload(u, v, k, a))
                seen_keys.add((u, v, k))
        for u, v, k, a in g.out_edges(n, keys=True, data=True):
            if u in sub and v in sub and (u, v, k) not in seen_keys:
                edges.append(_edge_payload(u, v, k, a))
                seen_keys.add((u, v, k))
    return envelope(
        "neighborhood",
        {"entity": entity, "hops": hops},
        {"nodes": nodes, "edges": edges},
    )


def path(entity_a: str, entity_b: str, *, max_paths: int = 3) -> dict:
    g = _require_graph()
    a, b = _norm(entity_a), _norm(entity_b)
    if a not in g.nodes or b not in g.nodes:
        return envelope("path", {"from": entity_a, "to": entity_b}, {"paths": []})
    h = nx.Graph(g)
    paths_out: list[list[dict]] = []
    try:
        for i, p in enumerate(nx.all_shortest_paths(h, a, b)):
            if i >= max_paths:
                break
            paths_out.append([_node_payload(g, n) for n in p])
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        pass
    return envelope("path", {"from": entity_a, "to": entity_b}, {"paths": paths_out})


def community(community_id: str | None = None, topic: str | None = None) -> dict:
    comms = read_communities()
    selected: dict | None = None
    if community_id:
        selected = next((c for c in comms if c["community_id"] == community_id), None)
    elif topic:
        topic_l = topic.strip().lower()
        for c in comms:
            members_l = [m.lower() for m in c.get("members", [])]
            if topic_l in c["label"].lower() or topic_l in members_l:
                selected = c
                break
    if selected is None:
        return envelope(
            "community",
            {"community_id": community_id, "topic": topic},
            {"community": None, "available": [c["community_id"] for c in comms]},
        )
    g = _require_graph()
    members_payload = [_node_payload(g, n) for n in selected["members"]]
    return envelope(
        "community",
        {"community_id": community_id, "topic": topic},
        {"community": selected, "members": members_payload},
    )


def scoped(
    *,
    population_region: str | None = None,
    population_pregnancy: str | None = None,
    setting_endemic: str | None = None,
    setting_care_level: str | None = None,
    min_certainty: str | None = None,
    current_only: bool = True,
) -> dict:
    g = _require_graph()
    cert_rank = {"very_low": 0, "low": 1, "moderate": 2, "high": 3}
    floor = cert_rank.get((min_certainty or "").lower(), -1)

    nodes_in: set[str] = set()
    edges_out: list[dict] = []
    for u, v, k, a in g.edges(keys=True, data=True):
        if current_only and not a.get("current", True):
            continue
        if floor >= 0 and cert_rank.get(a.get("certainty", "moderate"), 2) < floor:
            continue
        q = a.get("qualifiers") or {}
        pop = (q.get("population") or {}) if isinstance(q, dict) else {}
        setting = (q.get("setting") or {}) if isinstance(q, dict) else {}
        if population_region and (pop.get("region") or "").lower() != population_region.lower():
            continue
        if (
            population_pregnancy
            and (pop.get("pregnancy") or "").lower() != population_pregnancy.lower()
        ):
            continue
        if (
            setting_endemic
            and (setting.get("endemic_status") or "").lower() != setting_endemic.lower()
        ):
            continue
        if (
            setting_care_level
            and (setting.get("care_level") or "").lower() != setting_care_level.lower()
        ):
            continue
        edges_out.append(_edge_payload(u, v, k, a))
        nodes_in.add(u)
        nodes_in.add(v)

    return envelope(
        "scoped",
        {
            "population_region": population_region,
            "population_pregnancy": population_pregnancy,
            "setting_endemic": setting_endemic,
            "setting_care_level": setting_care_level,
            "min_certainty": min_certainty,
            "current_only": current_only,
        },
        {
            "nodes": [_node_payload(g, n) for n in sorted(nodes_in)],
            "edges": edges_out,
        },
    )


def recent(since_iso: str) -> dict:
    g = _require_graph()
    nodes_out = []
    edges_out = []
    cutoff = since_iso
    for n, attrs in g.nodes(data=True):
        last = attrs.get("last_updated") or ""
        if last >= cutoff:
            nodes_out.append({"id": n, **attrs, "concept_md": _concept_md_path(n)})
    for u, v, k, a in g.edges(keys=True, data=True):
        ing = a.get("ingested_at") or ""
        if ing >= cutoff:
            edges_out.append(_edge_payload(u, v, k, a))
    return envelope(
        "recent",
        {"since": since_iso},
        {"nodes": nodes_out, "edges": edges_out},
    )


def gaps() -> dict:
    audit = read_audit()
    questions_path = config.QUESTIONS_FILE
    questions_text = (
        questions_path.read_text(encoding="utf-8") if questions_path.exists() else ""
    )
    return envelope(
        "gaps",
        {},
        {"audit": audit, "questions_md": questions_text},
    )


def evidence_pack(claim_ids: list[str]) -> dict:
    out: list[dict] = []
    if not claim_ids:
        return envelope("evidence_pack", {"claim_ids": []}, {"claims": []})
    touched: set[str] = set()
    with session_scope() as sess:
        rows = sess.execute(
            select(Claim, Source)
            .join(Source, Claim.source_id == Source.source_id, isouter=True)
            .where(Claim.claim_id.in_(claim_ids))
        ).all()
        for claim, src in rows:
            for key in ((claim.subject_text or "").lower(), (claim.object_text or "").lower()):
                if key and key not in touched:
                    touched.add(key)
            out.append(
                {
                    "claim_id": claim.claim_id,
                    "subject": claim.subject_text,
                    "predicate": claim.predicate.value,
                    "object": claim.object_text,
                    "qualifiers": claim.qualifiers or {},
                    "certainty": claim.certainty.value,
                    "evidence_grade": claim.evidence_grade.value,
                    "status": claim.status.value,
                    "supersedes_id": claim.supersedes_id,
                    "valid_from": claim.valid_from.isoformat() if claim.valid_from else None,
                    "valid_until": claim.valid_until.isoformat() if claim.valid_until else None,
                    "current": claim.valid_until is None,
                    "ingested_at": claim.ingested_at.isoformat() if claim.ingested_at else None,
                    "source": (
                        {
                            "type": src.source_type.value,
                            "external_id": src.external_id,
                            "title": src.title,
                            "url": src.url,
                            "publication_date": src.publication_date.isoformat()
                            if src.publication_date
                            else None,
                        }
                        if src
                        else None
                    ),
                }
            )
    for key in touched:
        _touch_salience(key)
    return envelope("evidence_pack", {"claim_ids": claim_ids}, {"claims": out})
