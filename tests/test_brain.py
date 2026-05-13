"""Phase 3 tests: questions parser/serializer, Brain agent with mocked LLM."""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from medbrain.agents.questions_io import (
    Question,
    QuestionsFile,
    next_qid,
)


# ---------- questions_io ----------


def test_serialize_empty():
    qf = QuestionsFile()
    out = qf.serialize()
    assert "# Questions" in out


def test_round_trip_single_question():
    q = Question(
        qid="Q-2026-05-01-001",
        priority=1,
        status="open",
        created=datetime(2026, 5, 1, 14, 0, 0, tzinfo=UTC),
        topic="pediatric tafenoquine",
        body="What is the pediatric weight-band dose of tafenoquine for P. vivax radical cure?",
    )
    qf = QuestionsFile(questions=[q])
    text = qf.serialize()
    assert "Q-2026-05-01-001" in text
    assert "priority: 1" in text
    assert "status: open" in text
    assert "pediatric tafenoquine" in text

    parsed = QuestionsFile.parse(text)
    assert len(parsed.questions) == 1
    p = parsed.questions[0]
    assert p.qid == "Q-2026-05-01-001"
    assert p.priority == 1
    assert p.status == "open"
    assert p.topic == "pediatric tafenoquine"
    assert "tafenoquine" in p.body


def test_merge_appends_new_and_replaces_existing():
    base = Question(
        qid="Q-2026-05-01-001",
        priority=2,
        status="open",
        created=datetime(2026, 5, 1, tzinfo=UTC),
        topic="x",
        body="orig body",
    )
    qf = QuestionsFile(questions=[base])

    update_existing = Question(
        qid="Q-2026-05-01-001",
        priority=1,
        status="resolved",
        created=datetime(2026, 5, 1, tzinfo=UTC),
        topic="x",
        body="resolved body",
    )
    new_one = Question(
        qid="Q-2026-05-01-002",
        priority=2,
        status="open",
        created=datetime(2026, 5, 1, tzinfo=UTC),
        topic="y",
        body="new body",
    )
    added, updated_n = qf.merge([update_existing, new_one])
    assert added == 1
    assert updated_n == 1
    by_id = qf.by_id()
    assert by_id["Q-2026-05-01-001"].priority == 1
    assert by_id["Q-2026-05-01-001"].status == "resolved"
    assert by_id["Q-2026-05-01-001"].body == "resolved body"
    assert by_id["Q-2026-05-01-002"].body == "new body"


def test_next_qid_increments_within_day():
    today = datetime(2026, 5, 1, 12, 0, 0, tzinfo=UTC)
    existing = [
        Question(
            qid=f"Q-2026-05-01-{i:03d}",
            priority=1,
            status="open",
            created=today,
            topic="t",
            body="b",
        )
        for i in (1, 3, 5)
    ]
    assert next_qid(existing, today=today) == "Q-2026-05-01-006"
    assert next_qid([], today=today) == "Q-2026-05-01-001"


def test_serialize_sorts_by_priority_then_status():
    qs = [
        Question(qid="Q-2026-05-01-001", priority=3, status="open", created=datetime(2026, 5, 1, tzinfo=UTC), topic="a", body="low"),
        Question(qid="Q-2026-05-01-002", priority=1, status="resolved", created=datetime(2026, 5, 1, tzinfo=UTC), topic="b", body="hi-resolved"),
        Question(qid="Q-2026-05-01-003", priority=1, status="open", created=datetime(2026, 5, 1, tzinfo=UTC), topic="c", body="hi-open"),
    ]
    qf = QuestionsFile(questions=qs)
    text = qf.serialize()
    # priority-1 open should appear before priority-1 resolved should appear before priority-3
    pos_open = text.find("Q-2026-05-01-003")
    pos_resolved = text.find("Q-2026-05-01-002")
    pos_low = text.find("Q-2026-05-01-001")
    assert pos_open < pos_resolved < pos_low


# ---------- Brain agent end-to-end (mocked LLM, mocked filesystem) ----------


@pytest.fixture
def tmp_brain(monkeypatch: pytest.MonkeyPatch) -> Path:
    from tests.conftest import setup_tmp_root
    tmp = Path(tempfile.mkdtemp(prefix="medbrain-brain-"))
    return setup_tmp_root(monkeypatch, tmp)


def _seed_md(root_dir: Path):
    """Seed a minimal corpus. Writes under the new student/ layout so
    Brain's ``_changed_files(CONCEPTS_DIR, ...)`` sees the files."""
    from medbrain import config
    config.CONCEPTS_DIR.mkdir(parents=True, exist_ok=True)
    (config.NOTES_DIR / "treatment").mkdir(parents=True, exist_ok=True)
    (config.CONCEPTS_DIR / "chloroquine.md").write_text(
        "# Chloroquine\n\n> Antimalarial drug.\n", encoding="utf-8"
    )
    (config.NOTES_DIR / "treatment" / "malaria.md").write_text(
        "# Treatment: malaria\n\n> Standard regimens.\n", encoding="utf-8"
    )


def test_run_brain_writes_memory_and_questions(tmp_brain: Path, monkeypatch: pytest.MonkeyPatch):
    from medbrain.db import init_schema
    init_schema()
    _seed_md(tmp_brain)

    # brain.py invokes `call()` twice per run — once for memory synthesis,
    # once for the questions document. The mock decides which by sniffing the
    # user prompt for the questions-task marker.
    def _fake_call(system: str, user: str, **kw):
        if "concept notes" in user and "topic notes" in user and "Topic context" in user:
            return (
                "# Questions\n\n"
                "Research backlog.\n\n"
                "## Q-2026-05-13-001\n"
                "- priority: 1\n"
                "- status: open\n"
                "- created: 2026-05-13T22:00:00+00:00\n"
                "- topic: pediatric chloroquine\n"
                "- source: brain\n\n"
                "What is the pediatric weight-band dose of chloroquine?\n"
            )
        return (
            "# Memory\n\n> Mock synthesis.\n\n"
            "## Active themes\n- malaria treatment [concepts/chloroquine.md]\n"
        )

    monkeypatch.setattr("medbrain.agents.brain.call", _fake_call)

    from medbrain.agents.brain import run_brain
    result = run_brain(force_full=True)

    assert result.concepts_read == 1
    assert result.topics_read == 1
    assert result.errors == []

    from medbrain.config import MEMORY_FILE, QUESTIONS_FILE
    assert MEMORY_FILE.exists()
    assert "Mock synthesis" in MEMORY_FILE.read_text()
    assert QUESTIONS_FILE.exists()
    qtext = QUESTIONS_FILE.read_text()
    assert "pediatric chloroquine" in qtext
    assert "priority: 1" in qtext


def test_run_brain_no_changes_records_empty_run(tmp_brain: Path, monkeypatch: pytest.MonkeyPatch):
    from medbrain.db import init_schema
    init_schema()

    # First run with no .md files: should complete with 0 reads, no LLM call needed.
    called = {"n": 0}
    def _fake_call(*a, **k):
        called["n"] += 1
        return ""
    monkeypatch.setattr("medbrain.agents.brain.call", _fake_call)

    from medbrain.agents.brain import run_brain
    result = run_brain(force_full=True)
    assert result.concepts_read == 0
    assert result.topics_read == 0
    assert called["n"] == 0  # no LLM call when nothing to read
