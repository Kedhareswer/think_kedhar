"""Student agent: ingest a single PubMed paper end-to-end.

Phase 1 scope: fetch -> extract -> novelty gate -> insert claims + dirty-track.
Phase 2 will add concepts/notes regeneration.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from medbrain.db import session_scope
from medbrain.enums import ClaimStatus, SourceType
from medbrain.extractors.claims import extract_from_pubmed_abstract
from medbrain.extractors.novelty import evaluate
from medbrain.models import Claim, DirtyTracker, EvidenceLedger, Source
from medbrain.regen.topics import topics_for
from medbrain.tools.publication_type import grade_from_publication_types
from medbrain.tools.pubmed import PubMedArticle, fetch_article


@dataclass
class StudentResult:
    pmid: str
    source_id: str | None = None
    extracted: int = 0
    inserted: int = 0
    duplicates: int = 0
    auto_promoted: int = 0
    pending_review: int = 0
    contradictions_flagged: int = 0
    dirty_entities: list[str] = field(default_factory=list)
    dirty_topics: list[str] = field(default_factory=list)


def _upsert_source(sess: Session, art: PubMedArticle) -> Source:
    existing = sess.execute(
        select(Source).where(Source.external_id == f"PMID:{art.pmid}")
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    src = Source(
        source_type=SourceType.PUBMED,
        external_id=f"PMID:{art.pmid}",
        url=art.url,
        title=art.title,
        publication_date=art.publication_date,
        publication_type=art.primary_publication_type,
        raw_text=art.abstract,
    )
    sess.add(src)
    sess.flush()
    return src


def _mark_dirty(sess: Session, kind: str, name: str) -> None:
    name = name.strip()
    if not name:
        return
    existing = sess.execute(
        select(DirtyTracker).where(
            DirtyTracker.kind == kind,
            DirtyTracker.name == name,
            DirtyTracker.processed_at.is_(None),
        )
    ).scalar_one_or_none()
    if existing is not None:
        return
    sess.add(DirtyTracker(kind=kind, name=name))


def ingest_pmid(pmid: str) -> StudentResult:
    """Run Student agent for one PMID. Returns summary."""
    art = fetch_article(pmid)
    grade = grade_from_publication_types(art.publication_types)
    extracted = extract_from_pubmed_abstract(
        art.title, art.abstract, publication_types=art.publication_types
    )

    result = StudentResult(pmid=pmid, extracted=len(extracted))

    with session_scope() as sess:
        src = _upsert_source(sess, art)
        result.source_id = src.source_id

        for cand in extracted:
            decision = evaluate(sess, cand, grade)
            if decision.is_duplicate:
                result.duplicates += 1
                continue

            claim = Claim(
                subject_text=cand.subject,
                predicate=cand.predicate,
                object_text=cand.object,
                qualifiers=cand.qualifiers.to_storage(),
                certainty=cand.certainty,
                source_id=src.source_id,
                evidence_grade=grade,
                status=decision.status,
            )
            sess.add(claim)
            sess.flush()

            sess.add(
                EvidenceLedger(
                    claim_id=claim.claim_id,
                    source_id=src.source_id,
                    evidence_grade=grade,
                    note=cand.evidence_note or None,
                )
            )

            _mark_dirty(sess, "entity", cand.subject)
            _mark_dirty(sess, "entity", cand.object)
            for topic in topics_for(cand.predicate, cand.subject, cand.object):
                _mark_dirty(sess, "topic", topic)

            result.inserted += 1
            if claim.status == ClaimStatus.AUTO_PROMOTED:
                result.auto_promoted += 1
            else:
                result.pending_review += 1
            if decision.contradicts:
                result.contradictions_flagged += len(decision.contradicts)

    # Snapshot dirty entities + topics (read after commit).
    with session_scope() as sess:
        ent_rows = sess.execute(
            select(DirtyTracker.name)
            .where(DirtyTracker.kind == "entity", DirtyTracker.processed_at.is_(None))
            .distinct()
        ).all()
        top_rows = sess.execute(
            select(DirtyTracker.name)
            .where(DirtyTracker.kind == "topic", DirtyTracker.processed_at.is_(None))
            .distinct()
        ).all()
        result.dirty_entities = [r[0] for r in ent_rows]
        result.dirty_topics = [r[0] for r in top_rows]

    return result
