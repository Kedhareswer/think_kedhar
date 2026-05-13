"""End-to-end orchestrator: plan → execute → store → reflect → update → loop.

One CLI command takes a free-text topic (e.g. "malaria") and drives every
agent in the system until the question backlog converges or a budget cap
is hit. The loop is self-extending: each pass discovers new gaps via
Brain, the active learner picks them up, regen failures auto-emit retry
questions, Dream compacts on cadence, and the Obsidian vault stays in
sync after every iteration.

Phases per iteration:
  1. EXECUTE  — Researcher.ingest_topic (initial seed) OR
                active_learner.run_once (subsequent iterations).
  2. STORE    — handled inside ingest_topic (DB writes + regen with citation gate).
  3. REFLECT  — run_brain() synthesizes brain/memory.md and emits/refreshes
                qid blocks in brain/questions.md.
  4. UPDATE   — publish_to_vault() mirrors brain/dream artifacts into the
                student/ Obsidian vault so the human sees the new state.
  5. DREAM    — only if cadence-due (default 7d): compact, derivative, decay.

Stop conditions (whichever fires first):
  - max_iterations reached
  - no open or in_progress questions remain in questions.md
  - cumulative_papers >= max_papers_total
  - wall-clock exceeded max_minutes
  - errors_in_a_row >= 3 (research+regen+brain all failing — safer to halt)

The seed iteration uses the user-supplied topic; subsequent iterations
use whatever the active learner picks from the qid backlog.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from medbrain import config
from medbrain.agents.active_learner import ActiveLearnerResult, run_once as active_run_once
from medbrain.agents.brain import BrainResult, run_brain
from medbrain.agents.dream import DreamResult, is_due as dream_is_due, run_dream
from medbrain.agents.questions_io import Question, QuestionsFile, load as load_questions, next_qid
from medbrain.agents.researcher import ResearchResult, ingest_topic
from medbrain.exporters.obsidian_vault import (
    VaultExportResult,
    publish_to_vault,
    write_vault_index,
)
from medbrain.regen.atomic import atomic_write_text


@dataclass
class IterationResult:
    iteration: int
    started_at: datetime
    completed_at: datetime | None = None
    kind: str = ""  # "seed" | "active_learner"
    research: ResearchResult | None = None
    active: ActiveLearnerResult | None = None
    brain: BrainResult | None = None
    vault: VaultExportResult | None = None
    dream: DreamResult | None = None
    errors: list[str] = field(default_factory=list)


@dataclass
class OrchestratorResult:
    topic: str
    started_at: datetime
    completed_at: datetime | None = None
    iterations: list[IterationResult] = field(default_factory=list)
    total_papers_ingested: int = 0
    total_claims_inserted: int = 0
    stop_reason: str = ""

    @property
    def successful_iterations(self) -> int:
        return sum(1 for it in self.iterations if not it.errors)


def _seed_human_question(topic: str) -> str:
    """Plant the user's topic as a priority-1 human-source question so the
    backlog has at least one open Q after the seed iteration, even if the
    Researcher's planner is the one doing the real work for iteration 1.
    """
    qpath = config.QUESTIONS_FILE
    qfile = load_questions(qpath)

    # Dedup: if a human Q with the same body already exists, reuse it.
    for q in qfile.questions:
        if q.source == "human" and q.body.strip() == topic.strip():
            return q.qid

    qid = next_qid(qfile.questions)
    new_q = Question(
        qid=qid,
        priority=1,
        status="in_progress",  # seed iteration will research it now
        created=datetime.now(UTC),
        topic=topic[:80],
        body=topic,
        source="human",
    )
    qfile.merge([new_q])
    qpath.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(qpath, qfile.serialize())
    return qid


def _open_question_count() -> int:
    qfile = load_questions(config.QUESTIONS_FILE)
    return sum(1 for q in qfile.questions if q.status in ("open", "in_progress"))


def run_loop(
    topic: str,
    *,
    max_iterations: int = 5,
    max_papers_total: int = 300,
    max_minutes: float = 360.0,
    dream_cadence_days: int = 7,
    publish_vault: bool = True,
    write_index: bool = True,
) -> OrchestratorResult:
    """Drive the full agentic loop on a topic.

    Args:
        topic: free-text research topic ("malaria", "what is malaria",
            "dengue diagnostics in Southeast Asia", etc.).
        max_iterations: hard cap on the number of passes.
        max_papers_total: cumulative ingest budget across all passes.
        max_minutes: wall-clock budget; checked between iterations.
        dream_cadence_days: only run Dream if last successful run is older
            than this many days.
        publish_vault: mirror brain + dream artifacts into student/ after
            each iteration so Obsidian stays current.
        write_index: write student/_index.md on the first publish.

    Returns:
        OrchestratorResult with per-iteration breakdown and stop reason.
    """
    config.ensure_brain_dirs()
    deadline = datetime.now(UTC) + timedelta(minutes=max_minutes)
    result = OrchestratorResult(topic=topic, started_at=datetime.now(UTC))

    # Seed the user's topic into the backlog as a human-source Q in
    # in_progress state so the brain layer respects it and the loop has a
    # backlog entry to converge against.
    seed_qid = _seed_human_question(topic)
    print(f"[orchestrator] seeded human question {seed_qid}: {topic}")

    errors_in_a_row = 0
    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        it = IterationResult(
            iteration=iteration,
            started_at=datetime.now(UTC),
            kind="seed" if iteration == 1 else "active_learner",
        )
        print(f"\n=== Iteration {iteration}/{max_iterations} ({it.kind}) ===")

        # 1. EXECUTE
        try:
            if iteration == 1:
                it.research = ingest_topic(topic, regen=True)
                result.total_papers_ingested += it.research.total_papers_ingested
                result.total_claims_inserted += it.research.total_claims_inserted
            else:
                it.active = active_run_once(regen=True)
                if it.active.no_open_questions:
                    result.stop_reason = "no open questions"
                    it.completed_at = datetime.now(UTC)
                    result.iterations.append(it)
                    break
                if it.active.research is not None:
                    result.total_papers_ingested += it.active.research.total_papers_ingested
                    result.total_claims_inserted += it.active.research.total_claims_inserted
                if it.active.errors:
                    it.errors.extend(it.active.errors)
        except Exception as exc:
            it.errors.append(f"execute: {exc}")

        # 2. STORE — DB writes + regen with citation gate are inside
        # ingest_topic (called above). Regen failures emit qid Qs into
        # the backlog automatically via failure_log.emit_regen_failure_question.

        # 3. REFLECT — Brain synthesizes memory + refreshes qid backlog.
        try:
            it.brain = run_brain(force_full=(iteration == 1))
            if it.brain.errors:
                it.errors.extend(f"brain: {e}" for e in it.brain.errors)
        except Exception as exc:
            it.errors.append(f"brain: {exc}")

        # 4. UPDATE — publish to Obsidian vault.
        if publish_vault:
            try:
                it.vault = publish_to_vault()
                if iteration == 1 and write_index:
                    write_vault_index()
                if it.vault.errors:
                    it.errors.extend(f"vault: {e}" for e in it.vault.errors)
            except Exception as exc:
                it.errors.append(f"vault: {exc}")

        # 5. DREAM — cadence-gated. Skip silently when not due.
        try:
            due, _reason = dream_is_due(cadence_days=dream_cadence_days)
            if due:
                print("[orchestrator] Dream cadence due — running.")
                it.dream = run_dream()
                if it.dream.errors:
                    it.errors.extend(f"dream: {e}" for e in it.dream.errors)
        except Exception as exc:
            it.errors.append(f"dream: {exc}")

        it.completed_at = datetime.now(UTC)
        result.iterations.append(it)

        # Stop-condition checks
        if it.errors:
            errors_in_a_row += 1
        else:
            errors_in_a_row = 0
        if errors_in_a_row >= 3:
            result.stop_reason = "3 consecutive iterations with errors"
            break
        if result.total_papers_ingested >= max_papers_total:
            result.stop_reason = f"paper cap reached ({max_papers_total})"
            break
        if datetime.now(UTC) >= deadline:
            result.stop_reason = "wall-clock deadline"
            break
        if _open_question_count() == 0:
            result.stop_reason = "backlog converged (no open/in_progress Qs)"
            break

    if not result.stop_reason:
        result.stop_reason = f"max_iterations ({max_iterations})"

    result.completed_at = datetime.now(UTC)

    # Final vault publish so the last Brain state is visible.
    if publish_vault:
        try:
            final_vault = publish_to_vault()
            if write_index:
                write_vault_index()
            print(
                f"[orchestrator] final vault publish: {len(final_vault.files_written)} files written"
            )
        except Exception as exc:
            print(f"[orchestrator] final vault publish failed: {exc}")

    return result
