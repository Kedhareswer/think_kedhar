"""Companions pane — right side.

For the currently-focused concept slug, shows the three sibling files that
make up the learner-centric view (memory gist, flashcards) plus the open
research questions naming this entity and a count of evidence claims.

The four sub-panes render Markdown properly (tables, bold, headers) via
Textual's Markdown widget. That fixes the rendering of `**Scope:**` /
pipe-tables / heading hierarchy that previously came through as raw text.
"""
from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Label, Markdown, Static

from medbrain import config


def _read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return ""


class _Section(VerticalScroll):
    """One titled, markdown-rendered section. Renders empty state gracefully."""

    DEFAULT_CSS = """
    _Section {
        height: auto;
        max-height: 30;
        margin: 0 0 1 0;
        padding: 0;
    }
    _Section > Label.title {
        color: #8a7d6b;
        text-style: bold;
        padding: 0 1;
        margin: 1 0 0 0;
    }
    _Section > Markdown {
        height: auto;
        max-height: 26;
        padding: 0 1;
        background: #14110e;
    }
    _Section > Markdown.empty {
        color: #564a3e;
        text-style: italic;
    }
    """

    def __init__(self, title: str, empty_msg: str) -> None:
        super().__init__()
        self._title = title
        self._empty_msg = empty_msg

    def compose(self) -> ComposeResult:
        yield Label(self._title, classes="title")
        md = Markdown(f"*{self._empty_msg}*")
        md.add_class("empty")
        yield md

    def set_markdown(self, text: str | None) -> None:
        md = self.query_one(Markdown)
        if not text or not text.strip():
            md.update(f"*{self._empty_msg}*")
            md.add_class("empty")
        else:
            md.update(text)
            md.remove_class("empty")


class Companions(VerticalScroll):
    """Right pane — gist / flashcards / questions / evidence for selected slug."""

    DEFAULT_CSS = """
    Companions {
        width: 42;
        padding: 0 0;
        background: #14110e;
        border-left: solid #3a3128;
    }
    """

    def __init__(self) -> None:
        super().__init__(id="companions")
        self._current_slug: str | None = None

    def compose(self) -> ComposeResult:
        yield _Section(
            "THE GIST · brain memory",
            "No brain-memory written for this concept yet.",
        )
        yield _Section(
            "FLASHCARDS · dream",
            "No flashcards yet — Dream generates these on its weekly pass.",
        )
        yield _Section(
            "OPEN QUESTIONS · brain questions",
            "No open questions registered for this concept.",
        )
        yield _Section(
            "EVIDENCE · SQL count",
            "No claims found mentioning this concept.",
        )

    def show_for_slug(self, slug: str) -> None:
        self._current_slug = slug
        sections = list(self.query(_Section))
        sections[0].set_markdown(self._gist_md(slug))
        sections[1].set_markdown(self._flashcards_md(slug))
        sections[2].set_markdown(self._questions_md(slug))
        sections[3].set_markdown(self._evidence_md(slug))

    # ---- per-section markdown producers ----
    def _gist_md(self, slug: str) -> str:
        text = _read_text(config.MEMORY_DIR / f"{slug}.md").strip()
        if not text:
            return ""
        # Strip the H1 if present — the section label already names it
        lines = text.splitlines()
        if lines and lines[0].startswith("# "):
            lines = lines[1:]
        return "\n".join(lines).strip()

    def _flashcards_md(self, slug: str) -> str:
        text = _read_text(config.FLASHCARDS_DIR / f"{slug}.md").strip()
        if not text:
            return ""
        # Show first 2 cards; rest as a count
        chunks = text.split("\n## ")
        if len(chunks) <= 3:
            return text
        preview = chunks[0] + "\n## " + "\n## ".join(chunks[1:3])
        return preview + f"\n\n*… and {len(chunks) - 3} more card(s)*"

    def _questions_md(self, slug: str) -> str:
        per_topic = _read_text(config.QUESTIONS_DIR / f"{slug}.md").strip()
        if per_topic:
            return per_topic
        global_text = _read_text(config.QUESTIONS_FILE)
        if not global_text:
            return ""
        needle = slug.replace("-", " ").lower()
        lines = [ln for ln in global_text.splitlines() if needle in ln.lower()]
        return "\n".join(lines[:10]) if lines else ""

    def _evidence_md(self, slug: str) -> str:
        try:
            from sqlalchemy import or_, select
            from medbrain.db import session_scope
            from medbrain.models import Claim
            from medbrain.enums import ClaimStatus
            needle = slug.replace("-", " ")
            counts: dict[str, int] = {}
            with session_scope() as sess:
                rows = sess.execute(
                    select(Claim.evidence_grade).where(
                        or_(
                            Claim.subject_text.ilike(f"%{needle}%"),
                            Claim.object_text.ilike(f"%{needle}%"),
                        ),
                        Claim.status != ClaimStatus.REJECTED,
                    )
                ).scalars().all()
                for g in rows:
                    counts[g.value] = counts.get(g.value, 0) + 1
            if not counts:
                return ""
            total = sum(counts.values())
            lines = [f"**{total} claims** in current corpus", "", "| Grade | Count |", "|---|---|"]
            for grade, n in sorted(counts.items(), key=lambda kv: -kv[1]):
                lines.append(f"| {grade} | {n} |")
            return "\n".join(lines)
        except Exception as e:
            return f"*Evidence count unavailable ({type(e).__name__})*"
