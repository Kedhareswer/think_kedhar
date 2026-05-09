"""SQLAlchemy models — qualified-claim schema per spec §4 + §10."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Enum as SAEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from medbrain.enums import Certainty, ClaimStatus, EvidenceGrade, Predicate, SourceType


def _uuid() -> str:
    return str(uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Source(Base):
    __tablename__ = "sources"

    source_id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    source_type: Mapped[SourceType] = mapped_column(SAEnum(SourceType), index=True)
    external_id: Mapped[str] = mapped_column(String, index=True, unique=True)
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    publication_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    publication_type: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    claims: Mapped[list["Claim"]] = relationship(back_populates="source")


class Claim(Base):
    __tablename__ = "claims"

    claim_id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)

    subject_text: Mapped[str] = mapped_column(String, index=True)
    subject_concept_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    predicate: Mapped[Predicate] = mapped_column(SAEnum(Predicate), index=True)

    object_text: Mapped[str] = mapped_column(String, index=True)
    object_concept_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    qualifiers: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    certainty: Mapped[Certainty] = mapped_column(SAEnum(Certainty), default=Certainty.MODERATE)

    valid_from: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)

    source_id: Mapped[str] = mapped_column(String, ForeignKey("sources.source_id"), index=True)
    source: Mapped[Source] = relationship(back_populates="claims")

    evidence_grade: Mapped[EvidenceGrade] = mapped_column(SAEnum(EvidenceGrade), index=True)

    supersedes_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("claims.claim_id"), nullable=True
    )

    status: Mapped[ClaimStatus] = mapped_column(
        SAEnum(ClaimStatus), default=ClaimStatus.PENDING_REVIEW, index=True
    )

    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)


class EvidenceLedger(Base):
    """Insert-only audit trail. Spec §10."""

    __tablename__ = "evidence_ledger"

    ledger_id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    claim_id: Mapped[str] = mapped_column(String, ForeignKey("claims.claim_id"), index=True)
    source_id: Mapped[str] = mapped_column(String, ForeignKey("sources.source_id"))
    evidence_grade: Mapped[EvidenceGrade] = mapped_column(SAEnum(EvidenceGrade))
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)


class DirtyTracker(Base):
    """Entities and topics needing regeneration. Cleared by Brain after processing."""

    __tablename__ = "dirty_tracker"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String, index=True)  # "entity" | "topic"
    name: Mapped[str] = mapped_column(String, index=True)
    marked_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)


class Salience(Base):
    """Per-entity usage stats. Drives Dream-cycle decay. Spec §10."""

    __tablename__ = "salience"

    entity: Mapped[str] = mapped_column(String, primary_key=True)
    query_count: Mapped[int] = mapped_column(Integer, default=0)
    citation_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    grace_score: Mapped[float] = mapped_column(Float, default=1.0)


class BrainRun(Base):
    """Tracks Brain-agent execution history. Drives 'what changed since last run' queries."""

    __tablename__ = "brain_runs"

    run_id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    concepts_read: Mapped[int] = mapped_column(Integer, default=0)
    topics_read: Mapped[int] = mapped_column(Integer, default=0)
    questions_added: Mapped[int] = mapped_column(Integer, default=0)
    questions_resolved: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class DreamRun(Base):
    """Tracks Dream-agent execution history. Drives --check cadence guard."""

    __tablename__ = "dream_runs"

    run_id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    files_compacted: Mapped[int] = mapped_column(Integer, default=0)
    files_skipped: Mapped[int] = mapped_column(Integer, default=0)
    derivatives_written: Mapped[int] = mapped_column(Integer, default=0)
    entities_decayed: Mapped[int] = mapped_column(Integer, default=0)
    entities_archived: Mapped[int] = mapped_column(Integer, default=0)
    snapshot_path: Mapped[str | None] = mapped_column(String, nullable=True)
    restored: Mapped[int] = mapped_column(Integer, default=0)  # 0/1 bool-as-int for SQLite simplicity
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
