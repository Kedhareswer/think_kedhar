"""Thinking animation — braille spinner for the status bar.

Inspired by https://github.com/czl9707/agents-are-thinking — a small Unicode
spinner cycle that signals "an agent is running" without taking real estate
or stealing focus. The widget toggles between idle (●) and running (animated
braille) states. No runtime dependencies beyond Textual.
"""
from __future__ import annotations

from textual.widgets import Static

# Braille spinner — 10-frame cycle, same family Cursor / Copilot use.
_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")


class StatusBar(Static):
    """Bottom-of-screen status bar with optional braille-thinking animation."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: #1f1a15;
        color: #b8a994;
        padding: 0 2;
    }
    """

    def __init__(self, **kwargs) -> None:
        # Construct with an initial rendered string so the first paint never
        # encounters a None visual.
        super().__init__(
            self._compose_text(running=False, label="IDLE",
                               message="press s · b · d · e to launch an agent"),
            **kwargs,
        )
        self._running = False
        self._label = "IDLE"
        self._message = "press s · b · d · e to launch an agent"
        self._frame = 0

    def on_mount(self) -> None:
        self.set_interval(0.1, self._tick)

    def _tick(self) -> None:
        if not self._running:
            return
        self._frame = (self._frame + 1) % len(_FRAMES)
        self.update(self._compose_text(
            running=True, label=self._label, message=self._message, frame=self._frame,
        ))

    @staticmethod
    def _compose_text(*, running: bool, label: str, message: str, frame: int = 0) -> str:
        if running:
            return (
                f"[#ff8c42]{_FRAMES[frame]}[/]  "
                f"[bold #ede4d3]{label}[/]  "
                f"[#8a7d6b]{message}[/]"
            )
        return (
            f"[#a7c282]●[/]  "
            f"[bold #b8a994]{label}[/]  "
            f"[#8a7d6b]{message}[/]"
        )

    # ---- public API ----
    def set_idle(self, msg: str = "press s · b · d · e to launch an agent") -> None:
        self._running = False
        self._label = "IDLE"
        self._message = msg
        self.update(self._compose_text(running=False, label="IDLE", message=msg))

    def set_running(self, label: str, msg: str) -> None:
        self._running = True
        self._label = label
        self._message = msg
        self.update(self._compose_text(
            running=True, label=label, message=msg, frame=self._frame,
        ))
