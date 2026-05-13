"""Topic-note regeneration: claims under a topic -> notes/<topic>.md."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from medbrain import config
from medbrain.enums import ClaimStatus, Predicate
from medbrain.llm import call
from medbrain.models import Claim, Source
from medbrain.regen.atomic import atomic_write_text
from medbrain.regen.citation_gate import check as citation_gate_check
from medbrain.regen.concepts import _claim_payload
from medbrain.regen.failure_log import emit_regen_failure_question
from medbrain.regen.topics import topics_for

PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "topic_note.md"


def _load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _fetch_topic_claims(
    sess: Session, topic: str
) -> list[tuple[Claim, Source | None]]:
    """Topic = '<bucket>/<slug>'. We re-derive topics from each claim and filter."""
    rows = sess.execute(
        select(Claim, Source)
        .join(Source, Claim.source_id == Source.source_id, isouter=True)
        .where(Claim.status != ClaimStatus.REJECTED)
        .order_by(Claim.ingested_at.desc())
    ).all()

    out: list[tuple[Claim, Source | None]] = []
    for claim, src in rows:
        if topic in topics_for(claim.predicate, claim.subject_text, claim.object_text):
            out.append((claim, src))
    return out


def regenerate_topic(sess: Session, topic: str) -> Path | None:
    """Regenerate notes/<topic>.md for one topic. Returns path or None if no claims."""
    pairs = _fetch_topic_claims(sess, topic)
    if not pairs:
        return None

    payload = [_claim_payload(c, s) for c, s in pairs]
    system = _load_prompt()
    user = (
        f"# Topic\n{topic}\n\n"
        f"# Claims (count={len(payload)})\n"
        f"```json\n{json.dumps(payload, indent=2, default=str)}\n```\n\n"
        f"# Now\n{datetime.now(UTC).isoformat()}\n"
    )
    body = call(system, user, timeout=180.0)

    target = config.NOTES_DIR / f"{topic}.md"
    gate = citation_gate_check(
        body=body,
        input_claim_ids=[c.claim_id for c, _ in pairs],
    )
    if not gate.passed:
        print(
            f"[citation_gate] REJECT topic '{topic}' "
            f"(coverage {gate.coverage:.0%}, cited {gate.cited_count}/{gate.input_count}): {gate.reason}"
        )
        try:
            emit_regen_failure_question(target=topic, kind="topic", result=gate)
        except Exception as exc:
            print(f"[citation_gate] failure_log emit failed: {exc}")
        return None
    atomic_write_text(target, body.strip() + "\n")
    return target
