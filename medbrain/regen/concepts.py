"""Concept-note regeneration: claims about an entity -> concepts/<slug>.md."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from medbrain import config
from medbrain.enums import ClaimStatus
from medbrain.llm import call
from medbrain.models import Claim, Source
from medbrain.regen.atomic import atomic_write_text
from medbrain.regen.slug import slugify

PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "concept_note.md"


def _load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _claim_payload(claim: Claim, source: Source | None) -> dict:
    return {
        "claim_id": claim.claim_id,
        "short_id": claim.claim_id[:8],
        "subject": claim.subject_text,
        "predicate": claim.predicate.value,
        "object": claim.object_text,
        "qualifiers": claim.qualifiers or {},
        "certainty": claim.certainty.value,
        "evidence_grade": claim.evidence_grade.value,
        "status": claim.status.value,
        "supersedes_id": claim.supersedes_id,
        "valid_from": claim.valid_from.isoformat() if claim.valid_from else None,
        "valid_until": claim.valid_until.isoformat() if claim.valid_until else None,
        "source": (
            {
                "type": source.source_type.value,
                "external_id": source.external_id,
                "title": source.title,
                "url": source.url,
            }
            if source
            else None
        ),
    }


def _fetch_entity_claims(sess: Session, entity: str) -> list[tuple[Claim, Source | None]]:
    name = entity.strip()
    rows = (
        sess.execute(
            select(Claim, Source)
            .join(Source, Claim.source_id == Source.source_id, isouter=True)
            .where(
                or_(Claim.subject_text.ilike(name), Claim.object_text.ilike(name)),
                Claim.status != ClaimStatus.REJECTED,
            )
            .order_by(Claim.ingested_at.desc())
        )
        .all()
    )
    return [(c, s) for (c, s) in rows]


def regenerate_concept(sess: Session, entity: str) -> Path | None:
    """Regenerate concepts/<slug>.md for one entity. Returns the path or None if no claims."""
    pairs = _fetch_entity_claims(sess, entity)
    if not pairs:
        return None

    payload = [_claim_payload(c, s) for c, s in pairs]
    system = _load_prompt()
    user = (
        f"# Entity\n{entity}\n\n"
        f"# Claims (count={len(payload)})\n"
        f"```json\n{json.dumps(payload, indent=2, default=str)}\n```\n\n"
        f"# Now\n{datetime.now(UTC).isoformat()}\n"
    )
    body = call(system, user, timeout=180.0)

    slug = slugify(entity)
    target = config.CONCEPTS_DIR / f"{slug}.md"
    atomic_write_text(target, body.strip() + "\n")
    return target


def _fetch_entity_claims_by_variants(
    sess: Session, variants: list[str]
) -> list[tuple[Claim, Source | None]]:
    """Fetch claims whose subject_text or object_text matches any variant exactly."""
    rows = (
        sess.execute(
            select(Claim, Source)
            .join(Source, Claim.source_id == Source.source_id, isouter=True)
            .where(
                or_(
                    Claim.subject_text.in_(variants),
                    Claim.object_text.in_(variants),
                ),
                Claim.status != ClaimStatus.REJECTED,
            )
            .order_by(Claim.ingested_at.desc())
        )
        .all()
    )
    return [(c, s) for (c, s) in rows]


def regenerate_concept_canonical(
    sess: Session, canonical: str, variants: list[str]
) -> Path | None:
    """Regenerate one concept page covering all surface-form variants of an entity.

    `canonical` is the slug-friendly canonical name. `variants` are the raw
    surface forms (used for the SQL match against subject_text/object_text).
    """
    pairs = _fetch_entity_claims_by_variants(sess, variants)
    if not pairs:
        return None

    payload = [_claim_payload(c, s) for c, s in pairs]
    system = _load_prompt()
    user = (
        f"# Entity\n{canonical}\n\n"
        f"# Surface variants\n{', '.join(sorted(set(variants)))}\n\n"
        f"# Claims (count={len(payload)})\n"
        f"```json\n{json.dumps(payload, indent=2, default=str)}\n```\n\n"
        f"# Now\n{datetime.now(UTC).isoformat()}\n"
    )
    body = call(system, user, timeout=180.0)

    slug = slugify(canonical)
    target = config.CONCEPTS_DIR / f"{slug}.md"
    atomic_write_text(target, body.strip() + "\n")
    return target
