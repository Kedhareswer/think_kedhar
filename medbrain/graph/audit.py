"""Audit pass: identify sparse regions, isolated nodes, low-grade-only entities,
and contradictions. Output is read by the `gaps` retrieval primitive.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

import networkx as nx

from medbrain.enums import HIGH_GRADES, EvidenceGrade


def audit(g: nx.MultiDiGraph) -> dict:
    if g.number_of_nodes() == 0:
        return {"isolated": [], "low_grade_only": [], "contradictions": [], "stub_entities": []}

    high_set = {gg.value for gg in HIGH_GRADES}

    # Isolated: no incoming or outgoing edges.
    isolated = sorted(
        n for n in g.nodes() if g.in_degree(n) == 0 and g.out_degree(n) == 0
    )

    # Low-grade-only: every claim involving the node has grade outside HIGH_GRADES.
    low_grade_only: list[str] = []
    for n in g.nodes():
        edges = list(g.in_edges(n, data=True)) + list(g.out_edges(n, data=True))
        if not edges:
            continue
        grades = {e[-1].get("evidence_grade") for e in edges}
        if not (grades & high_set):
            low_grade_only.append(n)
    low_grade_only.sort()

    # Stub entities: degree <= 2.
    stub_entities = sorted(n for n in g.nodes() if g.degree(n) <= 2)

    # Contradictions: same (subject, object) pair with opposing predicates.
    pair_predicates: dict[tuple[str, str], set[str]] = defaultdict(set)
    pair_claim_ids: dict[tuple[str, str], list[str]] = defaultdict(list)
    for u, v, attrs in g.edges(data=True):
        pair_predicates[(u, v)].add(attrs.get("predicate"))
        pair_claim_ids[(u, v)].append(attrs.get("claim_id"))

    opposing = {
        ("treats", "causes"),
        ("causes", "treats"),
        ("prevents", "causes"),
        ("causes", "prevents"),
        ("recommends", "contraindicates"),
        ("contraindicates", "recommends"),
    }
    contradictions: list[dict] = []
    for (u, v), preds in pair_predicates.items():
        for a in preds:
            for b in preds:
                if a != b and (a, b) in opposing:
                    contradictions.append(
                        {
                            "subject": u,
                            "object": v,
                            "predicates": sorted(preds),
                            "claim_ids": pair_claim_ids[(u, v)],
                        }
                    )
                    break

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "isolated": isolated,
        "low_grade_only": low_grade_only,
        "stub_entities": stub_entities,
        "contradictions": contradictions,
        "stats": {
            "isolated_count": len(isolated),
            "low_grade_only_count": len(low_grade_only),
            "stub_count": len(stub_entities),
            "contradiction_count": len(contradictions),
        },
    }
