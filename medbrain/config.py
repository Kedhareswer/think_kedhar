"""Runtime configuration loaded from environment + .env."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _path(env: str, default: str) -> Path:
    return Path(os.getenv(env, default)).resolve()


BRAIN_DIR: Path = _path("BRAIN_DIR", "./brain")
DB_PATH: Path = BRAIN_DIR / "brain.db"

CONCEPTS_DIR: Path = BRAIN_DIR / "concepts"
NOTES_DIR: Path = BRAIN_DIR / "notes"
DERIVATIVE_DIR: Path = BRAIN_DIR / "derivative"
ARCHIVE_DIR: Path = BRAIN_DIR / "archive"
CHANGELOG_DIR: Path = BRAIN_DIR / "changelog"
GRAPH_DIR: Path = BRAIN_DIR / "graph"

MEMORY_FILE: Path = BRAIN_DIR / "memory.md"
QUESTIONS_FILE: Path = BRAIN_DIR / "questions.md"

LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-sonnet-4-6")

PUBMED_API_KEY: str | None = os.getenv("PUBMED_API_KEY") or None
PUBMED_EMAIL: str = os.getenv("PUBMED_EMAIL", "anonymous@medbrain.local")

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


def ensure_brain_dirs() -> None:
    """Create brain/ subdirectories if they don't exist."""
    for d in (
        BRAIN_DIR,
        CONCEPTS_DIR,
        NOTES_DIR,
        NOTES_DIR / "treatment",
        NOTES_DIR / "resistance",
        NOTES_DIR / "epidemiology",
        DERIVATIVE_DIR,
        DERIVATIVE_DIR / "flashcards",
        DERIVATIVE_DIR / "mnemonics",
        DERIVATIVE_DIR / "analogies",
        DERIVATIVE_DIR / "gaps",
        ARCHIVE_DIR,
        CHANGELOG_DIR,
        GRAPH_DIR,
    ):
        d.mkdir(parents=True, exist_ok=True)
