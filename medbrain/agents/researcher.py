"""Researcher agent: natural-language topic -> plan -> search -> ingest loop.

Wraps the per-PMID Student in a topic-driven outer loop. The Student handles
fetch/extract/novelty/insert; the Researcher decides what to ingest and when
to stop.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from medbrain.agents.student import StudentResult, ingest_pmid
from medbrain.extractors.plan import QueryItem, ResearchPlan, plan_research
from medbrain.regen.coordinator import RegenResult, regenerate_dirty
from medbrain.tools.pubmed import search


@dataclass
class QueryRunResult:
    subtopic: str
    pubmed_query: str
    pmids_found: int
    pmids_attempted: int
    pmids_succeeded: int
    pmids_failed: int
    saturation_stop: bool
    per_pmid: list[StudentResult] = field(default_factory=list)


@dataclass
class ResearchResult:
    topic: str
    plan: ResearchPlan
    query_runs: list[QueryRunResult] = field(default_factory=list)
    total_papers_ingested: int = 0
    total_claims_extracted: int = 0
    total_claims_inserted: int = 0
    total_duplicates: int = 0
    cap_hit: bool = False
    regen: RegenResult | None = None


def _is_saturated(window: deque[StudentResult], threshold: float, min_size: int) -> bool:
    if len(window) < min_size:
        return False
    total_inserted = sum(r.inserted for r in window)
    total_duplicates = sum(r.duplicates for r in window)
    seen = total_inserted + total_duplicates
    if seen == 0:
        return True  # window of empty ingests = nothing to learn
    duplicate_ratio = total_duplicates / seen
    return duplicate_ratio >= threshold


def _run_query(
    item: QueryItem,
    *,
    saturation_window_size: int,
    duplicate_ratio_threshold: float,
    remaining_global_cap: int,
) -> QueryRunResult:
    pmids = search(item.pubmed_query, retmax=item.max_papers)
    qrr = QueryRunResult(
        subtopic=item.subtopic,
        pubmed_query=item.pubmed_query,
        pmids_found=len(pmids),
        pmids_attempted=0,
        pmids_succeeded=0,
        pmids_failed=0,
        saturation_stop=False,
    )

    window: deque[StudentResult] = deque(maxlen=saturation_window_size)
    cap_left = remaining_global_cap

    for pmid in pmids:
        if cap_left <= 0:
            break
        qrr.pmids_attempted += 1
        try:
            result = ingest_pmid(pmid)
            qrr.pmids_succeeded += 1
            qrr.per_pmid.append(result)
            window.append(result)
            cap_left -= 1
        except Exception as e:
            qrr.pmids_failed += 1
            print(f"[researcher] PMID {pmid} failed: {e}")
            continue

        if _is_saturated(window, duplicate_ratio_threshold, saturation_window_size):
            qrr.saturation_stop = True
            break

    return qrr


def ingest_topic(topic: str, *, regen: bool = True) -> ResearchResult:
    """Plan + execute a research session for a topic. Synchronous, returns summary.

    By default runs concept/topic regeneration on all dirty entities + topics
    after the ingest loop. Pass regen=False for a pure-ingest run (debug).
    """
    plan = plan_research(topic)

    result = ResearchResult(topic=topic, plan=plan)
    cap_left = plan.stop_criteria.max_total_papers

    for item in plan.queries:
        if cap_left <= 0:
            result.cap_hit = True
            break
        qrr = _run_query(
            item,
            saturation_window_size=plan.stop_criteria.saturation_window,
            duplicate_ratio_threshold=plan.stop_criteria.duplicate_ratio_threshold,
            remaining_global_cap=cap_left,
        )
        result.query_runs.append(qrr)
        result.total_papers_ingested += qrr.pmids_succeeded
        cap_left -= qrr.pmids_succeeded
        for sr in qrr.per_pmid:
            result.total_claims_extracted += sr.extracted
            result.total_claims_inserted += sr.inserted
            result.total_duplicates += sr.duplicates

    if cap_left <= 0 and any(item.max_papers > 0 for item in plan.queries):
        result.cap_hit = True

    if regen and result.total_claims_inserted > 0:
        result.regen = regenerate_dirty()

    return result
