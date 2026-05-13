"""Concept-note regeneration: claims about an entity -> concepts/<slug>.md.

A small type classifier picks one of three prompts based on the entity's claim
profile:
  - "condition"   -> prompts/concept_condition.md   (Master-sheet Conditions aligned)
  - "medication"  -> prompts/concept_medication.md  (Master-sheet Medications aligned)
  - "generic"     -> prompts/concept_note.md        (gene / mechanism / pattern)

Classification is best-effort and conservative: if signals are mixed or thin,
fall back to the generic prompt. The classifier never invents claims — it
only looks at predicate positions and qualifier shapes that already exist.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from medbrain import config
from medbrain.enums import ClaimStatus, Predicate
from medbrain.llm import call
from medbrain.models import Claim, Source
from medbrain.regen.atomic import atomic_write_text
from medbrain.regen.citation_gate import check as citation_gate_check
from medbrain.regen.failure_log import emit_regen_failure_question
from medbrain.regen.slug import slugify

_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"

PROMPT_PATH = _PROMPTS_DIR / "concept_note.md"                # generic (back-compat)
PROMPT_CONDITION = _PROMPTS_DIR / "concept_condition.md"
PROMPT_MEDICATION = _PROMPTS_DIR / "concept_medication.md"


def _load_prompt(prompt_type: str = "generic") -> str:
    """Load the prompt file for ``prompt_type`` ∈ {generic, condition, medication}.

    Unknown types fall back to the generic prompt rather than raising — the
    caller's classifier may evolve faster than the prompt library.
    """
    if prompt_type == "condition" and PROMPT_CONDITION.exists():
        return PROMPT_CONDITION.read_text(encoding="utf-8")
    if prompt_type == "medication" and PROMPT_MEDICATION.exists():
        return PROMPT_MEDICATION.read_text(encoding="utf-8")
    return PROMPT_PATH.read_text(encoding="utf-8")


def classify_entity(entity: str, claims: list[Claim]) -> str:
    """Heuristic entity type. Returns 'condition' | 'medication' | 'generic'.

    Signals:
      - Any claim with a ``dose_regimen`` qualifier strongly implies medication.
      - As SUBJECT of treats/prevents/contraindicates: drug-like.
      - As OBJECT of treats/prevents: condition-like.
      - As OBJECT of causes: condition-like.

    Conservative thresholds so the generic prompt is the default when signals
    are thin or contradictory.
    """
    if not claims:
        return "generic"

    name = entity.strip().lower()
    drug_signal = 0
    condition_signal = 0

    for c in claims:
        quals = c.qualifiers or {}
        if isinstance(quals, dict) and quals.get("dose_regimen"):
            drug_signal += 3  # strong

        subj_match = name in (c.subject_text or "").lower()
        obj_match = name in (c.object_text or "").lower()

        if c.predicate in (Predicate.TREATS, Predicate.PREVENTS, Predicate.CONTRAINDICATES):
            if subj_match:
                drug_signal += 1
            if obj_match:
                condition_signal += 1
        elif c.predicate == Predicate.CAUSES:
            if obj_match:
                condition_signal += 1
            if subj_match:
                # X causes Y; entity X is more often an agent (drug/pathogen) than a condition
                drug_signal += 0  # noisy, ignore
        elif c.predicate == Predicate.RESISTS:
            # "X resists Y" — X is usually a pathogen/condition, Y a drug
            if obj_match:
                drug_signal += 1
            # don't bias the subject side; pathogens aren't conditions per Master-sheet schema

    # Require a clear lead AND minimum confidence.
    threshold = 2
    if drug_signal >= threshold and drug_signal >= condition_signal * 2:
        return "medication"
    if condition_signal >= threshold and condition_signal >= drug_signal * 2:
        return "condition"
    return "generic"


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

    claims = [c for c, _ in pairs]
    prompt_type = classify_entity(entity, claims)
    payload = [_claim_payload(c, s) for c, s in pairs]
    system = _load_prompt(prompt_type)
    user = (
        f"# Entity\n{entity}\n\n"
        f"# Entity type (classifier hint)\n{prompt_type}\n\n"
        f"# Claims (count={len(payload)})\n"
        f"```json\n{json.dumps(payload, indent=2, default=str)}\n```\n\n"
        f"# Now\n{datetime.now(UTC).isoformat()}\n"
    )
    body = call(system, user, timeout=180.0)

    slug = slugify(entity)
    target = config.CONCEPTS_DIR / f"{slug}.md"
    gate = citation_gate_check(
        body=body,
        input_claim_ids=[c.claim_id for c in claims],
    )
    if not gate.passed:
        print(
            f"[citation_gate] REJECT concept '{entity}' "
            f"(coverage {gate.coverage:.0%}, cited {gate.cited_count}/{gate.input_count}): {gate.reason}"
        )
        try:
            emit_regen_failure_question(target=slug, kind="concept", result=gate)
        except Exception as exc:
            print(f"[citation_gate] failure_log emit failed: {exc}")
        return None
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

    claims = [c for c, _ in pairs]
    prompt_type = classify_entity(canonical, claims)
    payload = [_claim_payload(c, s) for c, s in pairs]
    system = _load_prompt(prompt_type)
    user = (
        f"# Entity\n{canonical}\n\n"
        f"# Surface variants\n{', '.join(sorted(set(variants)))}\n\n"
        f"# Entity type (classifier hint)\n{prompt_type}\n\n"
        f"# Claims (count={len(payload)})\n"
        f"```json\n{json.dumps(payload, indent=2, default=str)}\n```\n\n"
        f"# Now\n{datetime.now(UTC).isoformat()}\n"
    )
    body = call(system, user, timeout=180.0)

    slug = slugify(canonical)
    target = config.CONCEPTS_DIR / f"{slug}.md"
    gate = citation_gate_check(
        body=body,
        input_claim_ids=[c.claim_id for c in claims],
    )
    if not gate.passed:
        print(
            f"[citation_gate] REJECT concept '{canonical}' "
            f"(coverage {gate.coverage:.0%}, cited {gate.cited_count}/{gate.input_count}): {gate.reason}"
        )
        try:
            emit_regen_failure_question(target=slug, kind="concept", result=gate)
        except Exception as exc:
            print(f"[citation_gate] failure_log emit failed: {exc}")
        return None
    atomic_write_text(target, body.strip() + "\n")
    return target
