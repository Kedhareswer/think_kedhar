"""CLI: rebuild brain/graph/* from current SQL claims."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from medbrain.agents.graphify import run_graphify


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild knowledge graph from SQL claims")
    parser.add_argument(
        "--include-review",
        action="store_true",
        help="Include pending_review claims in the graph (debug)",
    )
    args = parser.parse_args()

    result = run_graphify(include_review=args.include_review)
    print(f"Started:           {result.started_at.isoformat()}")
    print(f"Completed:         {result.completed_at.isoformat() if result.completed_at else '-'}")
    print(f"Nodes:             {result.node_count}")
    print(f"Edges:             {result.edge_count}")
    print(f"Communities:       {result.community_count}")
    print(f"Isolated nodes:    {result.isolated_count}")
    print(f"Contradictions:    {result.contradiction_count}")
    if result.errors:
        for e in result.errors:
            print(f"  ERR: {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
