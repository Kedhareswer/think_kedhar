"""Phase 5 tests: snapshot, compactor, derivative, decay, Dream orchestrator."""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest


# ---------- shared tmp_brain fixture ----------

@pytest.fixture
def tmp_brain(monkeypatch: pytest.MonkeyPatch) -> Path:
    from tests.conftest import setup_tmp_root
    tmp = Path(tempfile.mkdtemp(prefix="medbrain-dream-"))
    return setup_tmp_root(monkeypatch, tmp)


# ---------- compactor citation gate ----------


def test_extract_citations_finds_all_ids():
    from medbrain.dream.compactor import extract_citations

    text = "First fact [c:abc-1] then [c:def-2] and again [c:abc-1]."
    assert extract_citations(text) == ["abc-1", "def-2", "abc-1"]


def test_citations_match_true_when_multiset_equal():
    from medbrain.dream.compactor import citations_match

    old = "x [c:1] y [c:2] z [c:1]"
    new = "shorter [c:2] [c:1] [c:1]"
    assert citations_match(old, new) is True


def test_citations_match_false_when_id_dropped():
    from medbrain.dream.compactor import citations_match

    old = "[c:1] [c:2]"
    new = "[c:1]"  # dropped c:2
    assert citations_match(old, new) is False


def test_citations_match_false_when_id_added():
    from medbrain.dream.compactor import citations_match

    old = "[c:1]"
    new = "[c:1] [c:invented]"
    assert citations_match(old, new) is False


def test_compact_file_skips_small_files(tmp_brain: Path, monkeypatch: pytest.MonkeyPatch):
    from medbrain.dream.compactor import compact_file

    p = tmp_brain / "small.md"
    p.write_text("tiny [c:1]\n", encoding="utf-8")
    res = compact_file(p, min_size_bytes=1024)
    assert res.skipped_reason and "min" in res.skipped_reason
    assert p.read_text() == "tiny [c:1]\n"


def test_compact_file_rejects_citation_drift(tmp_brain: Path, monkeypatch: pytest.MonkeyPatch):
    from medbrain.dream import compactor

    big = "verbose intro paragraph " * 50 + "[c:keep-1]\nMore prose [c:keep-2]\n"
    p = tmp_brain / "big.md"
    p.write_text(big, encoding="utf-8")
    # LLM "loses" citation keep-2
    monkeypatch.setattr(compactor, "call", lambda system, user, **kw: "compact body [c:keep-1]")

    res = compactor.compact_file(p, min_size_bytes=10)
    assert res.citations_preserved is False
    assert "drift" in (res.skipped_reason or "")
    # Original file untouched
    assert "keep-2" in p.read_text()


def test_compact_file_writes_when_smaller_and_citations_preserved(
    tmp_brain: Path, monkeypatch: pytest.MonkeyPatch
):
    from medbrain.dream import compactor

    big = "long intro " * 40 + "[c:k1] [c:k2]\n"
    p = tmp_brain / "big.md"
    p.write_text(big, encoding="utf-8")
    monkeypatch.setattr(
        compactor, "call",
        lambda system, user, **kw: "compact [c:k1] [c:k2]",
    )

    res = compactor.compact_file(p, min_size_bytes=10)
    assert res.citations_preserved
    assert res.new_size < res.old_size
    assert res.skipped_reason is None
    text = p.read_text()
    assert "[c:k1]" in text and "[c:k2]" in text
    assert "long intro" not in text


def test_compact_file_skips_when_no_citations(tmp_brain: Path):
    from medbrain.dream.compactor import compact_file

    p = tmp_brain / "opaque.md"
    p.write_text("a" * 1000, encoding="utf-8")  # no citations at all
    res = compact_file(p, min_size_bytes=10)
    assert res.skipped_reason and "no [c:" in res.skipped_reason


# ---------- snapshot ----------


