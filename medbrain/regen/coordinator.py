"""Drive regeneration of all dirty entities + topics, mark processed.

Two entry points:
  regenerate_dirty(): batch — process every unprocessed dirty_tracker row.
  regenerate_for_session(entities, topics): targeted — process the ones the
    Researcher just touched, regardless of dirty_tracker state.
"""

from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from medbrain.db import session_scope
from medbrain.enums import ClaimStatus
from medbrain.models import Claim, DirtyTracker
from medbrain.regen.canonical import canonicalize
from medbrain.regen.concepts import (
    regenerate_concept,
    regenerate_concept_canonical,
)
from medbrain.regen.notes import regenerate_topic
from medbrain.regen.topics import topics_for

REGEN_MIN_CLAIMS = int(os.getenv("MEDBRAIN_REGEN_MIN_CLAIMS", "2"))


@dataclass
class RegenResult:
    entities_processed: int = 0
    entities_failed: int = 0
    topics_processed: int = 0
    topics_failed: int = 0
    paths_written: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _mark_processed(sess: Session, kind: str, name: str) -> None:
    rows = (
        sess.execute(
            select(DirtyTracker).where(
                DirtyTracker.kind == kind,
                DirtyTracker.name == name,
                DirtyTracker.processed_at.is_(None),
            )
        )
        .scalars()
        .all()
    )
    now = datetime.now(UTC)
    for r in rows:
        r.processed_at = now


def regenerate_dirty() -> RegenResult:
    """Process all unprocessed dirty_tracker rows.

    Two efficiency layers vs naive per-row iteration:
      1. Entity surface forms are collapsed by `canonicalize()` so all variants of
         a real entity (e.g. 'P. falciparum (Cambodian)' / 'P. falciparum with
         kelch13 mutation') share one concept .md and one LLM call.
      2. Entities/topics with fewer than MEDBRAIN_REGEN_MIN_CLAIMS supporting
         claims are skipped — building a concept page from a single claim is
         net waste. They're still marked processed so the dirty queue clears.
    """
    with session_scope() as sess:
        rows = (
            sess.execute(
                select(DirtyTracker.kind, DirtyTracker.name)
                .where(DirtyTracker.processed_at.is_(None))
                .distinct()
            )
            .all()
        )
        entities_raw = sorted({name for kind, name in rows if kind == "entity"})
        topics_raw = sorted({name for kind, name in rows if kind == "topic"})

        # Group entity surface forms by canonical key.
        entity_groups: dict[str, list[str]] = defaultdict(list)
        for raw in entities_raw:
            key = canonicalize(raw)
            if key:
                entity_groups[key].append(raw)

        # Per-canonical-entity claim counts (any variant counts).
        entity_claim_counts: dict[str, int] = {}
        for canonical, variants in entity_groups.items():
            n = sess.execute(
                select(Claim)
                .where(
                    or_(
                        Claim.subject_text.in_(variants),
                        Claim.object_text.in_(variants),
                    ),
                    Claim.status != ClaimStatus.REJECTED,
                )
            ).scalars().all()
            entity_claim_counts[canonical] = len(n)

        # Per-topic claim counts (topics are already canonical buckets).
        all_claims = sess.execute(
            select(Claim).where(Claim.status != ClaimStatus.REJECTED)
        ).scalars().all()
        topic_claim_counts: dict[str, int] = defaultdict(int)
        for c in all_claims:
            for t in topics_for(c.predicate, c.subject_text, c.object_text):
                topic_claim_counts[t] += 1

    result = RegenResult()

    # ENTITIES — regen canonical groups with >= REGEN_MIN_CLAIMS, skip-mark the rest.
    for canonical, variants in sorted(entity_groups.items()):
        n_claims = entity_claim_counts.get(canonical, 0)
        if n_claims < REGEN_MIN_CLAIMS:
            with session_scope() as sess:
                for v in variants:
                    _mark_processed(sess, "entity", v)
            continue
        try:
            with session_scope() as sess:
                path = regenerate_concept_canonical(sess, canonical, variants)
                for v in variants:
                    _mark_processed(sess, "entity", v)
            if path is not None:
                result.entities_processed += 1
                result.paths_written.append(str(path))
        except Exception as e:
            result.entities_failed += 1
            result.errors.append(f"entity {canonical!r}: {e}")

    # TOPICS — regen those with >= REGEN_MIN_CLAIMS, skip-mark the rest.
    for topic in topics_raw:
        if topic_claim_counts.get(topic, 0) < REGEN_MIN_CLAIMS:
            with session_scope() as sess:
                _mark_processed(sess, "topic", topic)
            continue
        try:
            with session_scope() as sess:
                path = regenerate_topic(sess, topic)
                _mark_processed(sess, "topic", topic)
            if path is not None:
                result.topics_processed += 1
                result.paths_written.append(str(path))
        except Exception as e:
            result.topics_failed += 1
            result.errors.append(f"topic {topic!r}: {e}")

    return result


def regenerate_for_session(*, entities: list[str], topics: list[str]) -> RegenResult:
    """Regenerate the given entities + topics, then mark them processed."""
    result = RegenResult()

    for entity in entities:
        try:
            with session_scope() as sess:
                path = regenerate_concept(sess, entity)
                _mark_processed(sess, "entity", entity)
            if path is not None:
                result.entities_processed += 1
                result.paths_written.append(str(path))
        except Exception as e:
            result.entities_failed += 1
            result.errors.append(f"entity {entity!r}: {e}")

    for topic in topics:
        try:
            with session_scope() as sess:
                path = regenerate_topic(sess, topic)
                _mark_processed(sess, "topic", topic)
            if path is not None:
                result.topics_processed += 1
                result.paths_written.append(str(path))
        except Exception as e:
            result.topics_failed += 1
            result.errors.append(f"topic {topic!r}: {e}")

    return result
