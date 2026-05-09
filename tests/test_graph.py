"""Phase 4 tests: graph builder, communities, audit, menu primitives."""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest


@pytest.fixture
def tmp_brain(monkeypatch: pytest.MonkeyPatch) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="medbrain-graph-"))
    monkeypatch.setenv("BRAIN_DIR", str(tmp))
    import importlib

    import medbrain.config as config_mod
    import medbrain.db as db_mod

    importlib.reload(config_mod)
    importlib.reload(db_mod)
    return tmp


def _seed_claims(tmp_brain: Path) -> None:
    """Seed a small malaria knowledge graph: 3 entities, 4 claims."""
    from medbrain.db import init_schema, session_scope
    from medbrain.enums import (
        Certainty,
        ClaimStatus,
        EvidenceGrade,
        Predicate,
        SourceType,
    )
    from medbrain.models import Claim, Source

    init_schema()
    with session_scope() as sess:
        src = Source(source_type=SourceType.PUBMED, external_id="PMID:G1", title="Seed paper")
        sess.add(src)
        sess.flush()
        # 1: artemether-lumefantrine treats falciparum
        sess.add(
            Claim(
                subject_text="artemether-lumefantrine",
                predicate=Predicate.TREATS,
                object_text="uncomplicated falciparum",
                qualifiers={
                    "population": {"region": "West Africa", "pregnancy": "second_third_trimester"},
                    "setting": {"endemic_status": "endemic", "care_level": "outpatient"},
                },
                certainty=Certainty.HIGH,
                source_id=src.source_id,
                evidence_grade=EvidenceGrade.RCT,
                status=ClaimStatus.AUTO_PROMOTED,
            )
        )
        # 2: P. falciparum resists artemisinin (Mekong)
        sess.add(
            Claim(
                subject_text="P. falciparum",
                predicate=Predicate.RESISTS,
                object_text="artemisinin",
                qualifiers={"population": {"region": "Greater Mekong"}},
                certainty=Certainty.MODERATE,
                source_id=src.source_id,
                evidence_grade=EvidenceGrade.COHORT,
                status=ClaimStatus.AUTO_PROMOTED,
            )
        )
        # 3: artemether-lumefantrine causes uncomplicated falciparum (CONTRADICTS #1)
        sess.add(
            Claim(
                subject_text="artemether-lumefantrine",
                predicate=Predicate.CAUSES,
                object_text="uncomplicated falciparum",
                qualifiers={},
                certainty=Certainty.LOW,
                source_id=src.source_id,
                evidence_grade=EvidenceGrade.CASE_REPORT,
                status=ClaimStatus.AUTO_PROMOTED,
            )
        )
        # 4: chloroquine treats vivax
        sess.add(
            Claim(
                subject_text="chloroquine",
                predicate=Predicate.TREATS,
                object_text="P. vivax",
                qualifiers={
                    "population": {"region": "South America"},
                    "setting": {"endemic_status": "endemic"},
                },
                certainty=Certainty.HIGH,
                source_id=src.source_id,
                evidence_grade=EvidenceGrade.GUIDELINE,
                status=ClaimStatus.AUTO_PROMOTED,
            )
        )


def test_build_graph_nodes_and_edges(tmp_brain: Path) -> None:
    _seed_claims(tmp_brain)
    from medbrain.db import session_scope
    from medbrain.graph.builder import build_graph

    with session_scope() as sess:
        g = build_graph(sess)

    assert g.number_of_nodes() == 6  # AL, uncomplicated falciparum, P.fal, artemisinin, chloroquine, P.vivax
    assert g.number_of_edges() == 4
    assert "artemether-lumefantrine" in g.nodes
    assert "p. falciparum" in g.nodes


def test_communities_detected(tmp_brain: Path) -> None:
    _seed_claims(tmp_brain)
    from medbrain.db import session_scope
    from medbrain.graph.builder import build_graph
    from medbrain.graph.communities import detect

    with session_scope() as sess:
        g = build_graph(sess)
    comms = detect(g)
    assert len(comms) >= 1
    for c in comms:
        assert c["community_id"].startswith("c")
        assert c["size"] == len(c["members"])


def test_audit_finds_contradiction(tmp_brain: Path) -> None:
    _seed_claims(tmp_brain)
    from medbrain.db import session_scope
    from medbrain.graph.audit import audit
    from medbrain.graph.builder import build_graph

    with session_scope() as sess:
        g = build_graph(sess)
    a = audit(g)
    assert a["stats"]["contradiction_count"] >= 1
    pair = a["contradictions"][0]
    assert pair["subject"] == "artemether-lumefantrine"
    assert pair["object"] == "uncomplicated falciparum"
    assert "treats" in pair["predicates"]
    assert "causes" in pair["predicates"]


def test_run_graphify_writes_artifacts(tmp_brain: Path) -> None:
    _seed_claims(tmp_brain)
    from medbrain.agents.graphify import run_graphify
    from medbrain.config import GRAPH_DIR

    result = run_graphify()
    assert result.errors == []
    assert (GRAPH_DIR / "graph.json").exists()
    assert (GRAPH_DIR / "communities.json").exists()
    assert (GRAPH_DIR / "audit.json").exists()
    assert (GRAPH_DIR / "version.json").exists()
    assert result.node_count == 6
    assert result.edge_count == 4


