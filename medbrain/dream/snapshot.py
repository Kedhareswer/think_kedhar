"""Snapshot mutable corpus state before destructive Dream ops.

Snapshot dir: ``brain/.dream-snapshots/<utc-iso>/``

Captures the paths Dream may overwrite — currently:
  - student/concepts/  (Dream rewrites for compaction)
  - student/notes/     (Dream rewrites for compaction)
  - brain.db           (Dream updates salience and DreamRun rows)

Derivative outputs (flashcards/mnemonics/analogies/gaps) and the archive are
not snapshotted because Dream only appends to them; rollback would lose
work the user might want to keep.
"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

from medbrain import config

SNAPSHOT_ROOT_NAME = ".dream-snapshots"


def _snapshot_items() -> list[tuple[str, Path]]:
    """(snapshot-folder-name, source-path) pairs. Resolved on demand because
    config paths can be monkeypatched by tests."""
    return [
        ("concepts", config.CONCEPTS_DIR),
        ("notes",    config.NOTES_DIR),
        ("brain.db", config.DB_PATH),
    ]


def _root() -> Path:
    return config.BRAIN_DIR / SNAPSHOT_ROOT_NAME


def _ts() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def take_snapshot() -> Path:
    """Copy current mutable items into a fresh timestamped snapshot dir."""
    root = _root()
    root.mkdir(parents=True, exist_ok=True)
    dest = root / _ts()
    if dest.exists():
        i = 1
        while True:
            candidate = root / f"{dest.name}-{i}"
            if not candidate.exists():
                dest = candidate
                break
            i += 1
    dest.mkdir(parents=True)
    for name, src in _snapshot_items():
        if not src.exists():
            continue
        target = dest / name
        if src.is_dir():
            shutil.copytree(src, target)
        else:
            shutil.copy2(src, target)
    return dest


def restore(snapshot_dir: Path) -> None:
    """Restore mutable items from a snapshot dir. Overwrites existing items."""
    snapshot_dir = Path(snapshot_dir)
    if not snapshot_dir.exists():
        raise FileNotFoundError(f"snapshot not found: {snapshot_dir}")
    for name, target in _snapshot_items():
        src = snapshot_dir / name
        if not src.exists():
            # Item didn't exist at snapshot time → also remove from current state.
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        if src.is_dir():
            shutil.copytree(src, target)
        else:
            shutil.copy2(src, target)


def gc_old(*, keep: int = 3) -> list[Path]:
    """Delete all but the N newest snapshot dirs. Returns deleted paths."""
    root = _root()
    if not root.exists():
        return []
    dirs = sorted(
        (p for p in root.iterdir() if p.is_dir()),
        key=lambda p: p.name,
        reverse=True,
    )
    to_delete = dirs[keep:]
    for d in to_delete:
        shutil.rmtree(d, ignore_errors=True)
    return to_delete


def list_snapshots() -> list[Path]:
    """Newest-first list of snapshot dirs."""
    root = _root()
    if not root.exists():
        return []
    return sorted(
        (p for p in root.iterdir() if p.is_dir()),
        key=lambda p: p.name,
        reverse=True,
    )
