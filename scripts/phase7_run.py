"""Phase 7 end-to-end validation runner.

Loads corpus/topics.json + corpus/cds_queries.json, drives the full pipeline,
and emits brain/phase7_report.md with category coverage, per-query envelopes,
and acceptance verdicts.

Usage:
    python scripts/phase7_run.py                  # full run (ingests, may be slow + LLM-billed)
    python scripts/phase7_run.py --skip-ingest    # only graphify + brain + queries (re-uses existing claims)
    python scripts/phase7_run.py --queries-only   # only the 10 CDS queries (assumes graph is built)
    python scripts/phase7_run.py --topics T01,T08 # subset of topics
    python scripts/phase7_run.py --dry-run        # parse corpus, print plan, no work
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import desc, select

from medbrain import config
from medbrain.agents.brain import run_brain
from medbrain.agents.graphify import run_graphify
from medbrain.agents.researcher import ResearchResult, ingest_topic
from medbrain.api import menu
from medbrain.db import session_scope
from medbrain.enums import EvidenceGrade
from medbrain.models import Claim, Source

CORPUS_DIR = ROOT / "corpus"
TOPICS_FILE = CORPUS_DIR / "topics.json"
QUERIES_FILE = CORPUS_DIR / "cds_queries.json"
REPORT_PATH = config.BRAIN_DIR / "phase7_report.md"


@dataclass
class TopicOutcome:
    id: str
    category: str
    topic: str
    started_at: str
    completed_at: str | None = None
    papers_ingested: int = 0
    claims_inserted: int = 0
    duplicates: int = 0
    pmids: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class QueryOutcome:
    id: str
    primitive: str
    args: dict
    ok: bool
    elapsed_ms: int
    summary: str
    envelope_excerpt: dict = field(default_factory=dict)
    error: str | None = None


# ---------- corpus loaders ----------


def load_topics() -> dict:
    return json.loads(TOPICS_FILE.read_text(encoding="utf-8"))


def load_queries() -> dict:
    return json.loads(QUERIES_FILE.read_text(encoding="utf-8"))


# ---------- pipeline stages ----------


def run_ingest(topics: list[dict], *, regen: bool = True) -> list[TopicOutcome]:
    outcomes: list[TopicOutcome] = []
    for t in topics:
        out = TopicOutcome(
            id=t["id"],
            category=t["category"],
            topic=t["topic"],
            started_at=datetime.now(UTC).isoformat(),
        )
        print(f"[phase7] ingest {t['id']} ({t['category']}): {t['topic']}", flush=True)
        try:
            r: ResearchResult = ingest_topic(t["topic"], regen=regen)
            out.papers_ingested = r.total_papers_ingested
            out.claims_inserted = r.total_claims_inserted
            out.duplicates = r.total_duplicates
            for qr in r.query_runs:
                for sr in qr.per_pmid:
                    if sr.inserted > 0 or sr.duplicates > 0:
                        out.pmids.append(sr.pmid)
        except Exception as e:
            out.error = f"{type(e).__name__}: {e}"
            print(f"[phase7] ERROR {t['id']}: {out.error}", flush=True)
            traceback.print_exc()
        out.completed_at = datetime.now(UTC).isoformat()
        outcomes.append(out)
    return outcomes


def _resolve_claim_ids(strategy: str, n: int) -> list[str]:
    if strategy != "auto_top_n_high_grade":
        return []
    grade_rank = [
        EvidenceGrade.META_ANALYSIS,
        EvidenceGrade.RCT,
        EvidenceGrade.GUIDELINE,
        EvidenceGrade.COHORT,
        EvidenceGrade.CASE_CONTROL,
        EvidenceGrade.CASE_REPORT,
        EvidenceGrade.EXPERT_OPINION,
    ]
    out: list[str] = []
    with session_scope() as sess:
        for g in grade_rank:
            rows = (
                sess.execute(
                    select(Claim.claim_id)
                    .where(Claim.evidence_grade == g)
                    .order_by(desc(Claim.ingested_at))
                    .limit(n - len(out))
                )
                .scalars()
                .all()
            )
            out.extend(rows)
            if len(out) >= n:
                break
    return out[:n]


def _envelope_excerpt(env: dict) -> dict:
    """Trim envelope for inclusion in the report — keep verdict-relevant fields, drop bulky bodies."""
    data = env.get("data", {})
    excerpt: dict[str, Any] = {
        "primitive": env.get("primitive"),
        "args": env.get("args"),
        "derivative_included": env.get("derivative_included"),
    }
    if "node" in data:
        excerpt["node_present"] = data["node"] is not None and not (data["node"] or {}).get("missing", False)
        excerpt["neighbors_count"] = len(data.get("neighbors", []) or [])
        excerpt["edges_count"] = len(data.get("edges", []) or [])
    if "nodes" in data:
        excerpt["nodes_count"] = len(data.get("nodes", []) or [])
    if "edges" in data:
        excerpt["edges_count"] = len(data.get("edges", []) or [])
    if "paths" in data:
        excerpt["paths_count"] = len(data.get("paths", []) or [])
    if "community" in data:
        excerpt["community_present"] = data.get("community") is not None
        excerpt["members_count"] = len(data.get("members", []) or [])
    if "claims" in data:
        excerpt["claims_count"] = len(data.get("claims", []) or [])
        excerpt["claims_with_source"] = sum(
            1 for c in data.get("claims", []) if c.get("source") is not None
        )
        excerpt["claims_current"] = sum(1 for c in data.get("claims", []) if c.get("current"))
    if "audit" in data:
        a = data["audit"] or {}
        excerpt["audit_keys"] = sorted(a.keys()) if isinstance(a, dict) else None
        if isinstance(a, dict):
            excerpt["contradictions_count"] = len(a.get("contradictions") or [])
            excerpt["isolated_count"] = len(a.get("isolated") or [])
    return excerpt


def _summarize(primitive: str, env: dict) -> str:
    d = env.get("data", {})
    if primitive == "lookup":
        return f"node={'yes' if d.get('node') and not d['node'].get('missing') else 'no'} neighbors={len(d.get('neighbors',[]) or [])}"
    if primitive == "neighborhood":
        return f"nodes={len(d.get('nodes',[]) or [])} edges={len(d.get('edges',[]) or [])}"
    if primitive == "path":
        return f"paths={len(d.get('paths',[]) or [])}"
    if primitive == "community":
        c = d.get("community") or {}
        return f"present={'yes' if c else 'no'} members={len(d.get('members',[]) or [])}"
    if primitive == "scoped":
        return f"nodes={len(d.get('nodes',[]) or [])} edges={len(d.get('edges',[]) or [])}"
    if primitive == "recent":
        return f"nodes={len(d.get('nodes',[]) or [])} edges={len(d.get('edges',[]) or [])}"
    if primitive == "gaps":
        a = d.get("audit") or {}
        return f"contradictions={len(a.get('contradictions') or [])} questions_md_chars={len(d.get('questions_md','') or '')}"
    if primitive == "evidence_pack":
        cs = d.get("claims") or []
        return f"claims={len(cs)} with_source={sum(1 for c in cs if c.get('source'))}"
    return ""


def run_queries(spec: dict) -> list[QueryOutcome]:
    outcomes: list[QueryOutcome] = []
    for q in spec["queries"]:
        prim = q["primitive"]
        args = dict(q["args"])
        t0 = time.perf_counter()
        out = QueryOutcome(id=q["id"], primitive=prim, args=args, ok=False, elapsed_ms=0, summary="")
        try:
            if prim == "lookup":
                env = menu.lookup(args["entity"])
            elif prim == "neighborhood":
                env = menu.neighborhood(args["entity"], hops=int(args.get("hops", 1)))
            elif prim == "path":
                env = menu.path(args["from"], args["to"], max_paths=int(args.get("max_paths", 3)))
            elif prim == "community":
                env = menu.community(community_id=args.get("community_id"), topic=args.get("topic"))
            elif prim == "scoped":
                env = menu.scoped(
                    population_region=args.get("population_region"),
                    population_pregnancy=args.get("population_pregnancy"),
                    setting_endemic=args.get("setting_endemic"),
                    setting_care_level=args.get("setting_care_level"),
                    min_certainty=args.get("min_certainty"),
                    current_only=bool(args.get("current_only", True)),
                )
            elif prim == "recent":
                env = menu.recent(args["since"])
            elif prim == "gaps":
                env = menu.gaps()
            elif prim == "evidence_pack":
                if "claim_ids_from" in args:
                    cids = _resolve_claim_ids(args["claim_ids_from"], int(args.get("n", 10)))
                else:
                    cids = list(args.get("claim_ids") or [])
                args["resolved_claim_ids"] = cids
                env = menu.evidence_pack(cids)
            else:
                raise ValueError(f"unknown primitive {prim}")
            out.envelope_excerpt = _envelope_excerpt(env)
            out.summary = _summarize(prim, env)
            out.ok = True
        except Exception as e:
            out.error = f"{type(e).__name__}: {e}"
            traceback.print_exc()
        out.elapsed_ms = int((time.perf_counter() - t0) * 1000)
        outcomes.append(out)
    return outcomes


# ---------- coverage / verdict ----------


def category_coverage(topic_outcomes: list[TopicOutcome], categories: dict[str, str]) -> dict:
    by_cat: Counter[str] = Counter()
    pmid_set: set[str] = set()
    for o in topic_outcomes:
        if o.error is None and o.papers_ingested > 0:
            by_cat[o.category] += o.papers_ingested
        pmid_set.update(o.pmids)
    return {
        "categories_seen": dict(by_cat),
        "categories_missing": [c for c in categories if c not in by_cat],
        "distinct_pmids": len(pmid_set),
    }


def verdict(coverage: dict, queries: list[QueryOutcome]) -> dict:
    pmid_target_met = coverage["distinct_pmids"] >= 50
    cats_met = len(coverage["categories_missing"]) <= 1  # WHO/guideline path partly deferred
    ok_queries = sum(1 for q in queries if q.ok)
    queries_met = ok_queries == len(queries) and ok_queries > 0
    overall = pmid_target_met and cats_met and queries_met
    return {
        "pmid_target_met": pmid_target_met,
        "category_coverage_met": cats_met,
        "queries_all_passed": queries_met,
        "overall_pass": overall,
    }


# ---------- report writer ----------


def write_report(
    topic_outcomes: list[TopicOutcome],
    queries: list[QueryOutcome],
    coverage: dict,
    verd: dict,
    *,
    started: datetime,
    completed: datetime,
) -> Path:
    config.ensure_brain_dirs()
    lines: list[str] = []
    lines.append("# Phase 7 — End-to-End Validation Report")
    lines.append("")
    lines.append(f"- Started:   `{started.isoformat()}`")
    lines.append(f"- Completed: `{completed.isoformat()}`")
    lines.append(f"- Overall:   **{'PASS' if verd['overall_pass'] else 'FAIL'}**")
    lines.append("")
    lines.append("## Acceptance verdict")
    for k, v in verd.items():
        lines.append(f"- `{k}`: **{v}**")
    lines.append("")
    lines.append("## Coverage")
    lines.append(f"- distinct PMIDs ingested: **{coverage['distinct_pmids']}** (target ≥ 50)")
    lines.append(f"- categories_seen: `{coverage['categories_seen']}`")
    lines.append(f"- categories_missing: `{coverage['categories_missing']}`")
    lines.append("")
    lines.append("## Topic outcomes")
    lines.append("| id | category | topic | papers | claims | dupes | error |")
    lines.append("|---|---|---|---:|---:|---:|---|")
    for o in topic_outcomes:
        topic_short = o.topic if len(o.topic) <= 80 else o.topic[:77] + "..."
        err = "" if o.error is None else f"`{o.error}`"
        lines.append(
            f"| {o.id} | {o.category} | {topic_short} | "
            f"{o.papers_ingested} | {o.claims_inserted} | {o.duplicates} | {err} |"
        )
    lines.append("")
    lines.append("## CDS query outcomes")
    lines.append("| id | primitive | ok | ms | summary |")
    lines.append("|---|---|---|---:|---|")
    for q in queries:
        ok = "yes" if q.ok else "**NO**"
        summary = q.summary if q.ok else (q.error or "")
        lines.append(f"| {q.id} | {q.primitive} | {ok} | {q.elapsed_ms} | {summary} |")
    lines.append("")
    lines.append("## CDS query envelope excerpts")
    for q in queries:
        lines.append(f"### {q.id} — `{q.primitive}` args=`{json.dumps(q.args, ensure_ascii=False)}`")
        if q.ok:
            lines.append("```json")
            lines.append(json.dumps(q.envelope_excerpt, indent=2, ensure_ascii=False))
            lines.append("```")
        else:
            lines.append(f"FAILED: `{q.error}`")
        lines.append("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return REPORT_PATH


# ---------- main ----------


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7 end-to-end validation runner")
    parser.add_argument("--skip-ingest", action="store_true",
                        help="Skip ingest stage; assumes claims already in DB")
    parser.add_argument("--queries-only", action="store_true",
                        help="Skip ingest + graphify + brain; only run CDS queries")
    parser.add_argument("--topics", default="",
                        help="Comma-separated topic IDs (e.g. T01,T08); default = all")
    parser.add_argument("--no-regen", action="store_true",
                        help="Skip per-Researcher concept/note regeneration during ingest")
    parser.add_argument("--no-brain", action="store_true",
                        help="Skip running Brain agent before queries")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse corpus + print plan, do nothing")
    args = parser.parse_args()

    started = datetime.now(UTC)
    topics_doc = load_topics()
    queries_doc = load_queries()
    topics = topics_doc["topics"]

    if args.topics:
        wanted = {t.strip() for t in args.topics.split(",") if t.strip()}
        topics = [t for t in topics if t["id"] in wanted]
        if not topics:
            print(f"[phase7] no topics matched filter {sorted(wanted)}", file=sys.stderr)
            return 2

    print(f"[phase7] {len(topics)} topics, {len(queries_doc['queries'])} CDS queries")
    if args.dry_run:
        for t in topics:
            print(f"  - {t['id']} ({t['category']}): {t['topic']}")
        for q in queries_doc["queries"]:
            print(f"  Q {q['id']} {q['primitive']} {q['args']}")
        return 0

    topic_outcomes: list[TopicOutcome] = []
    if not (args.skip_ingest or args.queries_only):
        topic_outcomes = run_ingest(topics, regen=not args.no_regen)

    if not args.queries_only:
        print("[phase7] graphify rebuild")
        gr = run_graphify(include_review=False)
        print(f"  nodes={gr.node_count} edges={gr.edge_count} comms={gr.community_count}")

        if not args.no_brain:
            print("[phase7] brain run")
            br = run_brain(force_full=True)
            print(f"  concepts_read={br.concepts_read} topics_read={br.topics_read} "
                  f"q_added={br.questions_added} q_resolved={br.questions_resolved}")

    print("[phase7] running CDS queries")
    query_outcomes = run_queries(queries_doc)

    coverage = category_coverage(topic_outcomes, topics_doc["categories"])
    verd = verdict(coverage, query_outcomes)

    completed = datetime.now(UTC)
    path = write_report(topic_outcomes, query_outcomes, coverage, verd,
                        started=started, completed=completed)
    print(f"[phase7] report -> {path}")
    print(f"[phase7] verdict: {'PASS' if verd['overall_pass'] else 'FAIL'} "
          f"(pmids={coverage['distinct_pmids']}, "
          f"queries_ok={sum(1 for q in query_outcomes if q.ok)}/{len(query_outcomes)})")
    return 0 if verd["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
