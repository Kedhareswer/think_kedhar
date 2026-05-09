"""Active learning loop.

Per Phase 6 design (locked answers Q1-Q4):

- Pick top open question (priority asc, created asc).
- Mark `open -> in_progress`, atomic-write questions.md.
- Hand `Q.body` to existing Researcher.ingest_topic() — full reuse of planner/
  fetcher/extractor/regen.
- After ingest, the question stays `in_progress`. The next Brain run is responsible
  for flipping `in_progress -> resolved` if its LLM judge decides the new claims
  answered the question.

This module does NOT decide resolution itself. That's an explicit two-step lifecycle:
  active learner = "I tried"
  brain          = "did the try work?"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from medbrain import config
from medbrain.agents.questions_io import (
    Question,
    QuestionsFile,
    load as load_questions,
)
from medbrain.agents.researcher import ResearchResult, ingest_topic
from medbrain.regen.atomic import atomic_write_text


@dataclass
class ActiveLearnerResult:
    started_at: datetime
    completed_at: datetime | None = None
    picked: Question | None = None
    research: ResearchResult | None = None
    questions_file: str | None = None
    no_open_questions: bool = False
    errors: list[str] = field(default_factory=list)


def _open_questions(qfile: QuestionsFile) -> list[Question]:
    return [q for q in qfile.questions if q.status == "open"]


def pick_next(qfile: QuestionsFile) -> Question | None:
    """Return the next question to research, or None if no open questions.

    Order: priority asc, created asc (oldest priority-1 first).
    """
    candidates = _open_questions(qfile)
    if not candidates:
        return None
    return min(candidates, key=lambda q: (q.priority, q.created.timestamp()))


def _mark_in_progress(qfile: QuestionsFile, qid: str) -> None:
    """Mutate qfile in place: set status=in_progress + updated=now for qid."""
    now = datetime.now(UTC)
    by_id = qfile.by_id()
    if qid not in by_id:
        return
    q = by_id[qid]
    q.status = "in_progress"
    q.updated = now


def run_once(*, dry_run: bool = False, regen: bool = True) -> ActiveLearnerResult:
    """One pass: pick top open question, mark in_progress, ingest its body as topic.

    dry_run: pick + report, but neither flip status nor call Researcher.
    """
    started = datetime.now(UTC)
    result = ActiveLearnerResult(started_at=started)

    qpath = config.QUESTIONS_FILE
    qfile = load_questions(qpath)
    pick = pick_next(qfile)

    if pick is None:
        result.no_open_questions = True
        result.completed_at = datetime.now(UTC)
        return result

    result.picked = pick

    if dry_run:
        result.completed_at = datetime.now(UTC)
        return result

    # Flip status before ingesting so concurrent runs see in_progress and skip.
    _mark_in_progress(qfile, pick.qid)
    atomic_write_text(qpath, qfile.serialize())
    result.questions_file = str(qpath)

    try:
        result.research = ingest_topic(pick.body, regen=regen)
    except Exception as e:
        result.errors.append(f"ingest: {e}")

    result.completed_at = datetime.now(UTC)
    return result


def run_batch(*, max_questions: int = 1, regen: bool = True) -> list[ActiveLearnerResult]:
    """Run the loop up to max_questions times, stopping early if none remain."""
    results: list[ActiveLearnerResult] = []
    for _ in range(max(1, max_questions)):
        r = run_once(regen=regen)
        results.append(r)
        if r.no_open_questions or r.errors:
            break
    return results
