"""Modal screens — Student / Brain / Dream / Export.

Each modal is a ``ModalScreen`` pushed by the main app on a keybind:
  s → Student     b → Brain       d → Dream       e → Export

v1 modals are interactive but read-only side: they collect the inputs a
real run would need and then "dispatch" by emitting a ``RunRequested``
message that the app prints to the status bar. Wiring the dispatch into
``subprocess.Popen(scripts/...)`` with streamed stdout is the next milestone.
"""
from __future__ import annotations

from dataclasses import dataclass

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView, Markdown, Static

from medbrain import config


@dataclass
class RunRequest:
    """A user-confirmed agent run waiting to dispatch."""
    agent: str            # "student" | "brain" | "dream" | "export"
    args: dict[str, str]  # agent-specific arguments


class RunRequested(Message):
    """Bubbled from a modal back to the app when the user confirms a run."""
    def __init__(self, request: RunRequest):
        self.request = request
        super().__init__()


# Shared CSS for all modals — opencode-inspired, amber accent.
_MODAL_CSS = """
ModalScreen {
    align: center middle;
    background: rgba(0, 0, 0, 0.6);
}
#modal-box {
    width: 80%;
    max-width: 92;
    height: auto;
    max-height: 80%;
    background: #14110e;
    border: round #ff8c42;
    padding: 1 2;
}
#modal-title {
    color: #ff8c42;
    text-style: bold;
    padding: 0 0 1 0;
}
#modal-help {
    color: #b8a994;
    padding: 0 0 1 0;
}
#modal-input {
    margin: 0 0 1 0;
    background: #0e0c0a;
    border: solid #3a3128;
}
#modal-input:focus {
    border: solid #ff8c42;
}
.modal-section-title {
    color: #8a7d6b;
    text-style: bold;
    margin: 1 0 0 0;
}
ListView {
    background: #14110e;
    border: solid #3a3128;
    max-height: 12;
}
ListView > ListItem {
    background: #14110e;
}
ListView > ListItem.--highlight {
    background: rgba(255, 140, 66, 0.12);
}
.priority-pill {
    color: #d96852;
    text-style: bold;
    padding: 0 1;
}
.modal-footer {
    height: auto;
    align: right middle;
    padding: 1 0 0 0;
}
.modal-footer Button {
    margin: 0 0 0 1;
    min-width: 16;
}
.btn-primary {
    background: #ff8c42;
    color: #14110e;
}
.btn-primary:hover {
    background: #ffaa6e;
}
.btn-secondary {
    background: transparent;
    border: solid #3a3128;
    color: #b8a994;
}
.preview-md {
    background: #0e0c0a;
    padding: 1 2;
    border: solid #261f19;
    max-height: 16;
}
"""


def _read_open_questions(limit: int = 5) -> list[tuple[str, str]]:
    """Return up to ``limit`` (priority, text) pairs from brain/questions.md."""
    if not config.QUESTIONS_FILE.exists():
        return []
    out: list[tuple[str, str]] = []
    for line in config.QUESTIONS_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip("- *• ").strip()
        if not stripped:
            continue
        # Heuristic: a question line starts with a P1/P2/P3 marker or ends with a "?"
        low = stripped.lower()
        priority = "P?"
        for tag in ("p1", "p2", "p3"):
            if tag in low.replace(":", " ").split()[:3]:
                priority = tag.upper()
                break
        if priority != "P?" or stripped.endswith("?"):
            out.append((priority, stripped))
        if len(out) >= limit:
            break
    return out


# ============================================================
# Student modal — research a topic
# ============================================================
class StudentModal(ModalScreen[RunRequest | None]):
    """Run Student on a free-text topic or a pulled-from-backlog question."""

    BINDINGS = [
        Binding("escape", "cancel", "cancel"),
        Binding("enter",  "run",    "run"),
    ]
    DEFAULT_CSS = _MODAL_CSS

    def compose(self) -> ComposeResult:
        suggestions = _read_open_questions(limit=5)
        if suggestions:
            items = [
                ListItem(Static(
                    f"[{pri}] {(text if len(text) < 80 else text[:80] + '…')}"
                ))
                for pri, text in suggestions
            ]
        else:
            items = [ListItem(Static("[i]No open questions in backlog yet.[/i]"))]
        with Vertical(id="modal-box"):
            yield Label("Student — new research session", id="modal-title")
            yield Static(
                "Type a topic, or pick a suggested open question from "
                "brain/questions.md. The agent will plan a PubMed query set "
                "and ingest up to 30 papers, stopping at saturation.",
                id="modal-help",
            )
            yield Input(
                placeholder="e.g. artemisinin resistance in pregnancy",
                id="modal-input",
            )
            yield Label("Suggested · top open questions", classes="modal-section-title")
            yield ListView(*items, id="suggest-list")
            with Horizontal(classes="modal-footer"):
                yield Button("Cancel  Esc", id="cancel", classes="btn-secondary")
                yield Button("Run  ⏎",     id="confirm", classes="btn-primary")

    @on(Button.Pressed, "#cancel")
    def _cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#confirm")
    def _confirm(self) -> None:
        self.action_run()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_run(self) -> None:
        topic = self.query_one(Input).value.strip()
        if not topic:
            # If no input typed, use the highlighted suggestion
            lv = self.query_one(ListView)
            highlighted = lv.highlighted_child
            if highlighted:
                # Strip the [P1] prefix
                inner = highlighted.query_one(Static).renderable
                topic = str(inner).split("] ", 1)[-1] if "] " in str(inner) else str(inner)
        if topic:
            self.dismiss(RunRequest(agent="student", args={"topic": topic}))


