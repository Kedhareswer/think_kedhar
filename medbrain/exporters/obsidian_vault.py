"""Publish brain + dream artifacts into the student/ Obsidian vault.

The runtime layout separates writer ownership:
  - student/concepts, notes, memory, flashcards  ← Student/Brain/Dream write directly
  - brain/memory.md, questions.md, graph/         ← Brain-owned, OUTSIDE the vault
  - dream/mnemonics, analogies, gaps              ← Dream-owned, OUTSIDE the vault

Obsidian opens `student/` as the vault root. This exporter mirrors the
brain-owned and dream-owned artifacts into `student/_brain/` and
`student/_dream/` so a single Obsidian window shows everything the human
needs to read. The underscore prefix sorts these folders to the bottom of
the file explorer and signals "agent-published, do not hand-edit here".

Idempotent. Atomic per-file writes. Safe to call from any loop checkpoint.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from medbrain import config
from medbrain.regen.atomic import atomic_write_text

VAULT_BRAIN_DIRNAME = "_brain"
VAULT_DREAM_DIRNAME = "_dream"


@dataclass
class VaultExportResult:
    files_written: list[str] = field(default_factory=list)
    files_skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.files_written) + len(self.files_skipped)


def _publish_file(src: Path, dst: Path, result: VaultExportResult) -> None:
    if not src.exists():
        result.files_skipped.append(f"{src} (source missing)")
        return
    try:
        content = src.read_text(encoding="utf-8")
        atomic_write_text(dst, content)
        result.files_written.append(str(dst))
    except (OSError, UnicodeDecodeError) as exc:
        result.errors.append(f"{src} → {dst}: {exc}")


def _publish_binary(src: Path, dst: Path, result: VaultExportResult) -> None:
    if not src.exists():
        result.files_skipped.append(f"{src} (source missing)")
        return
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        result.files_written.append(str(dst))
    except OSError as exc:
        result.errors.append(f"{src} → {dst}: {exc}")


def _publish_glob(src_dir: Path, dst_dir: Path, pattern: str, result: VaultExportResult) -> None:
    if not src_dir.exists():
        return
    for src in src_dir.glob(pattern):
        if src.is_file():
            rel = src.relative_to(src_dir)
            _publish_file(src, dst_dir / rel, result)


def publish_to_vault(vault_root: Path | None = None) -> VaultExportResult:
    """Mirror brain + dream artifacts into the student/ Obsidian vault.

    Args:
        vault_root: where to publish. Defaults to ``config.STUDENT_DIR``.

    Returns:
        VaultExportResult with per-file outcomes.

    Items published (atomic per file):
      brain/memory.md          → <vault>/_brain/memory.md
      brain/questions.md       → <vault>/_brain/questions.md
      brain/questions/*.md     → <vault>/_brain/questions/*.md
      brain/graph/graph.html   → <vault>/_brain/graph/graph.html
      brain/graph/*.json       → <vault>/_brain/graph/*.json
      dream/mnemonics/*.md     → <vault>/_dream/mnemonics/*.md
      dream/analogies/*.md     → <vault>/_dream/analogies/*.md
      dream/gaps/*.md          → <vault>/_dream/gaps/*.md
    """
    vault_root = (vault_root or config.STUDENT_DIR).resolve()
    brain_root = vault_root / VAULT_BRAIN_DIRNAME
    dream_root = vault_root / VAULT_DREAM_DIRNAME
    result = VaultExportResult()

    # Brain artifacts
    _publish_file(config.MEMORY_FILE, brain_root / "memory.md", result)
    _publish_file(config.QUESTIONS_FILE, brain_root / "questions.md", result)
    _publish_glob(config.QUESTIONS_DIR, brain_root / "questions", "*.md", result)
    _publish_binary(config.GRAPH_DIR / "graph.html", brain_root / "graph" / "graph.html", result)
    for name in ("graph.json", "communities.json", "audit.json", "version.json"):
        _publish_file(config.GRAPH_DIR / name, brain_root / "graph" / name, result)

    # Dream artifacts (skip archive — keep ARCHIVE_DIR outside the vault, it's cold storage)
    for sub in ("mnemonics", "analogies", "gaps"):
        src_dir = config.DREAM_DIR / sub
        _publish_glob(src_dir, dream_root / sub, "*.md", result)

    return result


def write_vault_index(vault_root: Path | None = None) -> Path:
    """Write a top-level _index.md inside the vault that lists key entry points.

    Obsidian shows the index on vault open if configured. Lightweight — just
    wikilinks into the main artifact folders.
    """
    vault_root = (vault_root or config.STUDENT_DIR).resolve()
    index = vault_root / "_index.md"
    content = (
        "---\n"
        "type: index\n"
        "tags: [vault/index]\n"
        "---\n\n"
        "# MedBrain Vault\n\n"
        "Auto-published by `medbrain.exporters.obsidian_vault`. Open the links "
        "below or use the graph view to explore.\n\n"
        "## Entry points\n\n"
        "- [[_brain/memory|Cross-concept synthesis (memory)]]\n"
        "- [[_brain/questions|Research backlog (questions)]]\n"
        "- [Knowledge graph](_brain/graph/graph.html)\n\n"
        "## Folders\n\n"
        "- `concepts/` — per-entity concept notes (Student/Brain output)\n"
        "- `notes/` — per-topic synthesis (Student output)\n"
        "- `memory/` — per-entity longitudinal memory (Brain output)\n"
        "- `flashcards/` — spaced-repetition cards (Dream output)\n"
        "- `_brain/` — global memory, questions, graph (auto-published)\n"
        "- `_dream/` — mnemonics, analogies, gaps (auto-published)\n"
    )
    atomic_write_text(index, content)
    return index
