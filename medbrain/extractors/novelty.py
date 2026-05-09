"""Novelty gate: dedup, contradiction check, auto-promote routing.

Spec §5: auto-promote when ALL of:
  - evidence_grade in {meta_analysis, RCT, guideline, cohort}
  - no contradictions detected
  - all entities already known to brain (subject + object both seen before)
  - >= 3 qualifier fields populated
Otherwise -> pending_review.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from medbrain.enums import ClaimStatus, EvidenceGrade, HIGH_GRADES, Predicate
from medbrain.extractors.schema import ExtractedClaim
from medbrain.models import Claim


_OPPOSING: dict[Predicate, set[Predicate]] = {
    Predicate.TREATS: {Predicate.CAUSES},
    Predicate.CAUSES: {Predicate.TREATS, Predicate.PREVENTS},
    Predicate.PREVENTS: {Predicate.CAUSES},
    Predicate.RECOMMENDS: {Predicate.CONTRAINDICATES},
    Predicate.CONTRAINDICATES: {Predicate.RECOMMENDS, Predicate.TREATS},
}


@dataclass(slots=True)
class NoveltyDecision:
    is_duplicate: bool
    duplicate_of_id: str | None
    contradicts: list[str]  # claim_ids that contradict this
    entities_known: bool
    status: ClaimStatus

    @property
    def keep(self) -> bool:
        return not self.is_duplicate


def _dedup_key(c: ExtractedClaim) -> tuple[str, ...]:
    """Identity used to detect duplicates. Subject+predicate+object+population.region+setting."""
    pop = c.qualifiers.population
    setting = c.qualifiers.setting
    return (
        c.subject.strip().lower(),
        c.predicate.value,
        c.object.strip().lower(),
        (pop.region or "").strip().lower(),
        (setting.endemic_status or "").strip().lower(),
        (pop.pregnancy or "").strip().lower(),
    )


def _stored_key(row: Claim) -> tuple[str, ...]:
    pop = (row.qualifiers or {}).get("population", {}) or {}
    setting = (row.qualifiers or {}).get("setting", {}) or {}
    return (
        row.subject_text.strip().lower(),
        row.predicate.value,
        row.object_text.strip().lower(),
        (pop.get("region") or "").strip().lower(),
        (setting.get("endemic_status") or "").strip().lower(),
        (pop.get("pregnancy") or "").strip().lower(),
    )


def _entity_seen(sess: Session, name: str) -> bool:
    name = name.strip().lower()
    if not name:
        return False
    q = select(Claim.claim_id).where(
        (Claim.subject_text.ilike(name)) | (Claim.object_text.ilike(name))
    ).limit(1)
    return sess.scalar(q) is not None


def evaluate(
    sess: Session,
    candidate: ExtractedClaim,
    evidence_grade: EvidenceGrade,
) -> NoveltyDecision:
    """Decide what to do with an extracted claim before insertion."""
    key = _dedup_key(candidate)
    duplicate_of_id: str | None = None
    contradicts: list[str] = []

    same_subject = sess.execute(
        select(Claim).where(
            Claim.subject_text.ilike(candidate.subject),
            Claim.status != ClaimStatus.REJECTED,
        )
    ).scalars().all()

    for row in same_subject:
        if _stored_key(row) == key:
            duplicate_of_id = row.claim_id
            break
        if (
            row.predicate in _OPPOSING.get(candidate.predicate, set())
            and row.object_text.strip().lower() == candidate.object.strip().lower()
        ):
            contradicts.append(row.claim_id)

    entities_known = _entity_seen(sess, candidate.subject) and _entity_seen(
        sess, candidate.object
    )

    if duplicate_of_id is not None:
        return NoveltyDecision(
            is_duplicate=True,
            duplicate_of_id=duplicate_of_id,
            contradicts=contradicts,
            entities_known=entities_known,
            status=ClaimStatus.PENDING_REVIEW,
        )

    auto_ok = (
        evidence_grade in HIGH_GRADES
        and not contradicts
        and entities_known
        and candidate.qualifiers.populated_count() >= 3
    )
    status = ClaimStatus.AUTO_PROMOTED if auto_ok else ClaimStatus.PENDING_REVIEW

    return NoveltyDecision(
        is_duplicate=False,
        duplicate_of_id=None,
        contradicts=contradicts,
        entities_known=entities_known,
        status=status,
    )
