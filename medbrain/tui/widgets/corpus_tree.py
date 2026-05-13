"""Corpus tree — left pane.

Scans the filesystem (student/, brain/, dream/) and renders a collapsible
tree of every artefact a curator can open. Slugs are listed alphabetically
under each section. Selecting a leaf emits a `CorpusSelected` message that
the parent app uses to drive the centre and right panes.
"""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass

from textual.message import Message
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from medbrain import config


@dataclass
class CorpusEntry:
    """One openable artefact in the tree."""
    slug: str                # base name (e.g. "artemisinin-resistance")
    path: Path               # absolute path on disk
    kind: str                # "concept" | "note" | "memory" | "flashcard" | "question" | "archive"


class CorpusSelected(Message):
    def __init__(self, entry: CorpusEntry):
        self.entry = entry
        super().__init__()


class CorpusTree(Tree):
    """Tree widget showing the per-agent corpus organisation."""

    BINDINGS = []

    def __init__(self) -> None:
        super().__init__("MedBrain", id="corpus-tree")
        self.guide_depth = 2
        self.show_root = False
        self._load()

    def _add_section(self, label: str, directory: Path, kind: str) -> None:
        """Add a top-level section with a count and its file children."""
        if not directory.exists():
            count = 0
        else:
            files = sorted(directory.glob("**/*.md"))
            count = len(files)
        node = self.root.add(
            f"[b]{label.upper()}[/b]  [dim]{count}[/dim]",
            expand=True,
        )
        if not directory.exists():
            return
        for f in sorted(directory.glob("**/*.md")):
            slug = f.stem
            entry = CorpusEntry(slug=slug, path=f, kind=kind)
            child = node.add_leaf(slug, data=entry)

    def _load(self) -> None:
        """Populate the tree from the current corpus state."""
        self._add_section("Concepts",   config.CONCEPTS_DIR,   "concept")
        self._add_section("Notes",      config.NOTES_DIR,      "note")
        self._add_section("Memory",     config.MEMORY_DIR,     "memory")
        self._add_section("Flashcards", config.FLASHCARDS_DIR, "flashcard")
        self._add_section("Questions",  config.QUESTIONS_DIR,  "question")

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Emit a CorpusSelected message when a leaf is chosen."""
        data = event.node.data
        if isinstance(data, CorpusEntry):
            self.post_message(CorpusSelected(data))

    def refresh_tree(self) -> None:
        """Rescan the filesystem; useful when an agent run finishes."""
        self.root.remove_children()
        self._load()
