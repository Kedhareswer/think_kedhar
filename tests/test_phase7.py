"""Phase 7 harness tests — corpus parsing, query dispatch, report writer.

No live LLM, no live PubMed. Stubs the menu primitives and pipeline stages
so we verify the orchestrator's plumbing only.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts import phase7_run  # noqa: E402


def test_corpus_files_exist_and_parse():
    topics = phase7_run.load_topics()
    queries = phase7_run.load_queries()

    assert topics["version"]
    assert "categories" in topics
    assert isinstance(topics["topics"], list) and len(topics["topics"]) >= 10
    seen_ids = {t["id"] for t in topics["topics"]}
    assert len(seen_ids) == len(topics["topics"]), "topic IDs must be unique"
    for t in topics["topics"]:
        assert t["category"] in topics["categories"], f"unknown category {t['category']}"
        assert t["topic"].strip()

    assert queries["version"]
    assert isinstance(queries["queries"], list)
    assert len(queries["queries"]) == 10, "10 CDS queries expected"
    qids = {q["id"] for q in queries["queries"]}
    assert len(qids) == 10
    valid_primitives = {
        "lookup", "neighborhood", "path", "community",
        "scoped", "recent", "gaps", "evidence_pack",
    }
    for q in queries["queries"]:
        assert q["primitive"] in valid_primitives, q


def test_run_queries_dispatches_each_primitive(monkeypatch):
    """run_queries must call menu.<primitive> with the right args and capture envelopes."""
    calls: list[tuple[str, tuple, dict]] = []

    def _fake(name, *args, **kwargs):
        calls.append((name, args, kwargs))
        return {
            "version": "1.0",
            "primitive": name,
            "args": kwargs or {"_pos": args},
            "data": {"node": {"id": "x"}, "neighbors": [], "edges": [], "nodes": [], "paths": [], "claims": [], "audit": {}},
            "derivative_included": False,
            "generated_at": "2026-05-04T00:00:00+00:00",
        }

    from medbrain.api import menu

    monkeypatch.setattr(menu, "lookup", lambda e: _fake("lookup", entity=e))
    monkeypatch.setattr(menu, "neighborhood", lambda e, hops=1: _fake("neighborhood", entity=e, hops=hops))
    monkeypatch.setattr(menu, "path", lambda a, b, max_paths=3: _fake("path", a=a, b=b, max_paths=max_paths))
    monkeypatch.setattr(menu, "community", lambda community_id=None, topic=None: _fake("community", community_id=community_id, topic=topic))
    monkeypatch.setattr(menu, "scoped", lambda **kw: _fake("scoped", **kw))
    monkeypatch.setattr(menu, "recent", lambda since: _fake("recent", since=since))
    monkeypatch.setattr(menu, "gaps", lambda: _fake("gaps"))
    monkeypatch.setattr(menu, "evidence_pack", lambda cids: _fake("evidence_pack", cids=cids))
    monkeypatch.setattr(phase7_run, "_resolve_claim_ids", lambda strategy, n: ["c1", "c2"])

    spec = phase7_run.load_queries()
    outs = phase7_run.run_queries(spec)

    assert len(outs) == 10
    assert all(o.ok for o in outs), [(o.id, o.error) for o in outs if not o.ok]
    primitives_called = [c[0] for c in calls]
    assert {"lookup", "neighborhood", "path", "community", "scoped",
            "recent", "gaps", "evidence_pack"}.issubset(set(primitives_called))


def test_envelope_excerpt_trims_bulky_fields():
    env = {
        "primitive": "lookup",
        "args": {"entity": "x"},
        "derivative_included": False,
        "data": {
            "node": {"id": "x"},
            "neighbors": [{"id": "y"}, {"id": "z"}],
            "edges": [{"k": 1}],
        },
    }
    ex = phase7_run._envelope_excerpt(env)
    assert ex["node_present"] is True
    assert ex["neighbors_count"] == 2
    assert ex["edges_count"] == 1
    assert "node" not in ex  # bulky body dropped


def test_category_coverage_and_verdict():
    topics_doc = phase7_run.load_topics()
    outcomes = [
        phase7_run.TopicOutcome(id=t["id"], category=t["category"], topic=t["topic"],
                                started_at="t0", completed_at="t1",
                                papers_ingested=4, claims_inserted=10, duplicates=1,
                                pmids=[f"PMID{t['id']}{i}" for i in range(4)])
        for t in topics_doc["topics"]
    ]
    coverage = phase7_run.category_coverage(outcomes, topics_doc["categories"])
    assert coverage["distinct_pmids"] >= 50
    assert not coverage["categories_missing"]

    fake_queries = [phase7_run.QueryOutcome(id=f"Q{i:02d}", primitive="lookup",
                                            args={}, ok=True, elapsed_ms=1, summary="ok")
                    for i in range(1, 11)]
    v = phase7_run.verdict(coverage, fake_queries)
    assert v["overall_pass"] is True


def test_verdict_fails_when_pmids_short():
    topics_doc = phase7_run.load_topics()
    outcomes = [
        phase7_run.TopicOutcome(id=topics_doc["topics"][0]["id"],
                                category=topics_doc["topics"][0]["category"],
                                topic=topics_doc["topics"][0]["topic"],
                                started_at="t0", completed_at="t1",
                                papers_ingested=2, claims_inserted=2, duplicates=0,
                                pmids=["PMID-A", "PMID-B"])
    ]
    coverage = phase7_run.category_coverage(outcomes, topics_doc["categories"])
    fake_queries = [phase7_run.QueryOutcome(id="Q01", primitive="lookup",
                                            args={}, ok=True, elapsed_ms=1, summary="ok")]
    v = phase7_run.verdict(coverage, fake_queries)
    assert v["pmid_target_met"] is False
    assert v["overall_pass"] is False


def test_write_report_creates_file(monkeypatch):
    tmp_path = ROOT / "tests" / "fixtures" / "_phase7_tmp"
    tmp_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(phase7_run.config, "BRAIN_DIR", tmp_path)
    monkeypatch.setattr(phase7_run, "REPORT_PATH", tmp_path / "phase7_report.md")
    monkeypatch.setattr(phase7_run.config, "ensure_brain_dirs", lambda: None)

    started = datetime.now(UTC)
    completed = datetime.now(UTC)
    outcomes = [phase7_run.TopicOutcome(id="T01", category="rct", topic="x",
                                        started_at="t", completed_at="t",
                                        papers_ingested=3, claims_inserted=5)]
    qs = [phase7_run.QueryOutcome(id="Q01", primitive="lookup", args={"entity": "x"},
                                  ok=True, elapsed_ms=4, summary="ok",
                                  envelope_excerpt={"primitive": "lookup"})]
    coverage = {"distinct_pmids": 0, "categories_seen": {"rct": 3}, "categories_missing": ["cohort"]}
    verd = {"pmid_target_met": False, "category_coverage_met": False,
            "queries_all_passed": True, "overall_pass": False}
    path = phase7_run.write_report(outcomes, qs, coverage, verd,
                                   started=started, completed=completed)
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Phase 7" in text
    assert "T01" in text and "Q01" in text
    assert "FAIL" in text
