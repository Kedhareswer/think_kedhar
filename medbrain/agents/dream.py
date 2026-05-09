"""Dream agent orchestrator.

Order: snapshot → compact → derivative → decay → record.
On any unhandled exception, restore from snapshot and persist a DreamRun row
with `restored=1` and the error message.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select

from medbrain import config
from medbrain.db import session_scope
from medbrain.dream import compactor, decay, derivative, snapshot
from medbrain.models import DreamRun

DEFAULT_CADENCE_DAYS = 7
DEFAULT_SNAPSHOTS_KEPT = 3


@dataclass
class DreamResult:
    started_at: datetime
    completed_at: datetime | None = None
    snapshot_path: str | None = None
    files_compacted: int = 0
    files_skipped: int = 0
    bytes_saved: int = 0
    derivatives_written: int = 0
    derivative_entities: int = 0
    entities_decayed: int = 0
    entities_archived: int = 0
    claims_archived: int = 0
    archive_path: str | None = None
    restored: bool = False
    errors: list[str] = field(default_factory=list)
    skipped_stages: list[str] = field(default_factory=list)


def _last_completed() -> datetime | None:
    with session_scope() as sess:
        return sess.execute(
            select(DreamRun.completed_at)
            .where(DreamRun.completed_at.is_not(None))
            .where(DreamRun.restored == 0)
            .order_by(DreamRun.completed_at.desc())
            .limit(1)
        ).scalar_one_or_none()


def is_due(*, cadence_days: int = DEFAULT_CADENCE_DAYS, now: datetime | None = None) -> tuple[bool, str]:
    """Returns (due, reason). Used by `dream.py --check`."""
    now = now or datetime.now(UTC)
    last = _last_completed()
    if last is None:
        return True, "no successful Dream run on record"
    # SQLite returns naive datetimes; treat as UTC.
    if last.tzinfo is None:
        last = last.replace(tzinfo=UTC)
    elapsed = now - last
    if elapsed >= timedelta(days=cadence_days):
        return True, f"last run {elapsed.days}d ago (cadence {cadence_days}d)"
    return False, f"last run {elapsed.days}d ago, next due in {cadence_days - elapsed.days}d"


def _record(result: DreamResult) -> None:
    with session_scope() as sess:
        sess.add(
            DreamRun(
                started_at=result.started_at,
                completed_at=result.completed_at,
                files_compacted=result.files_compacted,
                files_skipped=result.files_skipped,
                derivatives_written=result.derivatives_written,
                entities_decayed=result.entities_decayed,
                entities_archived=result.entities_archived,
                snapshot_path=result.snapshot_path,
                restored=1 if result.restored else 0,
                error="; ".join(result.errors)[:1000] if result.errors else None,
            )
        )


def run_dream(
    *,
    skip: tuple[str, ...] = (),
    dry_run: bool = False,
    keep_snapshots: int = DEFAULT_SNAPSHOTS_KEPT,
) -> DreamResult:
    """One Dream pass.

    skip: names of stages to bypass — any of {"compact", "derivative", "decay"}.
    dry_run: prints intent (caller responsibility) — agent itself does NOT mutate
             when True; compaction/derivative/decay are all no-ops.
    """
    started = datetime.now(UTC)
    result = DreamResult(started_at=started)

    skip_set = set(skip)
    if dry_run:
        # Surface what WOULD run, then bail before snapshot.
        for stage in ("compact", "derivative", "decay"):
            if stage in skip_set:
                result.skipped_stages.append(stage)
        result.completed_at = datetime.now(UTC)
        result.errors.append("dry-run: no mutations attempted")
        # Do not record DreamRun — dry-run is informational.
        return result

    # 1) snapshot
    try:
        snap = snapshot.take_snapshot()
        result.snapshot_path = str(snap)
    except Exception as e:
        result.errors.append(f"snapshot: {e}")
        result.completed_at = datetime.now(UTC)
        _record(result)
        return result

    try:
        # 2) compact
        if "compact" in skip_set:
            result.skipped_stages.append("compact")
        else:
            roots = [config.CONCEPTS_DIR, config.NOTES_DIR]
            compact_results = compactor.compact_tree(roots)
            for r in compact_results:
                if r.error:
                    result.errors.append(f"compact {r.path.name}: {r.error}")
                    continue
                if r.skipped_reason:
                    result.files_skipped += 1
                    continue
                if r.new_size < r.old_size:
                    result.files_compacted += 1
                    result.bytes_saved += r.old_size - r.new_size

        # 3) derivative
        if "derivative" in skip_set:
            result.skipped_stages.append("derivative")
        else:
            entities = derivative.entities_with_concept_notes()
            for entity in entities:
                d = derivative.generate_for_entity(entity)
                if d.written:
                    result.derivatives_written += len(d.written)
                    result.derivative_entities += 1
                for dtype, err in d.errors.items():
                    result.errors.append(f"derivative[{entity}/{dtype}]: {err}")

        # 4) decay
        if "decay" in skip_set:
            result.skipped_stages.append("decay")
        else:
            decay_result = decay.run_decay()
            result.entities_decayed = decay_result.entities_decayed
            result.entities_archived = decay_result.entities_archived
            result.claims_archived = decay_result.claims_archived
            result.archive_path = decay_result.archive_path

    except Exception as e:
        # Hard failure → restore from snapshot
        result.errors.append(f"unhandled: {e}")
        try:
            snapshot.restore(Path(result.snapshot_path))
            result.restored = True
        except Exception as restore_err:
            result.errors.append(f"restore failed: {restore_err}")
        result.completed_at = datetime.now(UTC)
        _record(result)
        return result

    # 5) GC old snapshots (best-effort, non-fatal)
    try:
        snapshot.gc_old(keep=keep_snapshots)
    except Exception as e:
        result.errors.append(f"snapshot gc: {e}")

    result.completed_at = datetime.now(UTC)
    _record(result)
    return result
