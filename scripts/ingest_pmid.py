"""CLI: ingest one PubMed PMID directly. Bypasses the topic planner.

Mainly for debugging the per-paper pipeline. Production use goes through
`scripts/student.py "<topic>"`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from medbrain.agents.student import ingest_pmid


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest one PMID directly (debug)")
    parser.add_argument("pmid", help="PubMed ID, e.g. 33579778")
    args = parser.parse_args()

    result = ingest_pmid(args.pmid)
    print(f"PMID {result.pmid}")
    print(f"  source_id:         {result.source_id}")
    print(f"  extracted:         {result.extracted}")
    print(f"  inserted:          {result.inserted}")
    print(f"  duplicates:        {result.duplicates}")
    print(f"  auto_promoted:     {result.auto_promoted}")
    print(f"  pending_review:    {result.pending_review}")
    print(f"  contradictions:    {result.contradictions_flagged}")
    print(f"  dirty entities:    {len(result.dirty_entities)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
