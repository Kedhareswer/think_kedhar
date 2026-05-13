"""Launch the MedBrain curator TUI.

Usage:
    python scripts/tui.py

Read-mostly v1: browse the corpus, open per-concept companions, refresh.
Modals for Student/Brain/Dream/Export are stubs in v1 — they print intent
to the status bar. Wire-up to actual scripts/ is the next milestone.

Design spec: docs/superpowers/specs/2026-05-13-medbrain-tui-design.md
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make `medbrain` importable when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from medbrain.tui.app import main  # noqa: E402


if __name__ == "__main__":
    main()
