"""Smoke tests for SQLAlchemy models + db init."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest


@pytest.fixture
def tmp_brain(monkeypatch: pytest.MonkeyPatch) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="medbrain-test-"))
    monkeypatch.setenv("BRAIN_DIR", str(tmp))
    # Reload modules so they pick up new BRAIN_DIR.
    import importlib

    import medbrain.config as config_mod
    import medbrain.db as db_mod

    importlib.reload(config_mod)
    importlib.reload(db_mod)
    return tmp


def test_init_creates_schema_and_dirs(tmp_brain: Path) -> None:
    from medbrain.config import (
        BRAIN_DIR,
        CONCEPTS_DIR,
        DB_PATH,
        DERIVATIVE_DIR,
        GRAPH_DIR,
        NOTES_DIR,
    )
    from medbrain.db import init_schema

    init_schema()

    assert BRAIN_DIR.exists()
    assert CONCEPTS_DIR.exists()
    assert NOTES_DIR.exists()
    assert (NOTES_DIR / "treatment").exists()
    assert (NOTES_DIR / "resistance").exists()
    assert DERIVATIVE_DIR.exists()
    assert (DERIVATIVE_DIR / "flashcards").exists()
    assert GRAPH_DIR.exists()
    assert DB_PATH.exists()


def test_insert_claim_round_trip(tmp_brain: Path) -> None:
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
        src = Source(
            source_type=SourceType.PUBMED,
            external_id="PMID:31234567",
            url="https://pubmed.ncbi.nlm.nih.gov/31234567/",
            title="Greater Mekong artemisinin resistance cohort",
            publication_date=datetime(2019, 6, 1),
            publication_type="Cohort Study",
        )
        sess.add(src)
        sess.flush()
        claim = Claim(
            subject_text="P. falciparum",
            predicate=Predicate.RESISTS,
            object_text="artemisinin",
            qualifiers={
                "population": {"region": "Greater Mekong"},
                "setting": {"care_level": "outpatient", "endemic_status": "endemic"},
                "effect_size": {"metric": "day-3 positivity", "value": 0.18},
            },
            certainty=Certainty.MODERATE,
            source_id=src.source_id,
            evidence_grade=EvidenceGrade.COHORT,
            status=ClaimStatus.AUTO_PROMOTED,
        )
        sess.add(claim)

    with session_scope() as sess:
        rows = sess.query(Claim).all()
        assert len(rows) == 1
        c = rows[0]
        assert c.subject_text == "P. falciparum"
        assert c.predicate == Predicate.RESISTS
        assert c.qualifiers["population"]["region"] == "Greater Mekong"
        assert c.evidence_grade == EvidenceGrade.COHORT
        assert c.status == ClaimStatus.AUTO_PROMOTED


def test_dirty_tracker_round_trip(tmp_brain: Path) -> None:
    from medbrain.db import init_schema, session_scope
    from medbrain.models import DirtyTracker

    init_schema()

    with session_scope() as sess:
        sess.add(DirtyTracker(kind="entity", name="chloroquine"))
        sess.add(DirtyTracker(kind="topic", name="resistance/chloroquine_resistance"))

    with session_scope() as sess:
        unprocessed = sess.query(DirtyTracker).filter(DirtyTracker.processed_at.is_(None)).all()
        assert len(unprocessed) == 2
        assert {r.name for r in unprocessed} == {
            "chloroquine",
            "resistance/chloroquine_resistance",
        }
