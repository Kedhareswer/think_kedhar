"""Graphify agent: rebuild graph artifacts from current SQL claims.

Per Phase 4 of the build plan. Runs hourly after Brain (or on-demand).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from medbrain.db import session_scope
from medbrain.graph.audit import audit
from medbrain.graph.builder import build_graph
from medbrain.graph.communities import detect
from medbrain.graph.persist import write_artifacts


@dataclass
class GraphifyResult:
    started_at: datetime
    completed_at: datetime | None = None
    node_count: int = 0
    edge_count: int = 0
    community_count: int = 0
    isolated_count: int = 0
    contradiction_count: int = 0
    errors: list[str] = field(default_factory=list)


def run_graphify(*, include_review: bool = False) -> GraphifyResult:
    started = datetime.now(UTC)
    result = GraphifyResult(started_at=started)
    try:
        with session_scope() as sess:
            g = build_graph(sess, include_review=include_review)
        comms = detect(g)
        audit_data = audit(g)
        write_artifacts(g, comms, audit_data)

        result.node_count = g.number_of_nodes()
        result.edge_count = g.number_of_edges()
        result.community_count = len(comms)
        result.isolated_count = audit_data.get("stats", {}).get("isolated_count", 0)
        result.contradiction_count = audit_data.get("stats", {}).get("contradiction_count", 0)
    except Exception as e:
        result.errors.append(str(e))
    result.completed_at = datetime.now(UTC)
    return result
