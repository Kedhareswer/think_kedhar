"""CLI: regenerate concepts/*.md and notes/*.md for all dirty entries.

Useful after a crash, or as a standalone catch-up step. Normally regen runs
automatically at the tail of `python scripts/student.py "<topic>"`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from medbrain.regen.coordinator import regenerate_dirty


def main() -> int:
    result = regenerate_dirty()
    print(f"concepts written:  {result.entities_processed}")
    print(f"topics written:    {result.topics_processed}")
    print(f"failures:          {result.entities_failed + result.topics_failed}")
    for p in result.paths_written:
        print(f"  - {p}")
    for err in result.errors:
        print(f"  ERR: {err}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