def test_snapshot_round_trip(tmp_brain: Path):
    from medbrain.dream import snapshot
    from medbrain import config

    config.ensure_brain_dirs()
    (config.CONCEPTS_DIR / "a.md").write_text("original", encoding="utf-8")
    snap = snapshot.take_snapshot()
    assert snap.exists()
    assert (snap / "concepts" / "a.md").read_text() == "original"

    # Mutate then restore
    (config.CONCEPTS_DIR / "a.md").write_text("mutated", encoding="utf-8")
    (config.CONCEPTS_DIR / "b.md").write_text("new file", encoding="utf-8")
    snapshot.restore(snap)
    assert (config.CONCEPTS_DIR / "a.md").read_text() == "original"
    # b.md was created AFTER snapshot — restore should remove? No, snapshot only
    # captured items that existed; restore overwrites the captured items.
    # Per implementation, concepts/ dir is fully replaced from snapshot, so b.md is gone.
    assert not (config.CONCEPTS_DIR / "b.md").exists()


def test_snapshot_gc_keeps_n_newest(tmp_brain: Path):
    from medbrain.dream import snapshot
    from medbrain import config

    config.ensure_brain_dirs()
    paths = []
    for i in range(5):
        (config.CONCEPTS_DIR / f"f{i}.md").write_text(str(i), encoding="utf-8")
        paths.append(snapshot.take_snapshot())

    deleted = snapshot.gc_old(keep=2)
    assert len(deleted) == 3
    remaining = snapshot.list_snapshots()
    assert len(remaining) == 2
    # Newest two retained
    assert remaining[0] == paths[-1]


# ---------- decay ----------


def test_decay_ensure_rows_creates_one_per_entity(tmp_brain: Path):
    from medbrain.db import init_schema, session_scope
    from medbrain.dream.decay import ensure_salience_rows
    from medbrain.enums import (
        Certainty, ClaimStatus, EvidenceGrade, Predicate, SourceType,
    )
    from medbrain.models import Claim, Salience, Source
    from sqlalchemy import select

    init_schema()
    with session_scope() as sess:
        src = Source(source_type=SourceType.PUBMED, external_id="PMID:D1")
        sess.add(src)
        sess.flush()
        sess.add(Claim(
            subject_text="Metformin", predicate=Predicate.TREATS,
            object_text="Diabetes", qualifiers={}, certainty=Certainty.HIGH,
            source_id=src.source_id, evidence_grade=EvidenceGrade.RCT,
            status=ClaimStatus.AUTO_PROMOTED,
        ))
    n = ensure_salience_rows()
    assert n == 2  # "metformin" + "diabetes"
    with session_scope() as sess:
        keys = set(sess.execute(select(Salience.entity)).scalars().all())
        assert keys == {"metformin", "diabetes"}


