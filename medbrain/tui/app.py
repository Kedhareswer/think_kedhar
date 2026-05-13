"""MedBrainApp — Textual TUI for curators.

Three panes:
  - LEFT  (CorpusTree)  — concepts / notes / memory / flashcards / questions
  - MID   (DocViewer)   — focused .md file rendered as Markdown
  - RIGHT (Companions)  — gist / flashcards / questions / evidence for slug

Modal screens pushed via push_screen on keybinds:
  s → StudentModal     b → BrainModal
  d → DreamModal       e → ExportModal

The status bar at the bottom shows an animated braille spinner while an
agent is "running" (currently mocked — v1 dispatches print to status).
Wiring into subprocess.Popen(scripts/...) is the next milestone.
"""
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Footer, Header

from .screens import (
    BrainModal,
    DreamModal,
    ExportModal,
    RunRequest,
    StudentModal,
)
from .widgets.companions import Companions
from .widgets.corpus_tree import CorpusSelected, CorpusTree
from .widgets.thinking import StatusBar
from .widgets.viewer import DocViewer


class MedBrainApp(App):
    """Top-level Textual app for the MedBrain curator TUI."""

    CSS = """
    Screen { background: #14110e; }
    Header { background: #1f1a15; color: #ede4d3; }
    Footer { background: #1f1a15; }
    #main { height: 1fr; }
    CorpusTree {
        width: 36;
        background: #14110e;
        padding: 1 1;
        border-right: solid #3a3128;
    }
    DocViewer {
        height: 1fr;
        background: #14110e;
    }
    """

    # priority=True so the keybinds fire even when CorpusTree (which
    # consumes single letters for find-as-you-type) has focus.
    BINDINGS = [
        Binding("q",      "quit",            "quit",         show=True, priority=True),
        Binding("r",      "refresh_corpus",  "refresh",      show=True, priority=True),
        Binding("s",      "open_student",    "Student",      show=True, priority=True),
        Binding("b",      "open_brain",      "Brain",        show=True, priority=True),
        Binding("d",      "open_dream",      "Dream",        show=True, priority=True),
        Binding("e",      "open_export",     "Export",       show=True, priority=True),
    ]

    TITLE = "MedBrain · curator"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(id="main"):
            yield CorpusTree()
            yield DocViewer()
            yield Companions()
        yield StatusBar(id="status-bar")
        yield Footer()

    # ---- message handlers ----
    def on_corpus_selected(self, event: CorpusSelected) -> None:
        viewer = self.query_one(DocViewer)
        viewer.open_path(event.entry.path)
        self.query_one(Companions).show_for_slug(event.entry.slug)
        self.query_one(StatusBar).set_idle(
            f"opened {event.entry.kind}/{event.entry.slug}"
        )

    # ---- actions: open modals ----
    def action_refresh_corpus(self) -> None:
        self.query_one(CorpusTree).refresh_tree()
        self.query_one(StatusBar).set_idle("corpus tree refreshed")

    def action_open_student(self) -> None:
        self.push_screen(StudentModal(), self._after_modal)

    def action_open_brain(self) -> None:
        self.push_screen(BrainModal(), self._after_modal)

    def action_open_dream(self) -> None:
        self.push_screen(DreamModal(), self._after_modal)

    def action_open_export(self) -> None:
        self.push_screen(ExportModal(), self._after_modal)

    # ---- modal result handler ----
    def _after_modal(self, request: RunRequest | None) -> None:
        if request is None:
            self.query_one(StatusBar).set_idle()
            return
        # v1: mock the dispatch by setting the status bar to "running" with
        # the agent's description. Wiring into subprocess.Popen is next.
        descriptions = {
            "student": ("STUDENT",  f"would run scripts/student.py {request.args.get('topic', '')!r}"),
            "brain":   ("BRAIN",    "would run scripts/brain.py"),
            "dream":   ("DREAM",    "would run scripts/dream.py"),
            "export":  ("EXPORT",   f"would run scripts/export_master_sheet.py"
                                    f"{' --llm' if request.args.get('llm') == '1' else ''}"),
        }
        label, msg = descriptions.get(request.agent, ("?", "?"))
        self.query_one(StatusBar).set_running(label, msg)


def main() -> None:
    MedBrainApp().run()


if __name__ == "__main__":
    main()
