"""CLI: run the Brain agent once.

Recommended usage:
    python scripts/brain.py --topic "artemisinin resistance"

Writes per-topic synthesis to brain/memory/<slug>.md and a classified
question list (Answerable / Gaps) to brain/questions/<slug>.md.

Without --topic, writes to the legacy global brain/memory.md and
brain/questions.md files.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from medbrain.agents.brain import run_brain


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Brain agent (synthesis + question classifier)")
    parser.add_argument(
        "--topic",
        help="Topic name. Output files written to brain/memory/<slug>.md and brain/questions/<slug>.md.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Re-read all .md files (ignore last-run cutoff)",
    )
    args = parser.parse_args()

    result = run_brain(topic=args.topic, force_full=args.full)
    print(f"Started:           {result.started_at.isoformat()}")
    print(f"Completed:         {result.completed_at.isoformat() if result.completed_at else '-'}")
    print(f"Topic:             {result.topic or '(global)'}")
    print(f"Concepts read:     {result.concepts_read}")
    print(f"Topics read:       {result.topics_read}")
    print(f"memory:            {result.memory_path or '-'}")
    print(f"questions:         {result.questions_path or '-'}")
    if result.errors:
        print("Errors:")
        for e in result.errors:
            print(f"  - {e}")
    return 0 if not result.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
