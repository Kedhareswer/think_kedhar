"""Export medbrain corpus → exports/master_sheet.xlsx (human verification format).

Mirrors the structure of `Master sheet.xlsx`:
  Conditions · Medications · Lab tests · RadiologyImaging · Special Diagnostic
  Studies · HistopathologyCytology · SurgeriesProcedures · Provider type &
  Specialty · Hospital Addressbook.

Each sheet keeps the original column headers verbatim. Domains without
corpus data yet are written as empty sheets (headers only) so the schema is
stable for reviewers.

Usage:
    python scripts/export_master_sheet.py
    python scripts/export_master_sheet.py --out /tmp/check.xlsx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make `medbrain` importable when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from medbrain.exporters.master_sheet import SHEETS, export  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Export medbrain → Master sheet xlsx")
    parser.add_argument("--out", type=Path, default=None,
                        help="Output path (default: exports/master_sheet.xlsx)")
    parser.add_argument("--llm", action="store_true",
                        help="Use Claude to generate reference-style prose per cell. "
                             "Slow (~5-15s per concept) but produces reviewer-ready rows. "
                             "Requires the `claude` CLI on PATH.")
    args = parser.parse_args()

    written = export(args.out, llm=args.llm)
    print(f"wrote {written}")
    print(f"sheets: {len(SHEETS)}")
    for spec in SHEETS:
        marker = "  [LLM]" if (args.llm and spec.name == "Conditions") else ""
        print(f"  · {spec.name:<32} {len(spec.columns)} cols{marker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
