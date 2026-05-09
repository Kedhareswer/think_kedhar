"""Salience decay + archive.

Per design Q4-B (adapted to actual `salience` table, which is per-entity not per-claim):

Phase A (ensure rows): every distinct entity in `claims` gets a `salience` row.
  - New rows start with `grace_score=1.0` and `last_accessed=now`.

Phase B (decay): for entities whose `last_accessed` is older than UNREAD_THRESHOLD,
  reduce `grace_score` by DECAY_STEP.

Phase C (archive): entities whose `grace_score <= ARCHIVE_FLOOR`:
  - All claims for that entity (subject OR object match) are dumped to
    brain/archive/claims_<UTC-iso>.jsonl
  - Claims are DELETEd from `claims` (and EvidenceLedger rows for them).
  - Salience row is also removed.

Returns counts. Pure SQL + filesystem; no LLM.

Thresholds expressed as (1.0 = fresh, 0.0 = max-decayed). Default 6 months
unread, decay 0.1 per dream pass, archive at 0.3 = 7 missed passes from fresh.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Iterable

from sqlalchemy import delete, select

from medbrain import config
from medbrain.db import session_scope
from medbrain.models import Claim, EvidenceLedger, Salience

UNREAD_THRESHOLD_DAYS_DEFAULT = 180
DECAY_STEP_DEFAULT = 0.1
ARCHIVE_FLOOR_DEFAULT = 0.3


@dataclass
class DecayResult:
    rows_ensured: int = 0
    entities_decayed: int = 0
    entities_archived: int = 0
    claims_archived: int = 0
    archive_path: str | None = None
    archived_entities: list[str] = field(default_factory=list)


def _all_entity_keys() -> set[str]:
    """Distinct lowercased subject+object strings from claims."""
    with session_scope() as sess:
        subs = sess.execute(select(Claim.subject_text).distinct()).scalars().all()
        objs = sess.execute(select(Claim.object_text).distinct()).scalars().all()
    return {(s or "").strip().lower() for s in subs if s} | {
        (o or "").strip().lower() for o in objs if o
    }


def ensure_salience_rows(*, now: datetime | None = None) -> int:
    """Insert a Salience row for every entity in claims that doesn't have one yet."""
    now = now or datetime.now(UTC)
    keys = _all_entity_keys()
    if not keys:
        return 0
    with session_scope() as sess:
        existing = set(sess.execute(select(Salience.entity)).scalars().all())
        missing = keys - existing
        for key in missing:
            sess.add(
                Salience(
                    entity=key,
                    query_count=0,
                    citation_count=0,
                    last_accessed=now,
                    created_at=now,
                    grace_score=1.0,
                )
            )
    return len(missing)


def _archive_jsonl_path(now: datetime) -> Path:
    ts = now.strftime("%Y%m%dT%H%M%SZ")
    return config.ARCHIVE_DIR / f"claims_{ts}.jsonl"


def _serialize_claim(c: Claim) -> dict:
    return {
        "claim_id": c.claim_id,
        "subject_text": c.subject_text,
        "predicate": c.predicate.value,
        "object_text": c.object_text,
        "qualifiers": c.qualifiers or {},
        "certainty": c.certainty.value,
        "evidence_grade": c.evidence_grade.value,
        "status": c.status.value,
        "valid_from": c.valid_from.isoformat() if c.valid_from else None,
        "valid_until": c.valid_until.isoformat() if c.valid_until else None,
        "supersedes_id": c.supersedes_id,
        "source_id": c.source_id,
        "ingested_at": c.ingested_at.isoformat() if c.ingested_at else None,
    }


def _claims_for_entity_keys(sess, keys: Iterable[str]) -> list[Claim]:
    keys = list(keys)
    if not keys:
        return []
    rows = sess.execute(
        select(Claim).where(
            (Claim.subject_text.in_(keys)) | (Claim.object_text.in_(keys))
        )
    ).scalars().all()
    return list(rows)


def run_decay(
    *,
    now: datetime | None = None,
    unread_threshold_days: int = UNREAD_THRESHOLD_DAYS_DEFAULT,
    decay_step: float = DECAY_STEP_DEFAULT,
    archive_floor: float = ARCHIVE_FLOOR_DEFAULT,
) -> DecayResult:
    """Run the full decay → archive pipeline. Returns counts."""
    now = now or datetime.now(UTC)
    result = DecayResult()
    result.rows_ensured = ensure_salience_rows(now=now)

    cutoff = now - timedelta(days=unread_threshold_days)

    # Decay phase
    with session_scope() as sess:
        idle = sess.execute(
            select(Salience).where(Salience.last_accessed < cutoff)
        ).scalars().all()
        for s in idle:
            s.grace_score = max(0.0, s.grace_score - decay_step)
        result.entities_decayed = len(idle)

    # Archive phase (separate session so the decay commit lands first)
    with session_scope() as sess:
        doomed = sess.execute(
            select(Salience).where(Salience.grace_score <= archive_floor)
        ).scalars().all()
        if not doomed:
            return result

        # Match subject_text/object_text. Actual claim text is original-case in db,
        # but we compare case-insensitively because Salience.entity is lowercased.
        # SQLite default collation is NOCASE-friendly with .ilike-style matches via lower();
        # to keep behaviour portable we do a python-side filter after a broad fetch.
        keys = {s.entity for s in doomed}
        all_claims = sess.execute(select(Claim)).scalars().all()
        targets = [
            c for c in all_claims
            if (c.subject_text or "").strip().lower() in keys
            or (c.object_text or "").strip().lower() in keys
        ]

        if targets:
            archive_path = _archive_jsonl_path(now)
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            with archive_path.open("w", encoding="utf-8") as fh:
                for c in targets:
                    fh.write(json.dumps(_serialize_claim(c)) + "\n")
            result.archive_path = str(archive_path)
            result.claims_archived = len(targets)

            target_ids = [c.claim_id for c in targets]
            sess.execute(
                delete(EvidenceLedger).where(EvidenceLedger.claim_id.in_(target_ids))
            )
            sess.execute(delete(Claim).where(Claim.claim_id.in_(target_ids)))

        # Drop salience rows for archived entities.
        sess.execute(delete(Salience).where(Salience.entity.in_(keys)))
        result.entities_archived = len(keys)
        result.archived_entities = sorted(keys)

    return result


def touch(entity: str, *, now: datetime | None = None) -> None:
    """Bump last_accessed + query_count for an entity. Called by retrieval API."""
    key = (entity or "").strip().lower()
    if not key:
        return
    now = now or datetime.now(UTC)
    with session_scope() as sess:
        row = sess.execute(
            select(Salience).where(Salience.entity == key)
        ).scalar_one_or_none()
        if row is None:
            sess.add(
                Salience(
                    entity=key,
                    query_count=1,
                    citation_count=0,
                    last_accessed=now,
                    created_at=now,
                    grace_score=1.0,
                )
            )
        else:
            row.last_accessed = now
            row.query_count = (row.query_count or 0) + 1
