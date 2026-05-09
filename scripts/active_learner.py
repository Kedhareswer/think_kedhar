"""CLI: run the active learning loop.

Picks the highest-priority oldest open question from brain/questions.md,
flips it to in_progress, then ingests its body via the existing Researcher
pipeline. Brain agent (next run) judges resolution.

Usage:
    python scripts/active_learner.py                # one question
    python scripts/active_learner.py --max 3        # up to 3 questions
    python scripts/active_learner.py --dry-run      # show pick, do nothing
    python scripts/active_learner.py --no-regen     # skip post-ingest regen
    python scripts/active_learner.py --check        # exit 0 if open Q exists
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from medbrain import config
from medbrain.agents.active_learner import (
    ActiveLearnerResult,
    pick_next,
    run_batch,
    run_once,
)
from medbrain.agents.questions_io import load as load_questions


def _print_result(r: ActiveLearnerResult, idx: int) -> None:
    print(f"--- Pass {idx} ---")
    print(f"Started:    {r.started_at.isoformat()}")
    print(f"Completed:  {r.completed_at.isoformat() if r.completed_at else '-'}")
    if r.no_open_questions:
        print("No open questions in questions.md. Nothing to do.")
        return
    if r.picked is None:
        print("(no question picked)")
    else:
        p = r.picked
        print(f"Picked:     {p.qid}  priority={p.priority}  topic={p.topic}")
        print(f"Body:       {p.body[:200]}{'...' if len(p.body) > 200 else ''}")
    if r.research is not None:
        rr = r.research
        print(f"Plan queries:        {len(rr.plan.queries)}")
        print(f"Papers ingested:     {rr.total_papers_ingested}")
        print(f"Claims extracted:    {rr.total_claims_extracted}")
        print(f"Claims inserted:     {rr.total_claims_inserted}")
        print(f"Duplicates skipped:  {rr.total_duplicates}")
        print(f"Cap hit:             {rr.cap_hit}")
        if rr.regen:
            print(
                f"Regen:               entities={rr.regen.entities_processed}, "
                f"topics={rr.regen.topics_processed}"
            )
    if r.errors:
        print("Errors:")
        for e in r.errors:
            print(f"  - {e}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Active learning loop: pick top open question and ingest it")
    parser.add_argument("--max", type=int, default=1,
                        help="Max questions to research this run (default 1)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show which question would be picked, do not flip status or ingest")
    parser.add_argument("--no-regen", action="store_true",
                        help="Skip concept/note regen after ingest")
    parser.add_argument("--check", action="store_true",
                        help="Exit 0 + print top open question; exit 1 if none")
    args = parser.parse_args()

    if args.check:
        qfile = load_questions(config.QUESTIONS_FILE)
        pick = pick_next(qfile)
        if pick is None:
            print("No open questions.")
            return 1
        print(f"Next: {pick.qid}  priority={pick.priority}  {pick.topic}")
        print(pick.body)
        return 0

    if args.dry_run or args.max == 1:
        result = run_once(dry_run=args.dry_run, regen=not args.no_regen)
        _print_result(result, 1)
        return 0 if not result.errors else 1

    results = run_batch(max_questions=args.max, regen=not args.no_regen)
    for i, r in enumerate(results, 1):
        _print_result(r, i)
    any_errors = any(r.errors for r in results)
    return 1 if any_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
