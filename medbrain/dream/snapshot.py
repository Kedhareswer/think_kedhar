"""Snapshot brain/ subtrees before destructive Dream ops.

Snapshot dir: brain/.dream-snapshots/<utc-iso>/
Captures: concepts/, notes/, derivative/, archive/, brain.db
Excludes: nested .dream-snapshots/ (would recurse), graph/ (rebuilt by graphify),
          memory.md/questions.md (Brain owns those), changelog/ (append-only).
"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

from medbrain import config

SNAPSHOT_ROOT_NAME = ".dream-snapshots"

# Items inside BRAIN_DIR copied into snapshot. Anything missing is silently skipped.
_SNAPSHOT_ITEMS: tuple[str, ...] = (
    "concepts",
    "notes",
    "derivative",
    "archive",
    "brain.db",
)


def _root() -> Path:
    return config.BRAIN_DIR / SNAPSHOT_ROOT_NAME


def _ts() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def take_snapshot() -> Path:
    """Copy current brain/ items into a fresh timestamped snapshot dir. Returns the dir."""
    root = _root()
    root.mkdir(parents=True, exist_ok=True)
    dest = root / _ts()
    if dest.exists():
        # Sub-second collision unlikely but possible; append suffix.
        i = 1
        while True:
            candidate = root / f"{dest.name}-{i}"
            if not candidate.exists():
                dest = candidate
                break
            i += 1
    dest.mkdir(parents=True)
    for name in _SNAPSHOT_ITEMS:
        src = config.BRAIN_DIR / name
        if not src.exists():
            continue
        target = dest / name
        if src.is_dir():
            shutil.copytree(src, target)
        else:
            shutil.copy2(src, target)
    return dest


def restore(snapshot_dir: Path) -> None:
    """Restore brain/ items from a snapshot dir. Overwrites existing items."""
    snapshot_dir = Path(snapshot_dir)
    if not snapshot_dir.exists():
        raise FileNotFoundError(f"snapshot not found: {snapshot_dir}")
    for name in _SNAPSHOT_ITEMS:
        src = snapshot_dir / name
        target = config.BRAIN_DIR / name
        if not src.exists():
            # Item didn't exist at snapshot time → also remove from current state.
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            continue
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
