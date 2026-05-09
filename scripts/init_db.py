"""Initialize MedBrain database. Idempotent: safe to re-run.

Creates brain/ directory tree per spec §6 and the SQL schema per spec §10.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from medbrain.config import BRAIN_DIR, DB_PATH
from medbrain.db import init_schema


def main() -> None:
    init_schema()
    print(f"brain dir:   {BRAIN_DIR}")
    print(f"database:    {DB_PATH}")
    print("schema:      created (idempotent)")


if __name__ == "__main__":
    main()
