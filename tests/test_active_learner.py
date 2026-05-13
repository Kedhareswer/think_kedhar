"""Phase 6 tests: active learning loop (pick, status flip, integration)."""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest


@pytest.fixture
def tmp_brain(monkeypatch: pytest.MonkeyPatch) -> Path:
    from tests.conftest import setup_tmp_root
    tmp = Path(tempfile.mkdtemp(prefix="medbrain-active-"))
    return setup_tmp_root(monkeypatch, tmp)


# ---------- pick_next ----------


def _q(qid: str, *, priority: int = 1, status: str = "open", days_old: int = 0,
       topic: str = "t", body: str = "b"):
    from medbrain.agents.questions_io import Question
    return Question(
        qid=qid,
        priority=priority,
        status=status,  # type: ignore[arg-type]
        created=datetime.now(UTC) - timedelta(days=days_old),
        topic=topic,
        body=body,
    )


def test_pick_next_returns_none_when_no_open():
    from medbrain.agents.active_learner import pick_next
    from medbrain.agents.questions_io import QuestionsFile

    qfile = QuestionsFile(questions=[
        _q("Q-2026-05-01-001", status="resolved"),
        _q("Q-2026-05-01-002", status="in_progress"),
    ])
    assert pick_next(qfile) is None


def test_pick_next_picks_highest_priority():
    from medbrain.agents.active_learner import pick_next
    from medbrain.agents.questions_io import QuestionsFile

    qfile = QuestionsFile(questions=[
        _q("Q-2026-05-01-001", priority=3, days_old=10),  # oldest but lowest priority
        _q("Q-2026-05-01-002", priority=1, days_old=1),
        _q("Q-2026-05-01-003", priority=2, days_old=20),
    ])
    pick = pick_next(qfile)
    assert pick is not None
    assert pick.qid == "Q-2026-05-01-002"


def test_pick_next_breaks_priority_tie_by_oldest():
    from medbrain.agents.active_learner import pick_next
    from medbrain.agents.questions_io import QuestionsFile

    qfile = QuestionsFile(questions=[
        _q("Q-A", priority=1, days_old=2),
        _q("Q-B", priority=1, days_old=10),  # older — wins
        _q("Q-C", priority=1, days_old=5),
    ])
    assert pick_next(qfile).qid == "Q-B"


def test_pick_next_skips_in_progress_and_resolved():
    from medbrain.agents.active_learner import pick_next
    from medbrain.agents.questions_io import QuestionsFile

    qfile = QuestionsFile(questions=[
        _q("Q-A", priority=1, status="in_progress"),
        _q("Q-B", priority=1, status="resolved"),
        _q("Q-C", priority=2, status="open"),
    ])
    assert pick_next(qfile).qid == "Q-C"


# ---------- dry_run ----------


def test_run_once_no_open_questions_short_circuits(tmp_brain: Path):
    from medbrain.agents.active_learner import run_once

    res = run_once()
    assert res.no_open_questions is True
    assert res.picked is None
    assert res.research is None


def test_run_once_dry_run_does_not_flip_status(tmp_brain: Path):
    from medbrain import config
    from medbrain.agents.active_learner import run_once
    from medbrain.agents.questions_io import (
        QuestionsFile,
        load as load_questions,
    )
    from medbrain.regen.atomic import atomic_write_text

    qfile = QuestionsFile(questions=[
        _q("Q-2026-05-04-001", priority=1, topic="x", body="What is X?"),
    ])
    atomic_write_text(config.QUESTIONS_FILE, qfile.serialize())

    res = run_once(dry_run=True)
    assert res.picked is not None
    assert res.picked.qid == "Q-2026-05-04-001"
    assert res.research is None  # no ingest in dry-run

    # File on disk unchanged: status still open
    reloaded = load_questions(config.QUESTIONS_FILE)
    assert reloaded.questions[0].status == "open"


# ---------- real run with mocked Researcher ----------


