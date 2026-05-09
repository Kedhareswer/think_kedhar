"""Brain agent: read changed concepts/notes, regenerate memory.md + update questions.md."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

from medbrain import config
from medbrain.agents.questions_io import (
    Question,
    QuestionsFile,
    load as load_questions,
    next_qid,
)
from medbrain.db import session_scope
from medbrain.llm import LLMError, call, call_json
from medbrain.models import BrainRun
from medbrain.regen.atomic import atomic_write_text

SYNTH_PROMPT = Path(__file__).resolve().parent.parent.parent / "prompts" / "brain_synthesize.md"
QUESTIONS_PROMPT = Path(__file__).resolve().parent.parent.parent / "prompts" / "brain_questions.md"


@dataclass
class BrainResult:
    started_at: datetime
    completed_at: datetime | None = None
    concepts_read: int = 0
    topics_read: int = 0
    questions_added: int = 0
    questions_updated: int = 0
    questions_resolved: int = 0
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
                questions_added=result.questions_added,
                questions_resolved=result.questions_resolved,
                error="; ".join(result.errors)[:500] if result.errors else None,
            )
        )


def run_brain(*, force_full: bool = False) -> BrainResult:
    """One Brain pass: rewrite memory.md and update questions.md based on recent changes.

    By default reads only files modified since the last successful Brain run.
    Pass force_full=True to read all .md files.
    """
    started = datetime.now(UTC)
    result = BrainResult(started_at=started)

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

    current_memory = (
        config.MEMORY_FILE.read_text(encoding="utf-8") if config.MEMORY_FILE.exists() else ""
    )

    # --- 1. Synthesize memory.md ---
    try:
        synth_system = SYNTH_PROMPT.read_text(encoding="utf-8")
        synth_user = (
            "# TASK\n"
            "Emit a single Markdown document as your message text. Do NOT use any tools. "
            "Do NOT request file write permission. Tools are disabled. The Python caller "
            "will persist your text output to disk on your behalf. Your first character "
            "MUST be `#`. Output ONLY the rewritten document — no prose, no preamble, "
            "no questions back to the user.\n\n"
            f"# Existing document state\n\n{current_memory or '(empty)'}\n\n"
            f"# Source: changed concept notes ({len(concepts_payload)})\n\n"
            f"{_render_files(concepts_payload)}\n\n"
            f"# Source: changed topic notes ({len(topics_payload)})\n\n"
            f"{_render_files(topics_payload)}\n\n"
            f"# Now\n{datetime.now(UTC).isoformat()}\n"
        )
        memory_body = call(synth_system, synth_user, timeout=180.0)
        atomic_write_text(config.MEMORY_FILE, memory_body.strip() + "\n")
        result.memory_path = str(config.MEMORY_FILE)
    except LLMError as e:
        result.errors.append(f"synthesize: {e}")

    # --- 2. Update questions.md ---
    try:
        qfile = load_questions(config.QUESTIONS_FILE)
        existing_open = [q for q in qfile.questions if q.status != "resolved"]

        q_system = QUESTIONS_PROMPT.read_text(encoding="utf-8")
        q_user = (
            f"# Current open questions ({len(existing_open)})\n\n"
            f"```json\n{[{'qid': q.qid, 'priority': q.priority, 'status': q.status, 'topic': q.topic, 'body': q.body} for q in existing_open]!r}\n```\n\n"
            f"# Changed concepts ({len(concepts_payload)})\n\n"
            f"{_render_files(concepts_payload)}\n\n"
            f"# Changed notes ({len(topics_payload)})\n\n"
            f"{_render_files(topics_payload)}\n"
        )
        delta = call_json(q_system, q_user, timeout=180.0)

        new_questions: list[Question] = []
        now = datetime.now(UTC)
        for nq in delta.get("new_questions", []):
            qid = next_qid(qfile.questions + new_questions, today=now)
            new_questions.append(
                Question(
                    qid=qid,
                    priority=int(nq.get("priority", 3)),
                    status="open",
                    created=now,
                    topic=str(nq.get("topic", "")).strip(),
                    body=str(nq.get("body", "")).strip(),
                )
            )

        update_qs: list[Question] = []
        existing_by_id = qfile.by_id()
        for upd in delta.get("updates", []):
            qid = upd.get("qid")
            if not qid or qid not in existing_by_id:
                continue
            base = existing_by_id[qid]
            update_qs.append(
                Question(
                    qid=qid,
                    priority=int(upd.get("priority", base.priority)),
                    status=upd.get("status", base.status),
                    created=base.created,
                    topic=base.topic,
                    body=base.body,
                )
            )

        added, updated_n = qfile.merge(new_questions + update_qs)
        result.questions_added = added
        result.questions_updated = updated_n
        result.questions_resolved = sum(
            1 for u in update_qs if u.status == "resolved"
        )
        atomic_write_text(config.QUESTIONS_FILE, qfile.serialize())
        result.questions_path = str(config.QUESTIONS_FILE)
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
