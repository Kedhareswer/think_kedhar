"""Markdown viewer — centre pane.

Renders the currently-focused .md file with Textual's MarkdownViewer.
Handles the empty state (no selection) and missing-file state gracefully.
"""
from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Markdown, Static


class DocViewer(VerticalScroll):
    """Scrollable markdown viewer with a header strip showing the open path."""

    DEFAULT_CSS = """
    DocViewer {
        height: 1fr;
        padding: 0 1;
    }
    DocViewer #doc-header {
        height: 1;
        color: $text-muted;
        text-style: italic;
        padding: 0 1;
    }
    DocViewer Markdown {
        height: auto;
        padding: 1 1 2 1;
    }
    """

    def __init__(self) -> None:
        super().__init__(id="doc-viewer")
        self._current_path: Path | None = None

    def compose(self) -> ComposeResult:
        yield Static("Select a concept on the left to open it.", id="doc-header")
        yield Markdown("# MedBrain\n\nWaiting for selection…", id="doc-body")

    def open_path(self, path: Path) -> None:
        """Render the file at ``path``. Errors render as a small inline note."""
        header = self.query_one("#doc-header", Static)
        body = self.query_one("#doc-body", Markdown)
        self._current_path = path

        # Display path relative to the workspace root for compactness.
        try:
            from medbrain.config import ROOT_DIR
            rel = path.relative_to(ROOT_DIR)
            header.update(f"📄 {rel}")
        except (ValueError, ImportError):
            header.update(f"📄 {path}")

        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            body.update(f"# Cannot open\n\n`{path}` — {e}")
            return
        body.update(text)
