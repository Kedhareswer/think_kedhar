"""Derivative artifact generation: flashcards, mnemonics, analogies, gaps.

Output paths (post-restructure):
  student/flashcards/<entity-slug>.md   (co-located with the learner view)
  dream/mnemonics/<entity-slug>.md
  dream/analogies/<entity-slug>.md
  dream/gaps/<entity-slug>.md

Flashcards live under student/ so each concept has its concept-note, topic
note, brain memory, and flashcards side-by-side under one slug. The other
three derivative types live under dream/ as firewalled outputs that never
auto-feed back into the primary corpus.

Each file is rendered Markdown derived from the LLM's JSON output. The
retrieval API serves these only when ``?include_derivative=<type>`` is set.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import select

from medbrain import config
from medbrain.db import session_scope
from medbrain.llm import LLMError, call_json
from medbrain.models import Claim
from medbrain.regen.atomic import atomic_write_text
from medbrain.regen.slug import slugify

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"

DERIVATIVE_TYPES: tuple[str, ...] = ("flashcards", "mnemonics", "analogies", "gaps")

_PROMPT_FILES = {
    "flashcards": PROMPTS_DIR / "dream_flashcards.md",
    "mnemonics": PROMPTS_DIR / "dream_mnemonics.md",
    "analogies": PROMPTS_DIR / "dream_analogies.md",
    "gaps": PROMPTS_DIR / "dream_gaps.md",
}


@dataclass
class DerivativeResult:
    entity: str
    written: list[str] = field(default_factory=list)  # type names that produced output
    skipped: dict[str, str] = field(default_factory=dict)  # type → reason
    errors: dict[str, str] = field(default_factory=dict)  # type → error message


def _entity_dir(dtype: str) -> Path:
    return config.DERIVATIVE_DIRS[dtype]


def _output_path(dtype: str, entity: str) -> Path:
    return _entity_dir(dtype) / f"{slugify(entity)}.md"


def _claims_for_entity(entity: str) -> list[Claim]:
    key = entity.strip().lower()
    if not key:
        return []
    with session_scope() as sess:
        rows = sess.execute(
            select(Claim).where(
                (Claim.subject_text.ilike(key)) | (Claim.object_text.ilike(key))
            )
        ).scalars().all()
        # Force-load while session open
        for r in rows:
            _ = r.subject_text, r.object_text, r.predicate, r.qualifiers
        return list(rows)


def _claims_payload(claims: list[Claim]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for c in claims:
        out.append(
            {
                "claim_id": c.claim_id,
                "subject": c.subject_text,
                "predicate": c.predicate.value,
                "object": c.object_text,
                "qualifiers": c.qualifiers or {},
                "certainty": c.certainty.value,
                "evidence_grade": c.evidence_grade.value,
                "status": c.status.value,
                "current": c.valid_until is None,
            }
        )
    return out


def _concept_md(entity: str) -> str:
    p = config.CONCEPTS_DIR / f"{slugify(entity)}.md"
    if p.exists():
        try:
            return p.read_text(encoding="utf-8")
        except OSError:
            return ""
    return ""


def _render_flashcards(data: dict[str, Any], entity: str) -> str:
    cards = data.get("cards") or []
    lines = [f"# Flashcards — {entity}", ""]
    if not cards:
        lines.append("_No cards generated._")
        return "\n".join(lines) + "\n"
    for i, card in enumerate(cards, 1):
        front = str(card.get("front", "")).strip()
        back = str(card.get("back", "")).strip()
        tags = card.get("tags") or []
        lines += [
            f"## Card {i}",
            "",
            f"**Q:** {front}",
            "",
            f"**A:** {back}",
            "",
            f"Tags: {' '.join(f'`{t}`' for t in tags) if tags else '_none_'}",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def _render_mnemonics(data: dict[str, Any], entity: str) -> str:
    mnems = data.get("mnemonics") or []
    lines = [f"# Mnemonics — {entity}", ""]
    if not mnems:
        lines.append("_No mnemonics generated._")
        return "\n".join(lines) + "\n"
    for i, m in enumerate(mnems, 1):
        scope = str(m.get("scope", "")).strip()
        device = str(m.get("device", "")).strip()
        expansion = str(m.get("expansion", "")).strip()
        evidence = m.get("evidence") or []
        lines += [
            f"## {i}. {scope}",
            "",
            f"**Device:** {device}",
            "",
            f"**Expansion:** {expansion}",
            "",
            f"Evidence: {', '.join(f'[c:{e}]' for e in evidence) if evidence else '_none_'}",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def _render_analogies(data: dict[str, Any], entity: str) -> str:
    items = data.get("analogies") or []
    lines = [f"# Analogies — {entity}", ""]
    if not items:
        lines.append("_No analogies generated._")
        return "\n".join(lines) + "\n"
    for i, a in enumerate(items, 1):
        concept = str(a.get("concept_being_explained", "")).strip()
        domain = str(a.get("analogy_domain", "")).strip()
        mapping = a.get("mapping") or []
        breaks = str(a.get("where_it_breaks", "")).strip()
        lines += [
            f"## {i}. {concept}",
            "",
            f"**Analogy:** {domain}",
            "",
            "| Medical | Everyday | Evidence |",
            "|---------|----------|----------|",
        ]
        for row in mapping:
            med = str(row.get("medical", "")).strip()
            ev_id = str(row.get("evidence", "")).strip()
            ev = f"[c:{ev_id}]" if ev_id else ""
            lines.append(f"| {med} | {row.get('everyday', '')} | {ev} |")
        lines += [
            "",
            f"**Where it breaks:** {breaks}",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def _render_gaps(data: dict[str, Any], entity: str) -> str:
    items = data.get("gaps") or []
    lines = [f"# Gaps — {entity}", ""]
    if not items:
        lines.append("_No gaps identified._")
        return "\n".join(lines) + "\n"
    for i, g in enumerate(items, 1):
        topic = str(g.get("topic", "")).strip()
        q = str(g.get("question", "")).strip()
        why = str(g.get("why_it_matters", "")).strip()
        ev = g.get("evidence_so_far") or []
        search = str(g.get("suggested_search", "")).strip()
        existing_qid = g.get("existing_qid")
        lines += [
            f"## {i}. {topic}",
            "",
            f"**Question:** {q}",
            "",
            f"**Why it matters:** {why}",
            "",
            f"Evidence so far: {', '.join(f'[c:{e}]' for e in ev) if ev else '_none_'}",
            "",
            f"Suggested search: `{search}`" if search else "",
        ]
        if existing_qid:
            lines.append(f"Tracks existing: **{existing_qid}**")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


_RENDERERS = {
    "flashcards": _render_flashcards,
    "mnemonics": _render_mnemonics,
    "analogies": _render_analogies,
    "gaps": _render_gaps,
}


def _build_user_prompt(
    entity: str, concept_md: str, claims: list[dict[str, Any]], dtype: str
) -> str:
    parts = [
        f"# Entity\n{entity}\n",
        f"# Concept synthesis\n\n{concept_md or '_(no concept note yet)_'}\n",
        f"# Claims (n={len(claims)})\n\n```json\n{json.dumps(claims, indent=2)}\n```\n",
    ]
    if dtype == "gaps":
        existing_qids = _existing_qids_for_entity(entity)
        if existing_qids:
            parts.append(
                "# Existing tracked questions for this entity\n\n```\n"
                + "\n".join(existing_qids)
                + "\n```\n"
            )
    return "\n".join(parts)


def _existing_qids_for_entity(entity: str) -> list[str]:
    """Pull Q-IDs from questions.md that mention this entity. Best-effort."""
    qf = config.QUESTIONS_FILE
    if not qf.exists():
        return []
    try:
        text = qf.read_text(encoding="utf-8")
    except OSError:
        return []
    key = entity.lower()
    out: list[str] = []
    current_qid: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## Q-"):
            current_qid = stripped[3:].split()[0].strip()
        elif current_qid and key in line.lower():
            out.append(current_qid)
            current_qid = None
    return out


def generate_for_entity(
    entity: str,
    *,
    types: tuple[str, ...] = DERIVATIVE_TYPES,
    timeout: float = 180.0,
) -> DerivativeResult:
    """Generate all requested derivative types for one entity."""
    result = DerivativeResult(entity=entity)

    claims = _claims_for_entity(entity)
    if not claims:
        for t in types:
            result.skipped[t] = "no claims"
        return result

    payload = _claims_payload(claims)
    concept_md = _concept_md(entity)

    for dtype in types:
        if dtype not in _PROMPT_FILES:
            result.errors[dtype] = f"unknown derivative type: {dtype}"
            continue
        try:
            system = _PROMPT_FILES[dtype].read_text(encoding="utf-8")
            user = _build_user_prompt(entity, concept_md, payload, dtype)
            data = call_json(system, user, timeout=timeout)
        except LLMError as e:
            result.errors[dtype] = str(e)
            continue

        rendered = _RENDERERS[dtype](data, entity)
        out_path = _output_path(dtype, entity)
        atomic_write_text(out_path, rendered)
        result.written.append(dtype)

    return result


def entities_with_concept_notes() -> list[str]:
    """Every entity that has a concepts/<slug>.md file. Returns labels (not slugs)."""
    if not config.CONCEPTS_DIR.exists():
        return []
    out: set[str] = set()
    # Pull labels from claims so we get original casing; concepts dir gives slugs only.
    with session_scope() as sess:
        rows = sess.execute(
            select(Claim.subject_text).distinct()
        ).scalars().all()
        out.update(r for r in rows if r)
        rows2 = sess.execute(
            select(Claim.object_text).distinct()
        ).scalars().all()
        out.update(r for r in rows2 if r)
    # Filter to entities that have concept notes on disk.
    have_notes = {p.stem for p in config.CONCEPTS_DIR.glob("*.md")}
    return sorted(e for e in out if slugify(e) in have_notes)