def test_decay_archives_low_score_entities(tmp_brain: Path):
    from medbrain.db import init_schema, session_scope
    from medbrain.dream.decay import run_decay
    from medbrain.enums import (
        Certainty, ClaimStatus, EvidenceGrade, Predicate, SourceType,
    )
    from medbrain.models import Claim, Salience, Source
    from sqlalchemy import select

    init_schema()
    long_ago = datetime.now(UTC) - timedelta(days=400)
    with session_scope() as sess:
        src = Source(source_type=SourceType.PUBMED, external_id="PMID:D2")
        sess.add(src)
        sess.flush()
        sess.add(Claim(
            subject_text="OldDrug", predicate=Predicate.TREATS,
            object_text="OldCondition", qualifiers={}, certainty=Certainty.LOW,
            source_id=src.source_id, evidence_grade=EvidenceGrade.CASE_REPORT,
            status=ClaimStatus.AUTO_PROMOTED,
        ))
        # Pre-existing salience rows already at the floor
        sess.add(Salience(
            entity="olddrug", query_count=0, citation_count=0,
            last_accessed=long_ago, created_at=long_ago, grace_score=0.2,
        ))
        sess.add(Salience(
            entity="oldcondition", query_count=0, citation_count=0,
            last_accessed=long_ago, created_at=long_ago, grace_score=0.2,
        ))

    res = run_decay()
    assert res.entities_archived == 2
    assert res.claims_archived == 1
    assert res.archive_path is not None
    archive = Path(res.archive_path)
    assert archive.exists()
    # Round-trip the JSONL
    with archive.open(encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    assert len(rows) == 1
    assert rows[0]["subject_text"] == "OldDrug"

    with session_scope() as sess:
        remaining_claims = sess.execute(select(Claim)).scalars().all()
        assert remaining_claims == []
        remaining_sal = sess.execute(select(Salience)).scalars().all()
        assert remaining_sal == []


def test_decay_step_reduces_grace_for_idle_entities(tmp_brain: Path):
    from medbrain.db import init_schema, session_scope
    from medbrain.dream.decay import run_decay
    from medbrain.enums import (
        Certainty, ClaimStatus, EvidenceGrade, Predicate, SourceType,
    )
    from medbrain.models import Claim, Salience, Source
    from sqlalchemy import select

    init_schema()
    long_ago = datetime.now(UTC) - timedelta(days=400)
    with session_scope() as sess:
        src = Source(source_type=SourceType.PUBMED, external_id="PMID:D3")
        sess.add(src)
        sess.flush()
        sess.add(Claim(
            subject_text="Aspirin", predicate=Predicate.TREATS,
            object_text="HeadacheX", qualifiers={}, certainty=Certainty.HIGH,
            source_id=src.source_id, evidence_grade=EvidenceGrade.RCT,
            status=ClaimStatus.AUTO_PROMOTED,
        ))
        sess.add(Salience(
            entity="aspirin", last_accessed=long_ago, created_at=long_ago,
            grace_score=1.0, query_count=0, citation_count=0,
        ))
        sess.add(Salience(
            entity="headachex", last_accessed=long_ago, created_at=long_ago,
            grace_score=1.0, query_count=0, citation_count=0,
        ))

    res = run_decay()
    assert res.entities_decayed == 2
    assert res.entities_archived == 0  # 1.0 - 0.1 = 0.9 still above floor
    with session_scope() as sess:
        scores = {r.entity: r.grace_score for r in sess.execute(select(Salience)).scalars().all()}
        assert pytest.approx(scores["aspirin"]) == 0.9


def test_touch_creates_or_bumps_salience(tmp_brain: Path):
    from medbrain.db import init_schema, session_scope
    from medbrain.dream.decay import touch
    from medbrain.models import Salience
    from sqlalchemy import select

    init_schema()
    touch("Quinine")
    with session_scope() as sess:
        row = sess.execute(select(Salience).where(Salience.entity == "quinine")).scalar_one()
        assert row.query_count == 1
    touch("quinine")
    with session_scope() as sess:
        row = sess.execute(select(Salience).where(Salience.entity == "quinine")).scalar_one()
        assert row.query_count == 2


# ---------- Dream orchestrator ----------


def test_is_due_when_no_runs(tmp_brain: Path):
    from medbrain.agents.dream import is_due
    from medbrain.db import init_schema

    init_schema()
    due, reason = is_due(cadence_days=7)
    assert due is True
    assert "no successful" in reason.lower()


def test_is_due_false_when_recent_run(tmp_brain: Path):
    from medbrain.agents.dream import is_due
    from medbrain.db import init_schema, session_scope
    from medbrain.models import DreamRun

    init_schema()
    now = datetime.now(UTC)
    with session_scope() as sess:
        sess.add(DreamRun(
            started_at=now - timedelta(minutes=5),
            completed_at=now - timedelta(minutes=1),
            restored=0,
        ))

    due, reason = is_due(cadence_days=7)
    assert due is False
    assert "next due" in reason.lower()


def test_dream_dry_run_is_no_op(tmp_brain: Path):
    from medbrain.agents.dream import run_dream
    from medbrain.db import init_schema, session_scope
    from medbrain.models import DreamRun
    from sqlalchemy import select

    init_schema()
    res = run_dream(dry_run=True)
    assert "dry-run" in (res.errors[0] if res.errors else "")
    with session_scope() as sess:
        rows = sess.execute(select(DreamRun)).scalars().all()
    assert rows == []  # dry-run never persists a DreamRun row


def test_dream_skip_all_stages_records_run(tmp_brain: Path):
    from medbrain.agents.dream import run_dream
    from medbrain.db import init_schema, session_scope
    from medbrain.models import DreamRun
    from sqlalchemy import select

    init_schema()
    res = run_dream(skip=("compact", "derivative", "decay"))
    assert sorted(res.skipped_stages) == ["compact", "decay", "derivative"]
    assert res.snapshot_path is not None
    assert res.completed_at is not None
    with session_scope() as sess:
        rows = sess.execute(select(DreamRun)).scalars().all()
    assert len(rows) == 1
    assert rows[0].restored == 0
