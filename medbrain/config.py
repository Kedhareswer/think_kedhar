"""Runtime configuration loaded from environment + .env.

Layout (learner-centric):

  student/        what a learner sees per concept
    concepts/     (Student writes)
    notes/        (Student writes)
    memory/       (Brain writes — per-concept synthesis)
    flashcards/   (Dream writes — per-concept spaced-repetition cards)

  brain/          Brain's working area + global outputs
    brain.db      SQL source of truth
    memory.md     global cross-concept synthesis
    questions/    per-concept research backlog
    questions.md  global research backlog
    graph/        Graphify outputs

  dream/          Dream's other derivatives (firewalled)
    mnemonics/  analogies/  gaps/
    archive/      decayed claims (never deleted)

  exports/        Master sheet xlsx for human verification
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _path(env: str, default: str) -> Path:
    return Path(os.getenv(env, default)).resolve()


ROOT_DIR: Path = _path("MEDBRAIN_ROOT", ".")

STUDENT_DIR: Path = _path("STUDENT_DIR", str(ROOT_DIR / "student"))
BRAIN_DIR: Path = _path("BRAIN_DIR", str(ROOT_DIR / "brain"))
DREAM_DIR: Path = _path("DREAM_DIR", str(ROOT_DIR / "dream"))
EXPORTS_DIR: Path = _path("EXPORTS_DIR", str(ROOT_DIR / "exports"))

# Student-owned (learner view, one slug per file across all four subdirs)
CONCEPTS_DIR: Path = STUDENT_DIR / "concepts"
NOTES_DIR: Path = STUDENT_DIR / "notes"
MEMORY_DIR: Path = STUDENT_DIR / "memory"
FLASHCARDS_DIR: Path = STUDENT_DIR / "flashcards"

# Brain-owned
DB_PATH: Path = BRAIN_DIR / "brain.db"
MEMORY_FILE: Path = BRAIN_DIR / "memory.md"
QUESTIONS_FILE: Path = BRAIN_DIR / "questions.md"
QUESTIONS_DIR: Path = BRAIN_DIR / "questions"
GRAPH_DIR: Path = BRAIN_DIR / "graph"

# Dream-owned
MNEMONICS_DIR: Path = DREAM_DIR / "mnemonics"
ANALOGIES_DIR: Path = DREAM_DIR / "analogies"
GAPS_DIR: Path = DREAM_DIR / "gaps"
ARCHIVE_DIR: Path = DREAM_DIR / "archive"

# Master sheet output
MASTER_SHEET: Path = EXPORTS_DIR / "master_sheet.xlsx"

# Back-compat alias (Dream derivative subroots — kept so old callers don't break)
DERIVATIVE_DIRS: dict[str, Path] = {
    "flashcards": FLASHCARDS_DIR,
    "mnemonics": MNEMONICS_DIR,
    "analogies": ANALOGIES_DIR,
    "gaps": GAPS_DIR,
}

LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-sonnet-4-6")

PUBMED_API_KEY: str | None = os.getenv("PUBMED_API_KEY") or None
PUBMED_EMAIL: str = os.getenv("PUBMED_EMAIL", "anonymous@medbrain.local")

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


def ensure_brain_dirs() -> None:
    """Create runtime subdirectories if they don't exist.

    Name preserved for back-compat; covers all three agent roots + exports.
    """
    for d in (
        STUDENT_DIR, BRAIN_DIR, DREAM_DIR, EXPORTS_DIR,
        # student-owned
        CONCEPTS_DIR, NOTES_DIR, MEMORY_DIR, FLASHCARDS_DIR,
        NOTES_DIR / "treatment",
        NOTES_DIR / "resistance",
        NOTES_DIR / "epidemiology",
        # brain-owned
        QUESTIONS_DIR, GRAPH_DIR,
        # dream-owned
        MNEMONICS_DIR, ANALOGIES_DIR, GAPS_DIR, ARCHIVE_DIR,
    ):
        d.mkdir(parents=True, exist_ok=True)
