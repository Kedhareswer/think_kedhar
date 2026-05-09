"""Enum types used across models."""

from __future__ import annotations

import enum


class Predicate(str, enum.Enum):
    TREATS = "treats"
    CAUSES = "causes"
    RESISTS = "resists"
    REQUIRES = "requires"
    CONTRAINDICATES = "contraindicates"
    PREVENTS = "prevents"
    CO_OCCURS = "co_occurs"
    RECOMMENDS = "recommends"
    SUPERSEDES = "supersedes"


class EvidenceGrade(str, enum.Enum):
    META_ANALYSIS = "meta_analysis"
    RCT = "RCT"
    GUIDELINE = "guideline"
    COHORT = "cohort"
    CASE_CONTROL = "case_control"
    CASE_REPORT = "case_report"
    EXPERT_OPINION = "expert_opinion"


HIGH_GRADES: frozenset[EvidenceGrade] = frozenset(
    {
        EvidenceGrade.META_ANALYSIS,
        EvidenceGrade.RCT,
        EvidenceGrade.GUIDELINE,
        EvidenceGrade.COHORT,
    }
)


class Certainty(str, enum.Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very_low"


class ClaimStatus(str, enum.Enum):
    AUTO_PROMOTED = "auto_promoted"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class SourceType(str, enum.Enum):
    PUBMED = "pubmed"
    WHO_GUIDELINE = "who_guideline"
