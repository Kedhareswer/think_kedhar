"""Threshold sensitivity report for Phase 7.

Reads corpus/thresholds.json and probes the CURRENT corpus state to estimate
sensitivity for each knob. This is non-destructive — no LLM calls, no DB writes.
For knobs that need a real ingest sweep, output a recommended sweep command.

Usage:
    python scripts/phase7_tune.py
    python scripts/phase7_tune.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from medbrain.db import session_scope
from medbrain.dream import decay
from medbrain.models import Claim, Salience, Source

CORPUS_FILE = ROOT / "corpus" / "thresholds.json"


def _corpus_snapshot() -> dict:
    """One-shot read of distributions we need for sensitivity math."""
    with session_scope() as sess:
        n_claims = sess.execute(select(func.count(Claim.claim_id))).scalar_one()
        n_sources = sess.execute(select(func.count(Source.source_id))).scalar_one()
        n_salience = sess.execute(select(func.count(Salience.entity))).scalar_one()
        # last_accessed distribution buckets: <30d, 30-90d, 90-180d, 180-365d, >365d
        now = datetime.now(UTC)
        buckets = {"<30d": 0, "30-90d": 0, "90-180d": 0, "180-365d": 0, ">365d": 0}
        rows = sess.execute(select(Salience.last_accessed, Salience.grace_score)).all()
        for last, grace in rows:
            if last is None:
                continue
            if last.tzinfo is None:
                last = last.replace(tzinfo=UTC)
            d = (now - last).days
            key = ("<30d" if d < 30 else "30-90d" if d < 90 else "90-180d" if d < 180 else "180-365d" if d < 365 else ">365d")
            buckets[key] += 1
    return {
        "claims": n_claims,
        "sources": n_sources,
        "salience_rows": n_salience,
        "salience_age_buckets": buckets,
    }


def _sensitivity_for_decay(snap: dict, sweep: list, knob: str) -> list[dict]:
    out = []
    buckets = snap["salience_age_buckets"]
    if knob == "salience.unread_threshold_days":
        for d in sweep:
            decayed = sum(v for k, v in buckets.items()
                          if k != "<30d" and _bucket_min_days(k) >= d)
            out.append({"value": d, "would_decay_now": decayed})
    elif knob == "salience.archive_floor":
        for floor in sweep:
            with session_scope() as sess:
                n = sess.execute(
                    select(func.count(Salience.entity)).where(Salience.grace_score <= floor)
                ).scalar_one()
            out.append({"value": floor, "would_archive_now": n})
    elif knob == "salience.decay_step":
        for step in sweep:
            from_fresh = int(round((1.0 - decay.ARCHIVE_FLOOR_DEFAULT) / step + 0.5))
            out.append({"value": step, "passes_to_archive_from_fresh": from_fresh})
    return out


def _bucket_min_days(key: str) -> int:
    return {"<30d": 0, "30-90d": 30, "90-180d": 90, "180-365d": 180, ">365d": 365}[key]


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7 threshold sensitivity")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    spec = json.loads(CORPUS_FILE.read_text(encoding="utf-8"))
    snap = _corpus_snapshot()

    report = {"snapshot": snap, "knobs": []}
    for k in spec["knobs"]:
        entry = {
            "name": k["name"],
            "default": k["default"],
            "sweep": k["sweep"],
            "lives_in": k["lives_in"],
            "metric": k["metric"],
            "current_corpus_implication": [],
        }
        if k["name"].startswith("salience."):
            entry["current_corpus_implication"] = _sensitivity_for_decay(snap, k["sweep"], k["name"])
        else:
            entry["current_corpus_implication"] = [
                {"value": v, "note": "needs real ingest sweep — re-run phase7_run.py with this knob set"}
                for v in k["sweep"]
            ]
        report["knobs"].append(entry)

    if args.json:
        print(json.dumps(report, indent=2, default=str))
        return 0

    print(f"# corpus snapshot")
    print(f"  claims={snap['claims']} sources={snap['sources']} salience_rows={snap['salience_rows']}")
    print(f"  last_accessed buckets: {snap['salience_age_buckets']}")
    print()
    print(f"# knob sensitivity")
    for k in report["knobs"]:
        print(f"## {k['name']}  (default={k['default']})")
        print(f"   in: {k['lives_in']}")
        print(f"   metric: {k['metric']}")
        for row in k["current_corpus_implication"]:
            print(f"   {row}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