# ============================================================
# Brain modal — confirm synthesis run
# ============================================================
class BrainModal(ModalScreen[RunRequest | None]):
    BINDINGS = [
        Binding("escape", "cancel", "cancel"),
        Binding("enter",  "run",    "run"),
    ]
    DEFAULT_CSS = _MODAL_CSS

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-box"):
            yield Label("Brain — hourly synthesis", id="modal-title")
            yield Markdown(
                "Brain reads everything in `dirty_tracker`, re-reads the "
                "changed concept and topic notes, and rewrites two files:\n\n"
                "- `brain/memory.md` — cross-concept synthesis\n"
                "- `brain/questions.md` — updated research backlog with "
                "**priority** ranking\n\n"
                "This run is **non-destructive**. Existing files are atomic-"
                "overwritten; previous content is in git.",
                classes="preview-md",
            )
            with Horizontal(classes="modal-footer"):
                yield Button("Cancel  Esc", id="cancel", classes="btn-secondary")
                yield Button("Synthesize  ⏎", id="confirm", classes="btn-primary")

    @on(Button.Pressed, "#cancel")
    def _cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#confirm")
    def _confirm(self) -> None:
        self.action_run()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_run(self) -> None:
        self.dismiss(RunRequest(agent="brain", args={}))


# ============================================================
# Dream modal — compaction preview
# ============================================================
class DreamModal(ModalScreen[RunRequest | None]):
    BINDINGS = [
        Binding("escape", "cancel", "cancel"),
        Binding("enter",  "run",    "run"),
    ]
    DEFAULT_CSS = _MODAL_CSS

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-box"):
            yield Label("Dream — weekly compaction", id="modal-title")
            yield Markdown(
                "Dream operates on a **git branch** so this is rollback-safe.\n\n"
                "| Step | Action |\n"
                "|---|---|\n"
                "| 1 | Snapshot `student/concepts/`, `notes/`, `brain.db` |\n"
                "| 2 | Rewrite every `.md` tighter (same density) |\n"
                "| 3 | Generate `student/flashcards/<slug>.md` |\n"
                "| 4 | Generate `dream/{mnemonics,analogies,gaps}/` |\n"
                "| 5 | Decay cold claims → `dream/archive/` |\n"
                "| 6 | QA gate; if pass, merge to main |\n\n"
                "Typical runtime: **5-20 minutes** depending on corpus size.",
                classes="preview-md",
            )
            with Horizontal(classes="modal-footer"):
                yield Button("Cancel  Esc", id="cancel", classes="btn-secondary")
                yield Button("Start dream  ⏎", id="confirm", classes="btn-primary")

    @on(Button.Pressed, "#cancel")
    def _cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#confirm")
    def _confirm(self) -> None:
        self.action_run()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_run(self) -> None:
        self.dismiss(RunRequest(agent="dream", args={}))


# ============================================================
# Export modal — Master sheet with LLM toggle
# ============================================================
class ExportModal(ModalScreen[RunRequest | None]):
    BINDINGS = [
        Binding("escape", "cancel", "cancel"),
        Binding("enter",  "run",    "run"),
        Binding("l",      "toggle_llm", "toggle --llm"),
    ]
    DEFAULT_CSS = _MODAL_CSS

    use_llm: bool = False

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-box"):
            yield Label("Export — Master sheet xlsx", id="modal-title")
            yield Markdown(
                "Writes `exports/master_sheet.xlsx` — mirrors `Master sheet.xlsx`"
                " column-for-column (9 sheets). One row per concept where a"
                " builder exists.\n\n"
                "| Sheet | Status |\n"
                "|---|---|\n"
                "| Conditions | ● 8 rows (LLM-ready) |\n"
                "| Medications | ● builder ready (drug concepts) |\n"
                "| Lab tests, Radiology, … | ○ schema only |\n"
                "| Providers, Hospitals | ◐ CSV import path needed |",
                classes="preview-md",
            )
            yield Static("Mode (press [b]l[/b] to toggle):", classes="modal-section-title")
            yield Static(self._mode_text(), id="mode-line")
            with Horizontal(classes="modal-footer"):
                yield Button("Cancel  Esc", id="cancel", classes="btn-secondary")
                yield Button("Export  ⏎", id="confirm", classes="btn-primary")

    def _mode_text(self) -> str:
        if self.use_llm:
            return "[b][#ff8c42]●[/] --llm[/]  reference-style prose, ~2 min for current corpus"
        return "[#b8a994]○ fast (default)[/]  section-lift, ~2 seconds"

    def action_toggle_llm(self) -> None:
        self.use_llm = not self.use_llm
        self.query_one("#mode-line", Static).update(self._mode_text())

    @on(Button.Pressed, "#cancel")
    def _cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#confirm")
    def _confirm(self) -> None:
        self.action_run()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_run(self) -> None:
        self.dismiss(RunRequest(
            agent="export",
            args={"llm": "1" if self.use_llm else "0"},
        ))
