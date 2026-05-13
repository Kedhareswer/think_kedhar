"""Tests for human-authored question protection + regen-failure auto-emit."""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from medbrain.agents.questions_io import Question, QuestionsFile, load


def _q(qid: str, **kw) -> Question:
    defaults: dict = dict(
        priority=2,
        status="open",
        created=datetime(2026, 5, 13, tzinfo=UTC),
        topic="test",
        body="test body",
    )
    defaults.update(kw)
    return Question(qid=qid, **defaults)


def test_source_field_roundtrip():
    """Question.source survives serialize → parse."""
    q = _q("Q-2026-05-13-001", source="human", body="My human question")
    qf = QuestionsFile(questions=[q])
    serialized = qf.serialize()
    assert "- source: human" in serialized
    parsed = QuestionsFile.parse(serialized)
    assert len(parsed.questions) == 1
    assert parsed.questions[0].source == "human"


def test_source_field_optional():
    """Question without source serializes without the field line."""
    q = _q("Q-2026-05-13-001", body="orphan")
    qf = QuestionsFile(questions=[q])
    serialized = qf.serialize()
    assert "- source:" not in serialized
    parsed = QuestionsFile.parse(serialized)
    assert parsed.questions[0].source is None


def test_merge_protects_human_resolved():
    """Non-human update cannot mark a human Q as resolved."""
    human_q = _q("Q-2026-05-13-001", source="human", priority=1, status="open")
    qf = QuestionsFile(questions=[human_q])

    # Brain tries to mark it resolved.
    update = _q("Q-2026-05-13-001", source="brain", priority=2, status="resolved")
    qf.merge([update])

    final = qf.by_id()["Q-2026-05-13-001"]
    assert final.status == "open"          # not resolved
    assert final.priority == 1             # not demoted
    assert final.source == "human"          # source preserved


def test_merge_allows_human_to_self_modify():
    """Human can resolve their own question (source=human on update)."""
    human_q = _q("Q-2026-05-13-001", source="human", priority=1, status="open")
    qf = QuestionsFile(questions=[human_q])

    update = _q("Q-2026-05-13-001", source="human", priority=1, status="resolved")
    qf.merge([update])

    assert qf.by_id()["Q-2026-05-13-001"].status == "resolved"


def test_merge_allows_brain_to_keep_inprogress():
    """Brain may move human Q to in_progress (working on it) — that's expected."""
    human_q = _q("Q-2026-05-13-001", source="human", priority=1, status="open")
    qf = QuestionsFile(questions=[human_q])

    update = _q("Q-2026-05-13-001", source="brain", priority=1, status="in_progress")
    qf.merge([update])

    final = qf.by_id()["Q-2026-05-13-001"]
    assert final.status == "in_progress"
    assert final.source == "human"


def test_brain_merge_protects_human_against_llm_drift(monkeypatch: pytest.MonkeyPatch):
    """Even if Brain LLM emits a human Q with source=brain + status=resolved,
    the QuestionsFile.merge layer must restore source=human + the original status."""
    tmp = Path(tempfile.mkdtemp(prefix="medbrain-brainmerge-"))
    from tests.conftest import setup_tmp_root
    setup_tmp_root(monkeypatch, tmp)

    from medbrain import config

    # Seed an existing human question on disk.
    config.BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    seed = QuestionsFile(questions=[
        _q("Q-2026-05-10-001", source="human", priority=1, status="open",
           body="What is the pediatric IV artesunate dose for <20kg?"),
    ])
    config.QUESTIONS_FILE.write_text(seed.serialize(), encoding="utf-8")

    # Simulate Brain LLM emitting the same qid but trying to resolve + demote.
    llm_output = QuestionsFile(questions=[
        _q("Q-2026-05-10-001", source="brain", priority=3, status="resolved",
           body="What is the pediatric IV artesunate dose for <20kg?"),
        _q("Q-2026-05-13-001", source="brain", priority=2, status="open",
           body="New gap from Brain?"),
    ])

    # Merge LLM output into disk file (mirrors brain.py logic).
    from medbrain.agents.questions_io import load as load_questions
    disk = load_questions(config.QUESTIONS_FILE)
    disk.merge(llm_output.questions)

    # Human Q protected; new brain Q appended.
    final = disk.by_id()
    assert final["Q-2026-05-10-001"].source == "human"
    assert final["Q-2026-05-10-001"].status == "open"  # not resolved
    assert final["Q-2026-05-10-001"].priority == 1     # not demoted to 3
    assert final["Q-2026-05-13-001"].source == "brain"
    assert final["Q-2026-05-13-001"].status == "open"


def test_emit_regen_failure_question(monkeypatch: pytest.MonkeyPatch):
    """Failure emit writes a Q to brain/questions.md, dedups on retry."""
    tmp = Path(tempfile.mkdtemp(prefix="medbrain-failq-"))
    from tests.conftest import setup_tmp_root
    setup_tmp_root(monkeypatch, tmp)

    from medbrain import config
    from medbrain.regen.citation_gate import GateResult
    from medbrain.regen.failure_log import emit_regen_failure_question

    config.BRAIN_DIR.mkdir(parents=True, exist_ok=True)

    result = GateResult(
        passed=False,
        reason="fabricated citations: ['ffffffff']",
        coverage=0.5,
        cited_count=1,
        input_count=2,
        missing_input_ids=frozenset({"abcdef12"}),
        fabricated_ids=frozenset({"ffffffff"}),
    )

    qid1 = emit_regen_failure_question(target="artemisinin", kind="concept", result=result)
    assert qid1 is not None

    qfile = load(config.QUESTIONS_FILE)
    assert any(q.topic == "[regenfail] artemisinin" for q in qfile.questions)
    failq = next(q for q in qfile.questions if q.topic == "[regenfail] artemisinin")
    assert failq.source == "regen_gate"
    assert failq.status == "open"
    assert failq.priority == 2

    # Second emit with same target → dedup, returns None
    qid2 = emit_regen_failure_question(target="artemisinin", kind="concept", result=result)
    assert qid2 is None

    qfile2 = load(config.QUESTIONS_FILE)
    failqs = [q for q in qfile2.questions if q.topic == "[regenfail] artemisinin"]
    assert len(failqs) == 1
