"""Tests for medbrain.agents.orchestrator.

Mocks every LLM call + network. Verifies the loop wires plan → execute →
store → reflect → update correctly, respects stop conditions, and
preserves the user's topic as a human-source Q.
"""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest


def _setup(monkeypatch: pytest.MonkeyPatch) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="medbrain-orch-"))
    from tests.conftest import setup_tmp_root
    return setup_tmp_root(monkeypatch, tmp)


def _mock_research_result():
    from medbrain.agents.researcher import ResearchResult
    from medbrain.extractors.plan import ResearchPlan
    return ResearchResult(
        topic="malaria",
        plan=ResearchPlan(topic="malaria", scope="broad", decomposition=[], queries=[], stop_criteria={"max_total_papers": 1, "saturation_window": 3, "duplicate_ratio_threshold": 0.7}),
        query_runs=[],
        total_papers_ingested=2,
        total_claims_extracted=4,
        total_claims_inserted=3,
        total_duplicates=1,
        cap_hit=False,
        regen=None,
    )


def test_orchestrator_seeds_human_question_and_runs_one_iteration(monkeypatch: pytest.MonkeyPatch):
    root = _setup(monkeypatch)
    from medbrain import config
    from medbrain.db import init_schema
    init_schema()

    # Mock the agents the orchestrator wires.
    from medbrain.agents.researcher import ResearchResult
    monkeypatch.setattr(
        "medbrain.agents.orchestrator.ingest_topic",
        lambda topic, regen=True: _mock_research_result(),
    )

    from medbrain.agents.brain import BrainResult
    fake_brain = BrainResult(
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        topic=None,
        concepts_read=2,
        topics_read=1,
    )
    monkeypatch.setattr(
        "medbrain.agents.orchestrator.run_brain",
        lambda force_full=False, **kw: fake_brain,
    )
    # Dream never due in this test.
    monkeypatch.setattr(
        "medbrain.agents.orchestrator.dream_is_due",
        lambda cadence_days=7: (False, "test"),
    )
    monkeypatch.setattr(
        "medbrain.agents.orchestrator.run_dream",
        lambda *a, **k: pytest.fail("Dream should not run when not due"),
    )

    # First iteration is seed. Second iteration would call active_run_once;
    # we mock it to return no_open_questions so the loop stops cleanly.
    from medbrain.agents.active_learner import ActiveLearnerResult
    def _mock_active(regen=True):
        r = ActiveLearnerResult(started_at=datetime.now(UTC))
        r.no_open_questions = True
        r.completed_at = datetime.now(UTC)
        return r
    monkeypatch.setattr("medbrain.agents.orchestrator.active_run_once", _mock_active)

    from medbrain.agents.orchestrator import run_loop
    result = run_loop("malaria", max_iterations=3, max_papers_total=100)

    # Human Q seeded
    from medbrain.agents.questions_io import load as load_questions
    qf = load_questions(config.QUESTIONS_FILE)
    human_qs = [q for q in qf.questions if q.source == "human"]
    assert len(human_qs) == 1
    assert human_qs[0].body == "malaria"
    assert human_qs[0].priority == 1
    assert human_qs[0].status == "open"

    # Iterations executed
    assert len(result.iterations) >= 1
    assert result.iterations[0].kind == "seed"
    assert result.iterations[0].research is not None
    assert result.total_papers_ingested == 2
    assert result.total_claims_inserted == 3

    # Stop reason set
    assert result.stop_reason  # non-empty


def test_orchestrator_dedups_seed_human_question(monkeypatch: pytest.MonkeyPatch):
    """Re-running with the same topic does NOT create a second human Q."""
    root = _setup(monkeypatch)
    from medbrain import config
    from medbrain.db import init_schema
    init_schema()

    # Pre-seed one human Q matching the topic.
    from medbrain.agents.questions_io import Question, QuestionsFile
    qf = QuestionsFile(questions=[
        Question(
            qid="Q-2026-05-13-001",
            priority=1,
            status="open",
            created=datetime.now(UTC),
            topic="malaria",
            body="malaria",
            source="human",
        ),
    ])
    config.QUESTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.QUESTIONS_FILE.write_text(qf.serialize(), encoding="utf-8")

    monkeypatch.setattr(
        "medbrain.agents.orchestrator.ingest_topic",
        lambda topic, regen=True: _mock_research_result(),
    )
    from medbrain.agents.brain import BrainResult
    monkeypatch.setattr(
        "medbrain.agents.orchestrator.run_brain",
        lambda force_full=False, **kw: BrainResult(
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            concepts_read=0,
            topics_read=0,
        ),
    )
    monkeypatch.setattr(
        "medbrain.agents.orchestrator.dream_is_due",
        lambda cadence_days=7: (False, "test"),
    )
    from medbrain.agents.active_learner import ActiveLearnerResult
    def _mock_active(regen=True):
        r = ActiveLearnerResult(started_at=datetime.now(UTC))
        r.no_open_questions = True
        r.completed_at = datetime.now(UTC)
        return r
    monkeypatch.setattr("medbrain.agents.orchestrator.active_run_once", _mock_active)

    from medbrain.agents.orchestrator import run_loop
    run_loop("malaria", max_iterations=1, max_papers_total=10)

    from medbrain.agents.questions_io import load as load_questions
    qf2 = load_questions(config.QUESTIONS_FILE)
    human_qs = [q for q in qf2.questions if q.source == "human"]
    assert len(human_qs) == 1  # still one, not two


def test_orchestrator_respects_paper_cap(monkeypatch: pytest.MonkeyPatch):
    root = _setup(monkeypatch)
    from medbrain.db import init_schema
    init_schema()

    monkeypatch.setattr(
        "medbrain.agents.orchestrator.ingest_topic",
        lambda topic, regen=True: _mock_research_result(),
    )
    from medbrain.agents.brain import BrainResult
    monkeypatch.setattr(
        "medbrain.agents.orchestrator.run_brain",
        lambda force_full=False, **kw: BrainResult(
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            concepts_read=0,
            topics_read=0,
        ),
    )
    monkeypatch.setattr(
        "medbrain.agents.orchestrator.dream_is_due",
        lambda cadence_days=7: (False, "test"),
    )

    from medbrain.agents.orchestrator import run_loop
    # Cap at 1 paper — seed iteration ingests 2 → cap hit immediately after.
    result = run_loop("malaria", max_iterations=10, max_papers_total=1)
    assert "paper cap" in result.stop_reason
