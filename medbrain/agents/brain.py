"""Brain agent: read changed concepts/notes, regenerate memory and questions.

Two output modes:
  - **Topic-scoped (preferred):** pass `topic="..."`. Writes
    `student/memory/<slug>.md` (per-concept gist for the learner view) and
    `brain/questions/<slug>.md` (Brain's per-concept research backlog).
    Use this after each Student run so each topic has its own synthesis.
  - **Global (legacy):** no topic. Writes the single `brain/memory.md` +
    `brain/questions.md` files. Kept for back-compat with older callers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

from medbrain import config
from medbrain.db import session_scope
from medbrain.llm import LLMError, call
from medbrain.models import BrainRun
from medbrain.regen.atomic import atomic_write_text
from medbrain.regen.slug import slugify

SYNTH_PROMPT = Path(__file__).resolve().parent.parent.parent / "prompts" / "brain_synthesize.md"
QUESTIONS_PROMPT = Path(__file__).resolve().parent.parent.parent / "prompts" / "brain_questions.md"


@dataclass
class BrainResult:
    started_at: datetime
    completed_at: datetime | None = None
    topic: str | None = None
    concepts_read: int = 0
    topics_read: int = 0
    memory_path: str | None = None
    questions_path: str | None = None
    errors: list[str] = field(default_factory=list)


def _last_brain_run() -> datetime | None:
    with session_scope() as sess:
        row = sess.execute(
            select(BrainRun.completed_at)
            .where(BrainRun.completed_at.is_not(None))
            .order_by(BrainRun.completed_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        return row


def _changed_files(directory: Path, since: datetime | None) -> list[Path]:
    if not directory.exists():
        return []
    out: list[Path] = []
    cutoff = since.timestamp() if since else 0
    for p in directory.rglob("*.md"):
        try:
            if p.stat().st_mtime >= cutoff:
                out.append(p)
        except OSError:
            continue
    return sorted(out)


def _file_payload(paths: list[Path], root: Path) -> list[dict]:
    out: list[dict] = []
    for p in paths:
        try:
            rel = p.relative_to(root)
            out.append({"path": str(rel).replace("\\", "/"), "content": p.read_text(encoding="utf-8")})
        except (OSError, ValueError) as e:
            out.append({"path": str(p), "error": str(e)})
    return out


def _record_run(result: BrainResult) -> None:
    with session_scope() as sess:
        sess.add(
            BrainRun(
                started_at=result.started_at,
                completed_at=result.completed_at,
                concepts_read=result.concepts_read,
                topics_read=result.topics_read,
                questions_added=0,
                questions_resolved=0,
                error="; ".join(result.errors)[:500] if result.errors else None,
            )
        )


def _resolve_paths(topic: str | None) -> tuple[Path, Path, str]:
    """Return (memory_path, questions_path, header_label) for the run."""
    if topic:
        slug = slugify(topic)
        return (
            config.MEMORY_DIR / f"{slug}.md",
            config.QUESTIONS_DIR / f"{slug}.md",
            topic,
        )
    return (config.MEMORY_FILE, config.QUESTIONS_FILE, "general")


def run_brain(
    *,
    topic: str | None = None,
    force_full: bool = False,
) -> BrainResult:
    """One Brain pass.

    Topic-scoped (recommended): pass topic="<the research topic>". Writes the
    synthesis + classified questions to per-topic files so each Student run has
    its own knowledge package.
    """
    started = datetime.now(UTC)
    result = BrainResult(started_at=started, topic=topic)

    since = None if force_full else _last_brain_run()

    concept_paths = _changed_files(config.CONCEPTS_DIR, since)
    topic_paths = _changed_files(config.NOTES_DIR, since)
    result.concepts_read = len(concept_paths)
    result.topics_read = len(topic_paths)

    if not concept_paths and not topic_paths:
        result.completed_at = datetime.now(UTC)
        _record_run(result)
        return result

    concepts_payload = _file_payload(concept_paths, config.BRAIN_DIR)
    topics_payload = _file_payload(topic_paths, config.BRAIN_DIR)

    memory_path, questions_path, label = _resolve_paths(topic)

    current_memory = memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""

    # --- 1. Synthesize memory ---
    try:
        synth_system = SYNTH_PROMPT.read_text(encoding="utf-8")
        topic_clause = (
            f"This synthesis is scoped to the research topic: **{topic}**. "
            "Restrict the narrative to claims, mechanisms, and patterns that bear on this topic. "
            "If a supplied note is unrelated, you may omit it from the synthesis.\n\n"
            if topic
            else ""
        )
        synth_user = (
            "# TASK\n"
            "Emit a single Markdown document as your message text. Do NOT use any tools. "
            "Do NOT request file write permission. Tools are disabled. The Python caller "
            "will persist your text output to disk on your behalf. Your first character "
            "MUST be `#`. Output ONLY the rewritten document — no prose, no preamble, "
            "no questions back to the user.\n\n"
            f"{topic_clause}"
            f"# Existing document state\n\n{current_memory or '(empty)'}\n\n"
            f"# Source: changed concept notes ({len(concepts_payload)})\n\n"
            f"{_render_files(concepts_payload)}\n\n"
            f"# Source: changed topic notes ({len(topics_payload)})\n\n"
            f"{_render_files(topics_payload)}\n\n"
            f"# Now\n{datetime.now(UTC).isoformat()}\n"
        )
        memory_body = call(synth_system, synth_user, timeout=180.0)
        atomic_write_text(memory_path, memory_body.strip() + "\n")
        result.memory_path = str(memory_path)
    except LLMError as e:
        result.errors.append(f"synthesize: {e}")

    # --- 2. Generate questions (Answerable / Gaps classification) ---
    try:
        q_system = QUESTIONS_PROMPT.read_text(encoding="utf-8")
        q_user = (
            "# TASK\n"
            "Emit a single Markdown document as your message text. No tools. "
            "Do NOT request permissions. The Python caller persists your output. "
            "First character MUST be `#`. Output ONLY the markdown.\n\n"
            f"# Topic context\n{label}\n\n"
            f"# Source: concept notes ({len(concepts_payload)})\n\n"
            f"{_render_files(concepts_payload)}\n\n"
            f"# Source: topic notes ({len(topics_payload)})\n\n"
            f"{_render_files(topics_payload)}\n\n"
            f"# Now\n{datetime.now(UTC).isoformat()}\n"
        )
        questions_body = call(q_system, q_user, timeout=180.0)
        atomic_write_text(questions_path, questions_body.strip() + "\n")
        result.questions_path = str(questions_path)
    except LLMError as e:
        result.errors.append(f"questions: {e}")
    except Exception as e:
        result.errors.append(f"questions: {e}")

    result.completed_at = datetime.now(UTC)
    _record_run(result)
    return result


def _render_files(payload: list[dict]) -> str:
    if not payload:
        return "(none)"
    parts: list[str] = []
    for item in payload:
        if "error" in item:
            parts.append(f"## {item['path']}\n[error: {item['error']}]")
        else:
            parts.append(f"## {item['path']}\n\n{item['content']}")
    return "\n\n---\n\n".join(parts)
