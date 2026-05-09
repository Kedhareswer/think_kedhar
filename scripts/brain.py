"""CLI: run the Brain agent once.

By default reads only files modified since last successful Brain run.
Pass --full to ignore the cutoff and re-read everything.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from medbrain.agents.brain import run_brain


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Brain agent (synthesis + questions)")
    parser.add_argument("--full", action="store_true", help="Re-read all .md files (ignore last-run cutoff)")
    args = parser.parse_args()

    result = run_brain(force_full=args.full)
    print(f"Started:           {result.started_at.isoformat()}")
    print(f"Completed:         {result.completed_at.isoformat() if result.completed_at else '-'}")
    print(f"Concepts read:     {result.concepts_read}")
    print(f"Topics read:       {result.topics_read}")
    print(f"Questions added:   {result.questions_added}")
    print(f"Questions updated: {result.questions_updated}")
    print(f"Questions resolved:{result.questions_resolved}")
    print(f"memory.md:         {result.memory_path or '-'}")
    print(f"questions.md:      {result.questions_path or '-'}")
    if result.errors:
        print("Errors:")
        for e in result.errors:
            print(f"  - {e}")
    return 0 if not result.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