# ---------- menu primitives ----------


def test_menu_lookup_returns_neighbors(tmp_brain: Path) -> None:
    _seed_claims(tmp_brain)
    from medbrain.agents.graphify import run_graphify
    from medbrain.api import menu

    run_graphify()
    out = menu.lookup("artemether-lumefantrine")
    assert out["primitive"] == "lookup"
    assert out["data"]["node"] is not None
    neighbors = {n["id"] for n in out["data"]["neighbors"]}
    assert "uncomplicated falciparum" in neighbors


def test_menu_neighborhood_two_hops(tmp_brain: Path) -> None:
    _seed_claims(tmp_brain)
    from medbrain.agents.graphify import run_graphify
    from medbrain.api import menu

    run_graphify()
    out = menu.neighborhood("p. falciparum", hops=2)
    node_ids = {n["id"] for n in out["data"]["nodes"]}
    assert "p. falciparum" in node_ids
    assert "artemisinin" in node_ids


def test_menu_path_finds_route(tmp_brain: Path) -> None:
    _seed_claims(tmp_brain)
    from medbrain.agents.graphify import run_graphify
    from medbrain.api import menu

    run_graphify()
    out = menu.path("artemether-lumefantrine", "uncomplicated falciparum")
    assert len(out["data"]["paths"]) >= 1
    assert out["data"]["paths"][0][0]["id"] == "artemether-lumefantrine"
    assert out["data"]["paths"][0][-1]["id"] == "uncomplicated falciparum"


def test_menu_scoped_filters_region(tmp_brain: Path) -> None:
    _seed_claims(tmp_brain)
    from medbrain.agents.graphify import run_graphify
    from medbrain.api import menu

    run_graphify()
    out = menu.scoped(population_region="Greater Mekong", current_only=True)
    edges = out["data"]["edges"]
    # Only the falciparum-resists-artemisinin claim has Greater Mekong region.
    assert len(edges) == 1
    assert edges[0]["predicate"] == "resists"


def test_menu_scoped_min_certainty(tmp_brain: Path) -> None:
    _seed_claims(tmp_brain)
    from medbrain.agents.graphify import run_graphify
    from medbrain.api import menu

    run_graphify()
    out = menu.scoped(min_certainty="high", current_only=True)
    edges = out["data"]["edges"]
    grades_certs = {(e["predicate"], e["certainty"]) for e in edges}
    # Two HIGH-certainty claims: AL treats falciparum, chloroquine treats vivax.
    assert len(edges) == 2
    assert all(c == "high" for (_, c) in grades_certs)


def test_menu_recent_filters_by_date(tmp_brain: Path) -> None:
    _seed_claims(tmp_brain)
    from medbrain.agents.graphify import run_graphify
    from medbrain.api import menu

    run_graphify()
    future = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    out = menu.recent(future)
    assert out["data"]["nodes"] == []
    assert out["data"]["edges"] == []

    past = "2000-01-01T00:00:00"
    out = menu.recent(past)
    assert len(out["data"]["nodes"]) == 6
    assert len(out["data"]["edges"]) == 4


def test_menu_gaps_returns_audit(tmp_brain: Path) -> None:
    _seed_claims(tmp_brain)
    from medbrain.agents.graphify import run_graphify
    from medbrain.api import menu

    run_graphify()
    out = menu.gaps()
    assert "audit" in out["data"]
    assert out["data"]["audit"]["stats"]["contradiction_count"] >= 1


def test_menu_evidence_pack_returns_provenance(tmp_brain: Path) -> None:
    _seed_claims(tmp_brain)
    from medbrain.agents.graphify import run_graphify
    from medbrain.api import menu
    from medbrain.db import session_scope
    from sqlalchemy import select
    from medbrain.models import Claim

    run_graphify()
    with session_scope() as sess:
        first_id = sess.execute(select(Claim.claim_id).limit(1)).scalar_one()

    out = menu.evidence_pack([first_id])
    assert len(out["data"]["claims"]) == 1
    c = out["data"]["claims"][0]
    assert c["claim_id"] == first_id
    assert c["source"]["external_id"] == "PMID:G1"


def test_menu_lookup_missing_entity(tmp_brain: Path) -> None:
    _seed_claims(tmp_brain)
    from medbrain.agents.graphify import run_graphify
    from medbrain.api import menu

    run_graphify()
    out = menu.lookup("nonexistent_entity_xyz")
    assert out["data"]["node"] is None
    assert out["data"]["neighbors"] == []


def test_menu_envelope_shape() -> None:
    from medbrain.api.menu import envelope

    e = envelope("test", {"a": 1}, {"x": 2})
    assert e["version"] == "1.0"
    assert e["primitive"] == "test"
    assert e["args"] == {"a": 1}
    assert e["data"] == {"x": 2}
    assert e["derivative_included"] is False
    assert "generated_at" in e
