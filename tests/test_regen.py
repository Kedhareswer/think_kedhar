"""Phase 2 tests: slug, atomic write, topic mapper, regen coordinator (mocked LLM)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from medbrain.enums import (
    Certainty,
    ClaimStatus,
    EvidenceGrade,
    Predicate,
    SourceType,
)
from medbrain.regen.atomic import atomic_write_text
from medbrain.regen.slug import slugify
from medbrain.regen.topics import topics_for


# ---------- slug ----------


def test_slug_basic():
    assert slugify("Chloroquine") == "chloroquine"
    assert slugify("P. falciparum") == "p-falciparum"
    assert slugify("Artemether-Lumefantrine") == "artemether-lumefantrine"


def test_slug_unicode_and_punctuation():
    assert slugify("β-lactam") == "lactam"  # beta dropped by ASCII fold
    assert slugify("  ACE  Inhibitors!  ") == "ace-inhibitors"
    assert slugify("///") == "unknown"
    assert slugify("") == "unknown"


def test_slug_truncates_max_len():
    long = "a" * 200
    assert len(slugify(long, max_len=80)) == 80


# ---------- atomic write ----------


def test_atomic_write_creates_dirs_and_replaces():
    tmp = Path(tempfile.mkdtemp(prefix="medbrain-atomic-"))
    target = tmp / "deep" / "nested" / "out.md"
    atomic_write_text(target, "first\n")
    assert target.read_text() == "first\n"
    atomic_write_text(target, "second\n")
    assert target.read_text() == "second\n"
    # No leftover .tmp file
    assert list(target.parent.glob("*.tmp")) == []


# ---------- predicate -> topic mapping ----------


def test_topic_mapping_treats_recommends_to_treatment():
    assert topics_for(Predicate.TREATS, "artemether-lumefantrine", "uncomplicated falciparum") == [
        "treatment/uncomplicated-falciparum"
    ]
    assert topics_for(Predicate.RECOMMENDS, "WHO", "tafenoquine") == ["treatment/tafenoquine"]


def test_topic_mapping_resists_to_resistance():
    assert topics_for(Predicate.RESISTS, "P. falciparum", "artemisinin") == [
        "resistance/artemisinin"
    ]


def test_topic_mapping_contraindicates_to_safety():
    assert topics_for(Predicate.CONTRAINDICATES, "primaquine", "G6PD deficiency") == [
        "safety/primaquine"
    ]


def test_topic_mapping_supersedes_emits_nothing():
    assert topics_for(Predicate.SUPERSEDES, "x", "y") == []


# ---------- regenerator with mocked LLM ----------


@pytest.fixture
def tmp_brain(monkeypatch: pytest.MonkeyPatch) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="medbrain-regen-"))
    monkeypatch.setenv("BRAIN_DIR", str(tmp))
    import importlib

    import medbrain.config as config_mod
    import medbrain.db as db_mod

    importlib.reload(config_mod)
    importlib.reload(db_mod)
    return tmp


def test_regenerate_concept_writes_file(tmp_brain: Path, monkeypatch: pytest.MonkeyPatch):
    """End-to-end: insert a claim, mock LLM, regenerate, assert file exists."""
    from medbrain.db import init_schema, session_scope
    from medbrain.models import Claim, DirtyTracker, Source

    init_schema()

    # Mock the Claude CLI call so we don't spawn a subprocess.
    fake_body = "# Chloroquine\n\n> Mocked concept body.\n\n*Last regenerated: now.*\n"
    monkeypatch.setattr("medbrain.regen.concepts.call", lambda system, user, **kw: fake_body)

    with session_scope() as sess:
        src = Source(source_type=SourceType.PUBMED, external_id="PMID:CQ1")
        sess.add(src)
        sess.flush()
        sess.add(
            Claim(
                subject_text="P. falciparum",
                predicate=Predicate.RESISTS,
                object_text="chloroquine",
                qualifiers={"population": {"region": "sub-Saharan Africa"}},
                certainty=Certainty.HIGH,
                source_id=src.source_id,
                evidence_grade=EvidenceGrade.META_ANALYSIS,
                status=ClaimStatus.AUTO_PROMOTED,
            )
        )
        sess.add(DirtyTracker(kind="entity", name="chloroquine"))
        sess.add(DirtyTracker(kind="topic", name="resistance/chloroquine"))

    # Mock the topic regenerator's LLM too.
    monkeypatch.setattr(
        "medbrain.regen.notes.call", lambda system, user, **kw: "# Resistance: chloroquine\n\n> mock\n"
    )

    from medbrain.regen.coordinator import regenerate_dirty

    res = regenerate_dirty()
    assert res.entities_processed == 1
    assert res.topics_processed == 1
    assert res.entities_failed == 0
    assert res.topics_failed == 0

    from medbrain.config import CONCEPTS_DIR, NOTES_DIR

    concept_file = CONCEPTS_DIR / "chloroquine.md"
    topic_file = NOTES_DIR / "resistance" / "chloroquine.md"
    assert concept_file.exists()
    assert topic_file.exists()
    assert "Mocked concept body" in concept_file.read_text()
    assert "Resistance: chloroquine" in topic_file.read_text()


def test_dirty_tracker_marked_processed(tmp_brain: Path, monkeypatch: pytest.MonkeyPatch):
    from medbrain.db import init_schema, session_scope
    from medbrain.models import Claim, DirtyTracker, Source

    init_schema()
    monkeypatch.setattr("medbrain.regen.concepts.call", lambda *a, **k: "# Mock\n")
    monkeypatch.setattr("medbrain.regen.notes.call", lambda *a, **k: "# Mock\n")

    with session_scope() as sess:
        src = Source(source_type=SourceType.PUBMED, external_id="PMID:DT1")
        sess.add(src)
        sess.flush()
        sess.add(
            Claim(
                subject_text="metformin",
                predicate=Predicate.TREATS,
                object_text="diabetes",
                qualifiers={},
                source_id=src.source_id,
                evidence_grade=EvidenceGrade.RCT,
                status=ClaimStatus.AUTO_PROMOTED,
            )
        )
        sess.add(DirtyTracker(kind="entity", name="metformin"))

    from medbrain.regen.coordinator import regenerate_dirty
    from sqlalchemy import select as _select

    regenerate_dirty()

    with session_scope() as sess:
        rows = (
            sess.execute(
                _select(DirtyTracker).where(DirtyTracker.processed_at.is_(None))
            )
            .scalars()
            .all()
        )
        assert rows == [], f"unprocessed dirty rows remain: {[r.name for r in rows]}"


def test_regenerate_skips_entity_with_no_claims(tmp_brain: Path):
    from medbrain.db import init_schema
    from medbrain.regen.coordinator import regenerate_for_session

    init_schema()
    res = regenerate_for_session(entities=["nonexistent_entity"], topics=[])
    assert res.entities_processed == 0
    assert res.entities_failed == 0
