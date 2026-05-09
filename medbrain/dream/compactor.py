"""Per-file Markdown compaction with citation-preservation gate.

Citation tokens in MedBrain look like `[c:<claim_id>]`. The gate rejects
any rewrite that drops, adds, or duplicates a citation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from medbrain.llm import LLMError, call
from medbrain.regen.atomic import atomic_write_text

COMPACT_PROMPT = (
    Path(__file__).resolve().parent.parent.parent / "prompts" / "dream_compact.md"
)

_CITATION_RE = re.compile(r"\[c:([^\]]+)\]")


def extract_citations(text: str) -> list[str]:
    """All citation ids in document order, with duplicates."""
    return _CITATION_RE.findall(text)


def citations_match(old: str, new: str) -> bool:
    """True if the multiset of citation ids is identical."""
    return sorted(extract_citations(old)) == sorted(extract_citations(new))


@dataclass
class CompactResult:
    path: Path
    old_size: int
    new_size: int
    citations_preserved: bool
    skipped_reason: str | None = None  # set when no write happened
    error: str | None = None


def compact_file(
    md_path: Path,
    *,
    min_size_bytes: int = 256,
    timeout: float = 180.0,
) -> CompactResult:
    """Compact one .md file. Atomic-write only if citations preserved AND new < old.

    Files smaller than min_size_bytes are skipped (compaction overhead not worth it).
    """
    md_path = Path(md_path)
    old_text = md_path.read_text(encoding="utf-8")
    old_size = len(old_text.encode("utf-8"))

    if old_size < min_size_bytes:
        return CompactResult(
            path=md_path,
            old_size=old_size,
            new_size=old_size,
            citations_preserved=True,
            skipped_reason=f"size {old_size} < min {min_size_bytes}",
        )

    if not extract_citations(old_text):
        # Nothing to verify against; refuse to compact opaque files for safety.
        return CompactResult(
            path=md_path,
            old_size=old_size,
            new_size=old_size,
            citations_preserved=True,
            skipped_reason="no [c:<id>] citations in source",
        )

    try:
        system = COMPACT_PROMPT.read_text(encoding="utf-8")
        new_text = call(system, old_text, timeout=timeout).strip() + "\n"
    except LLMError as e:
        return CompactResult(
            path=md_path,
            old_size=old_size,
            new_size=old_size,
            citations_preserved=False,
            error=str(e),
        )

    new_size = len(new_text.encode("utf-8"))

    if not citations_match(old_text, new_text):
        return CompactResult(
            path=md_path,
            old_size=old_size,
            new_size=new_size,
            citations_preserved=False,
            skipped_reason="citation set drift; rewrite rejected",
        )

    if new_size >= old_size:
        return CompactResult(
            path=md_path,
            old_size=old_size,
            new_size=new_size,
            citations_preserved=True,
            skipped_reason="rewrite not smaller; no change",
        )

    atomic_write_text(md_path, new_text)
    return CompactResult(
        path=md_path,
        old_size=old_size,
        new_size=new_size,
        citations_preserved=True,
    )


def compact_tree(roots: list[Path]) -> list[CompactResult]:
    """Walk each root for *.md and compact each. Returns one result per file processed."""
    results: list[CompactResult] = []
    for root in roots:
        if not root.exists():
            continue
        for md in sorted(root.rglob("*.md")):
            results.append(compact_file(md))
    return results
