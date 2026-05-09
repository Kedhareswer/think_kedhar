"""CLI: run the Dream agent.

Usage:
    python scripts/dream.py                # run if cadence due, else exit 0
    python scripts/dream.py --force        # run regardless of cadence
    python scripts/dream.py --check        # exit 0 if due (prints reason), 1 if not
    python scripts/dream.py --dry-run      # print what WOULD run, no mutations
    python scripts/dream.py --skip compact --skip derivative --skip decay
    python scripts/dream.py --cadence-days 14
    python scripts/dream.py --keep-snapshots 5

Schedule recipe (Windows Task Scheduler):
    schtasks /Create /TN "MedBrain Dream" /TR "powershell -NoProfile -Command \\"
        cd D:\\MedBrain; .\\.venv\\Scripts\\python.exe scripts\\dream.py >> brain\\dream.log 2>&1\\"" /SC WEEKLY /D SUN /ST 03:00

Schedule recipe (cron):
    0 3 * * 0  cd /path/to/MedBrain && .venv/bin/python scripts/dream.py >> brain/dream.log 2>&1
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from medbrain.agents.dream import (
    DEFAULT_CADENCE_DAYS,
    DEFAULT_SNAPSHOTS_KEPT,
    is_due,
    run_dream,
)

VALID_SKIP = {"compact", "derivative", "decay"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Dream agent")
    parser.add_argument("--check", action="store_true",
                        help="Exit 0 + print reason if a Dream run is due; exit 1 otherwise")
    parser.add_argument("--force", action="store_true",
                        help="Run even if cadence guard says not due")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print intent, do not snapshot or mutate")
    parser.add_argument("--cadence-days", type=int, default=DEFAULT_CADENCE_DAYS,
                        help=f"Cadence guard window in days (default {DEFAULT_CADENCE_DAYS})")
    parser.add_argument("--skip", action="append", default=[],
                        choices=sorted(VALID_SKIP),
                        help="Skip a stage (repeatable)")
    parser.add_argument("--keep-snapshots", type=int, default=DEFAULT_SNAPSHOTS_KEPT,
                        help=f"Snapshots to retain after GC (default {DEFAULT_SNAPSHOTS_KEPT})")
    args = parser.parse_args()

    if args.check:
        due, reason = is_due(cadence_days=args.cadence_days)
        print(reason)
        return 0 if due else 1

    if not args.force:
        due, reason = is_due(cadence_days=args.cadence_days)
        if not due:
            print(f"Skipping: {reason}. Use --force to override.")
            return 0

    result = run_dream(
        skip=tuple(args.skip),
        dry_run=args.dry_run,
        keep_snapshots=args.keep_snapshots,
    )

    print(f"Started:               {result.started_at.isoformat()}")
    print(f"Completed:             {result.completed_at.isoformat() if result.completed_at else '-'}")
    print(f"Snapshot:              {result.snapshot_path or '-'}")
    if result.skipped_stages:
        print(f"Skipped stages:        {', '.join(result.skipped_stages)}")
    print(f"Files compacted:       {result.files_compacted}")
    print(f"Files skipped (compact):{result.files_skipped}")
    print(f"Bytes saved:           {result.bytes_saved}")
    print(f"Derivative entities:   {result.derivative_entities}")
    print(f"Derivative files:      {result.derivatives_written}")
    print(f"Entities decayed:      {result.entities_decayed}")
    print(f"Entities archived:     {result.entities_archived}")
    print(f"Claims archived:       {result.claims_archived}")
    print(f"Archive path:          {result.archive_path or '-'}")
    print(f"Restored from snapshot:{result.restored}")
    if result.errors:
        print("Errors:")
        for e in result.errors:
            print(f"  - {e}")
    return 1 if (result.errors and not result.skipped_stages) or result.restored else 0


if __name__ == "__main__":
    raise SystemExit(main())