def test_run_once_flips_to_in_progress_and_calls_researcher(
    tmp_brain: Path, monkeypatch: pytest.MonkeyPatch
):
    from medbrain import config
    from medbrain.agents import active_learner
    from medbrain.agents.questions_io import (
        QuestionsFile,
        load as load_questions,
    )
    from medbrain.extractors.plan import ResearchPlan, StopCriteria
    from medbrain.agents.researcher import ResearchResult
    from medbrain.regen.atomic import atomic_write_text

    qfile = QuestionsFile(questions=[
        _q("Q-2026-05-04-001", priority=1, topic="pediatric tafenoquine",
           body="What is the pediatric weight-band dose of tafenoquine?"),
    ])
    atomic_write_text(config.QUESTIONS_FILE, qfile.serialize())

    captured: dict = {}

    def fake_ingest(topic: str, *, regen: bool = True) -> ResearchResult:
        captured["topic"] = topic
        captured["regen"] = regen
        plan = ResearchPlan(
            topic=topic,
            scope="focused",
            decomposition=[],
            queries=[],
            stop_criteria=StopCriteria(
                saturation_window=3,
                duplicate_ratio_threshold=0.8,
                max_total_papers=10,
            ),
        )
        return ResearchResult(
            topic=topic,
            plan=plan,
            total_papers_ingested=2,
            total_claims_extracted=5,
            total_claims_inserted=4,
            total_duplicates=1,
        )

    monkeypatch.setattr(active_learner, "ingest_topic", fake_ingest)

    res = active_learner.run_once()
    assert res.picked is not None
    assert res.picked.qid == "Q-2026-05-04-001"
    assert res.research is not None
    assert res.research.total_claims_inserted == 4
    assert captured["topic"] == "What is the pediatric weight-band dose of tafenoquine?"
    assert captured["regen"] is True

    # File on disk: status flipped to in_progress
    reloaded = load_questions(config.QUESTIONS_FILE)
    assert reloaded.questions[0].status == "in_progress"
    assert reloaded.questions[0].updated is not None


def test_run_once_records_researcher_exception_in_errors(
    tmp_brain: Path, monkeypatch: pytest.MonkeyPatch
):
    from medbrain import config
    from medbrain.agents import active_learner
    from medbrain.agents.questions_io import (
        QuestionsFile,
        load as load_questions,
    )
    from medbrain.regen.atomic import atomic_write_text

    qfile = QuestionsFile(questions=[
        _q("Q-2026-05-04-002", priority=1, topic="t", body="failing question"),
    ])
    atomic_write_text(config.QUESTIONS_FILE, qfile.serialize())

    def boom(topic: str, *, regen: bool = True):
        raise RuntimeError("simulated PubMed outage")

    monkeypatch.setattr(active_learner, "ingest_topic", boom)

    res = active_learner.run_once()
    assert res.errors and "simulated PubMed outage" in res.errors[0]
    # Status still flipped despite ingest failure — caller can re-attempt by
    # editing questions.md back to open.
    reloaded = load_questions(config.QUESTIONS_FILE)
    assert reloaded.questions[0].status == "in_progress"


def test_run_batch_stops_when_no_more_open(
    tmp_brain: Path, monkeypatch: pytest.MonkeyPatch
):
    from medbrain import config
    from medbrain.agents import active_learner
    from medbrain.agents.questions_io import QuestionsFile
    from medbrain.extractors.plan import ResearchPlan, StopCriteria
    from medbrain.agents.researcher import ResearchResult
    from medbrain.regen.atomic import atomic_write_text

    qfile = QuestionsFile(questions=[
        _q("Q-2026-05-04-001", priority=1, body="QA?"),
        _q("Q-2026-05-04-002", priority=2, body="QB?"),
    ])
    atomic_write_text(config.QUESTIONS_FILE, qfile.serialize())

    def fake_ingest(topic: str, *, regen: bool = True):
        plan = ResearchPlan(
            topic=topic, scope="focused", decomposition=[], queries=[],
            stop_criteria=StopCriteria(
                saturation_window=3, duplicate_ratio_threshold=0.8, max_total_papers=10,
            ),
        )
        return ResearchResult(topic=topic, plan=plan)

    monkeypatch.setattr(active_learner, "ingest_topic", fake_ingest)

    results = active_learner.run_batch(max_questions=5)
    # Picks priority-1 first, then priority-2, then no more open → stops.
    assert len(results) == 3
    assert results[0].picked.qid == "Q-2026-05-04-001"
    assert results[1].picked.qid == "Q-2026-05-04-002"
    assert results[2].no_open_questions is True
