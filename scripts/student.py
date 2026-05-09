"""CLI: research a topic. Plans + ingests via PubMed.

Examples:
    python scripts/student.py "what is malaria"
    python scripts/student.py "artemisinin resistance in pregnancy"
    python scripts/student.py "vaginal yeast infection treatment"
    python scripts/student.py --plan-only "virology overview"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from medbrain.agents.researcher import ingest_topic
from medbrain.extractors.plan import plan_research


def main() -> int:
    parser = argparse.ArgumentParser(description="Research a topic into MedBrain")
    parser.add_argument("topic", help="Natural-language research topic")
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Print the research plan and exit; do not ingest",
    )
    parser.add_argument(
        "--no-regen",
        action="store_true",
        help="Skip concept/topic .md regeneration (debug; ingest only)",
    )
    args = parser.parse_args()

    if args.plan_only:
        plan = plan_research(args.topic)
        print(json.dumps(plan.model_dump(), indent=2, default=str))
        return 0

    result = ingest_topic(args.topic, regen=not args.no_regen)

    print(f"Topic:               {result.topic}")
    print(f"Scope:               {result.plan.scope.value}")
    if result.plan.decomposition:
        print(f"Decomposition:       {len(result.plan.decomposition)} subtopics")
        for s in result.plan.decomposition:
            print(f"   - {s}")
    print(f"Queries planned:     {len(result.plan.queries)}")
    print(f"Papers ingested:     {result.total_papers_ingested}")
    print(f"Claims extracted:    {result.total_claims_extracted}")
    print(f"Claims inserted:     {result.total_claims_inserted}")
    print(f"Duplicates skipped:  {result.total_duplicates}")
    if result.cap_hit:
        print("Stopped: hit max_total_papers cap.")
    print()
    for qr in result.query_runs:
        marker = " [SATURATED]" if qr.saturation_stop else ""
        print(
            f"  [{qr.subtopic}] {qr.pubmed_query!r}"
            f" -> found={qr.pmids_found} ingested={qr.pmids_succeeded}"
            f" failed={qr.pmids_failed}{marker}"
        )
    if result.regen is not None:
        print()
        print("Regen:")
        print(f"  concepts written:   {result.regen.entities_processed}")
        print(f"  topics written:     {result.regen.topics_processed}")
        print(f"  failures:           {result.regen.entities_failed + result.regen.topics_failed}")
        for p in result.regen.paths_written[:10]:
            print(f"    - {p}")
        if len(result.regen.paths_written) > 10:
            print(f"    ... and {len(result.regen.paths_written) - 10} more")
        for err in result.regen.errors[:5]:
            print(f"    ERR: {err}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
