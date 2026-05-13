"""CLI: publish brain + dream artifacts into the student/ Obsidian vault.

Run after each ingest / Brain run / Dream run, OR let the orchestrator
trigger it automatically. Idempotent.

Usage:
    python scripts/export_vault.py
    python scripts/export_vault.py --vault /custom/path
    python scripts/export_vault.py --no-index   # skip writing _index.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from medbrain.exporters.obsidian_vault import publish_to_vault, write_vault_index


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish brain + dream artifacts into the Obsidian vault")
    parser.add_argument("--vault", type=Path, help="Vault root (default: student/)")
    parser.add_argument("--no-index", action="store_true", help="Skip writing _index.md")
    args = parser.parse_args()

    res = publish_to_vault(vault_root=args.vault)
    print(f"Published:  {len(res.files_written)} files")
    print(f"Skipped:    {len(res.files_skipped)} (sources missing — normal on cold start)")
    if res.errors:
        print(f"Errors:     {len(res.errors)}")
        for e in res.errors[:5]:
            print(f"  - {e}")

    if not args.no_index:
        idx = write_vault_index(vault_root=args.vault)
        print(f"Index:      {idx}")
    return 0 if not res.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
