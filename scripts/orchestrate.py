"""CLI: end-to-end agentic loop driver.

One command runs the whole system on a topic until the backlog converges
or a budget cap is hit. Each iteration: plan → execute → store →
reflect → update → (dream if due) → publish vault.

Usage:
    python scripts/orchestrate.py "malaria"
    python scripts/orchestrate.py "malaria" --max-iterations 10 --max-papers 500
    python scripts/orchestrate.py "dengue diagnostics" --max-minutes 60
    python scripts/orchestrate.py "X" --no-vault    # skip Obsidian publish
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from medbrain.agents.orchestrator import OrchestratorResult, run_loop


def _print_summary(result: OrchestratorResult) -> None:
    print("\n" + "=" * 60)
    print("ORCHESTRATOR SUMMARY")
    print("=" * 60)
    print(f"Topic:                  {result.topic}")
    print(f"Started:                {result.started_at.isoformat()}")
    print(f"Completed:              {result.completed_at.isoformat() if result.completed_at else '-'}")
    print(f"Iterations run:         {len(result.iterations)}")
    print(f"Successful iterations:  {result.successful_iterations}")
    print(f"Total papers ingested:  {result.total_papers_ingested}")
    print(f"Total claims inserted:  {result.total_claims_inserted}")
    print(f"Stop reason:            {result.stop_reason}")
    print()
    for it in result.iterations:
        line = f"  it={it.iteration:2d} kind={it.kind:14s}"
        if it.research is not None:
            line += f" papers={it.research.total_papers_ingested:3d} claims={it.research.total_claims_inserted:3d}"
        elif it.active is not None:
            if it.active.picked:
                line += f" picked={it.active.picked.qid}"
            if it.active.research is not None:
                line += (
                    f" papers={it.active.research.total_papers_ingested:3d} "
                    f"claims={it.active.research.total_claims_inserted:3d}"
                )
        if it.brain is not None:
            line += f" brain_concepts={it.brain.concepts_read} brain_topics={it.brain.topics_read}"
        if it.vault is not None:
            line += f" vault={len(it.vault.files_written)}"
        if it.dream is not None:
            line += f" dream_compacted={it.dream.files_compacted}"
        if it.errors:
            line += f" ERRORS={len(it.errors)}"
        print(line)
        for e in it.errors[:3]:
            print(f"      - {e}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="End-to-end MedBrain agentic loop driver",
    )
    parser.add_argument("topic", help='Free-text research topic, e.g. "malaria"')
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=5,
        help="Hard cap on the number of passes (default: 5)",
    )
    parser.add_argument(
        "--max-papers",
        type=int,
        default=300,
        help="Cumulative ingest budget across all passes (default: 300)",
    )
    parser.add_argument(
        "--max-minutes",
        type=float,
        default=360.0,
        help="Wall-clock budget in minutes (default: 360)",
    )
    parser.add_argument(
        "--dream-cadence-days",
        type=int,
        default=7,
        help="Dream runs only if last successful run is older than this (default: 7)",
    )
    parser.add_argument(
        "--no-vault",
        action="store_true",
        help="Skip publishing artifacts to the Obsidian vault",
    )
    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Skip writing student/_index.md",
    )
    args = parser.parse_args()

    result = run_loop(
        args.topic,
        max_iterations=args.max_iterations,
        max_papers_total=args.max_papers,
        max_minutes=args.max_minutes,
        dream_cadence_days=args.dream_cadence_days,
        publish_vault=not args.no_vault,
        write_index=not args.no_index,
    )
    _print_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
