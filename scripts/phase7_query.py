"""Run only the Phase 7 CDS query pack against the current graph.

Useful when you've already ingested + graphified and just want to re-run
the 10-query smoke. Prints a compact pass/fail table and per-query summary.

Usage:
    python scripts/phase7_query.py
    python scripts/phase7_query.py --json    # machine-readable output
    python scripts/phase7_query.py --only Q01,Q08
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.phase7_run import load_queries, run_queries  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 7 CDS query pack")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--only", default="", help="Comma-separated query IDs")
    args = parser.parse_args()

    spec = load_queries()
    if args.only:
        wanted = {q.strip() for q in args.only.split(",") if q.strip()}
        spec = {**spec, "queries": [q for q in spec["queries"] if q["id"] in wanted]}
        if not spec["queries"]:
            print(f"no queries matched filter {sorted(wanted)}", file=sys.stderr)
            return 2

    outs = run_queries(spec)

    if args.json:
        print(json.dumps([o.__dict__ for o in outs], indent=2, default=str))
        return 0 if all(o.ok for o in outs) else 1

    print(f"{'id':<5} {'primitive':<14} {'ok':<4} {'ms':>6}  summary")
    for o in outs:
        ok = "yes" if o.ok else "NO"
        line = f"{o.id:<5} {o.primitive:<14} {ok:<4} {o.elapsed_ms:>6}  {o.summary if o.ok else (o.error or '')}"
        print(line)
    fails = [o.id for o in outs if not o.ok]
    print(f"\n{len(outs) - len(fails)}/{len(outs)} ok" + (f"; failed: {fails}" if fails else ""))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
