"""Auto-emit a research question when citation_gate rejects a regen.

The regen pipeline is best-effort: when the LLM rewrite drops too much
evidence or fabricates citations, the gate keeps the prior file but the
rejection is silent unless someone watches stdout. This module closes the
loop by writing a question into brain/questions.md that the active learner
will pick up on its next tick — researcher re-ingests the entity with
fresh focused queries, the next regen tick has more evidence to work with,
and the cycle resolves itself.

Dedup: an open Q with the same `topic` (e.g. "[regenfail] artemisinin")
suppresses a duplicate emission. The active learner flips it to
in_progress; if regen succeeds next pass, Brain (the question evaluator)
will move it to resolved on the next eval.
"""

from __future__ import annotations

from datetime import UTC, datetime

from medbrain import config
from medbrain.agents.questions_io import Question, load, next_qid
from medbrain.regen.atomic import atomic_write_text
from medbrain.regen.citation_gate import GateResult


def emit_regen_failure_question(
    *,
    target: str,
    kind: str,
    result: GateResult,
) -> str | None:
    """Append a regen-failure question to brain/questions.md.

    Args:
        target: the entity/topic slug whose regen failed.
        kind: "concept" | "topic" — for the question body.
        result: GateResult from citation_gate.check.

    Returns:
        The qid that was written, or None if a duplicate already exists.
    """
    qpath = config.QUESTIONS_FILE
    qfile = load(qpath)

    topic_tag = f"[regenfail] {target}"
    for existing in qfile.questions:
        if existing.topic == topic_tag and existing.status in ("open", "in_progress"):
            return None  # already tracked

    fabricated = sorted(result.fabricated_ids)[:5]
    missing = sorted(result.missing_input_ids)[:5]
    body_lines = [
        f"Regen of {kind} `{target}` failed the citation gate: {result.reason}.",
        f"Coverage {result.coverage:.0%} ({result.cited_count}/{result.input_count} input claims cited).",
    ]
    if fabricated:
        body_lines.append(f"Fabricated citations in rejected output: {fabricated}.")
    if missing:
        body_lines.append(f"Missing input claim_ids (sample): {missing}.")
    body_lines.append(
        f"Action: re-ingest evidence specifically on `{target}` with focused PubMed queries, "
        f"then the next regen pass should reach gate coverage."
    )
    body = "\n\n".join(body_lines)

    qid = next_qid(qfile.questions)
    new_q = Question(
        qid=qid,
        priority=2,
        status="open",
        created=datetime.now(UTC),
        topic=topic_tag,
        body=body,
        source="regen_gate",
    )
    qfile.merge([new_q])

    qpath.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(qpath, qfile.serialize())
    return qid
