"""Tests for researcher: planner schema, search wrapper, saturation logic."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import pytest

from medbrain.agents.researcher import _is_saturated
from medbrain.agents.student import StudentResult
from medbrain.extractors.plan import QueryItem, ResearchPlan, Scope, StopCriteria


def _sr(inserted: int, duplicates: int) -> StudentResult:
    return StudentResult(
        pmid="0",
        extracted=inserted + duplicates,
        inserted=inserted,
        duplicates=duplicates,
    )


def test_saturation_window_too_small_returns_false():
    w: deque[StudentResult] = deque(maxlen=3)
    w.append(_sr(0, 5))
    w.append(_sr(0, 5))
    assert _is_saturated(w, 0.7, 3) is False


def test_saturation_triggers_on_high_duplicate_ratio():
    w: deque[StudentResult] = deque(maxlen=3)
    w.append(_sr(1, 9))
    w.append(_sr(0, 8))
    w.append(_sr(2, 8))
    # total: inserted=3, duplicates=25, ratio = 25/28 ~= 0.89
    assert _is_saturated(w, 0.7, 3) is True


def test_saturation_does_not_trigger_below_threshold():
    w: deque[StudentResult] = deque(maxlen=3)
    w.append(_sr(5, 1))
    w.append(_sr(4, 2))
    w.append(_sr(6, 1))
    # ratio = 4/19 = 0.21
    assert _is_saturated(w, 0.7, 3) is False


def test_saturation_empty_window_returns_true():
    w: deque[StudentResult] = deque(maxlen=3)
    w.append(_sr(0, 0))
    w.append(_sr(0, 0))
    w.append(_sr(0, 0))
    assert _is_saturated(w, 0.7, 3) is True


# --- planner schema ---


def test_research_plan_validates_minimal():
    plan = ResearchPlan(
        topic="malaria",
        scope=Scope.BROAD,
        decomposition=["epidemiology", "treatment"],
        queries=[QueryItem(pubmed_query="malaria[MeSH]", max_papers=5)],
    )
    assert plan.scope == Scope.BROAD
    assert plan.queries[0].max_papers == 5
    assert plan.stop_criteria.max_total_papers == 30


def test_query_item_rejects_zero_max_papers():
    with pytest.raises(Exception):
        QueryItem(pubmed_query="x", max_papers=0)


def test_stop_criteria_clamps_threshold():
    with pytest.raises(Exception):
        StopCriteria(duplicate_ratio_threshold=1.5)
