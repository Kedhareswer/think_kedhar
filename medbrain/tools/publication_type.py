"""Map PubMed PublicationType strings to EvidenceGrade enum.

PubMed publication types are inconsistent — some abstracts list
"Journal Article" first, others list the study type. We pick the
strongest applicable grade from the list.
"""

from __future__ import annotations

from medbrain.enums import EvidenceGrade

_RANK: dict[EvidenceGrade, int] = {
    EvidenceGrade.META_ANALYSIS: 7,
    EvidenceGrade.RCT: 6,
    EvidenceGrade.GUIDELINE: 5,
    EvidenceGrade.COHORT: 4,
    EvidenceGrade.CASE_CONTROL: 3,
    EvidenceGrade.CASE_REPORT: 2,
    EvidenceGrade.EXPERT_OPINION: 1,
}


_PUBMED_MAP: dict[str, EvidenceGrade] = {
    "meta-analysis": EvidenceGrade.META_ANALYSIS,
    "systematic review": EvidenceGrade.META_ANALYSIS,
    "randomized controlled trial": EvidenceGrade.RCT,
    "controlled clinical trial": EvidenceGrade.RCT,
    "clinical trial, phase iii": EvidenceGrade.RCT,
    "clinical trial, phase iv": EvidenceGrade.RCT,
    "clinical trial, phase ii": EvidenceGrade.RCT,
    "clinical trial, phase i": EvidenceGrade.COHORT,
    "clinical trial": EvidenceGrade.COHORT,
    "practice guideline": EvidenceGrade.GUIDELINE,
    "guideline": EvidenceGrade.GUIDELINE,
    "consensus development conference": EvidenceGrade.GUIDELINE,
    "observational study": EvidenceGrade.COHORT,
    "comparative study": EvidenceGrade.COHORT,
    "evaluation study": EvidenceGrade.COHORT,
    "multicenter study": EvidenceGrade.COHORT,
    "case-control study": EvidenceGrade.CASE_CONTROL,
    "case reports": EvidenceGrade.CASE_REPORT,
    "case report": EvidenceGrade.CASE_REPORT,
    "review": EvidenceGrade.EXPERT_OPINION,
    "editorial": EvidenceGrade.EXPERT_OPINION,
    "letter": EvidenceGrade.EXPERT_OPINION,
    "comment": EvidenceGrade.EXPERT_OPINION,
}


def grade_from_publication_types(types: list[str]) -> EvidenceGrade:
    """Return the strongest grade matching any of the publication types.

    Falls back to EXPERT_OPINION if nothing matches (rather than raising —
    we'd rather ingest with low grade than drop the paper).
    """
    best: EvidenceGrade | None = None
    best_rank = -1
    for t in types:
        key = t.strip().lower()
        grade = _PUBMED_MAP.get(key)
        if grade is None:
            continue
        if _RANK[grade] > best_rank:
            best = grade
            best_rank = _RANK[grade]
    return best or EvidenceGrade.EXPERT_OPINION
