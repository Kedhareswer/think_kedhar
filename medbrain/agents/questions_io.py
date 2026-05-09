"""Read / write / merge questions.md.

Format: each question is an H2 block with a stable ID, followed by structured
fields and a body paragraph.

```
## Q-2026-05-01-001
- priority: 1
- status: open
- created: 2026-05-01T14:00:00Z
- topic: pediatric tafenoquine

What is the pediatric weight-band dose of tafenoquine for P. vivax radical cure?
```

Stable IDs let Brain re-emit a question (same ID) to update its priority/status,
or add new ones with fresh IDs without losing the old ones.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

QuestionStatus = Literal["open", "in_progress", "resolved"]


@dataclass
class Question:
    qid: str
    priority: int  # 1=high, 2=med, 3=low
    status: QuestionStatus
    created: datetime
    topic: str
    body: str
    updated: datetime | None = None

    def to_markdown(self) -> str:
        lines = [
            f"## {self.qid}",
            f"- priority: {self.priority}",
            f"- status: {self.status}",
            f"- created: {self.created.isoformat()}",
        ]
        if self.updated:
            lines.append(f"- updated: {self.updated.isoformat()}")
        lines.append(f"- topic: {self.topic}")
        lines.append("")
        lines.append(self.body.strip())
        return "\n".join(lines)


_HEADER = re.compile(r"^## (Q-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]+)\s*$", re.MULTILINE)
_FIELD = re.compile(r"^- ([a-z_]+):\s*(.*)$", re.MULTILINE)


@dataclass
class QuestionsFile:
    questions: list[Question] = field(default_factory=list)
    preamble: str = ""

    @classmethod
    def parse(cls, text: str) -> "QuestionsFile":
        if not text.strip():
            return cls()

        # Split on H2 headers; first chunk is preamble.
        positions = [(m.start(), m.group(1)) for m in _HEADER.finditer(text)]
        if not positions:
            return cls(preamble=text.strip())

        preamble = text[: positions[0][0]].strip()
        questions: list[Question] = []
        for i, (pos, qid) in enumerate(positions):
            end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
            block = text[pos:end]
            q = _parse_block(qid, block)
            if q is not None:
                questions.append(q)
        return cls(questions=questions, preamble=preamble)

    def serialize(self) -> str:
        out: list[str] = []
        if self.preamble:
            out.append(self.preamble)
        else:
            out.append("# Questions\n\nResearch backlog. Highest-priority `open` items get picked up by Student.")
        out.append("")
        # Sort: priority asc, status (open first), created desc.
        status_order = {"open": 0, "in_progress": 1, "resolved": 2}
        sorted_qs = sorted(
            self.questions,
            key=lambda q: (q.priority, status_order.get(q.status, 9), -q.created.timestamp()),
        )
        for q in sorted_qs:
            out.append(q.to_markdown())
            out.append("")
        return "\n".join(out).rstrip() + "\n"

    def by_id(self) -> dict[str, Question]:
        return {q.qid: q for q in self.questions}

    def merge(self, updates: list[Question]) -> tuple[int, int]:
        """Apply updates: same qid replaces, new qid appends. Returns (added, updated_count)."""
        existing = self.by_id()
        added = 0
        updated_n = 0
        now = datetime.now(UTC)
        for u in updates:
            if u.qid in existing:
                idx = self.questions.index(existing[u.qid])
                u.created = existing[u.qid].created
                u.updated = now
                self.questions[idx] = u
                updated_n += 1
            else:
                if u.created is None:
                    u.created = now
                self.questions.append(u)
                added += 1
        return added, updated_n


def _parse_block(qid: str, block: str) -> Question | None:
    fields: dict[str, str] = {}
    for m in _FIELD.finditer(block):
        fields[m.group(1)] = m.group(2).strip()

    # Body = everything after the last field line.
    field_lines_end = 0
    for m in _FIELD.finditer(block):
        field_lines_end = max(field_lines_end, m.end())
    body = block[field_lines_end:].strip()
    if body.startswith("\n"):
        body = body.lstrip("\n")

    try:
        return Question(
            qid=qid,
            priority=int(fields.get("priority", "3")),
            status=fields.get("status", "open"),  # type: ignore[arg-type]
            created=_parse_dt(fields.get("created")) or datetime.now(UTC),
            topic=fields.get("topic", ""),
            body=body,
            updated=_parse_dt(fields.get("updated")),
        )
    except (ValueError, KeyError):
        return None


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        # Handle Z suffix
        s = s.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def load(path: Path) -> QuestionsFile:
    if not path.exists():
        return QuestionsFile()
    return QuestionsFile.parse(path.read_text(encoding="utf-8"))


def next_qid(existing: list[Question], today: datetime | None = None) -> str:
    today = today or datetime.now(UTC)
    prefix = f"Q-{today.strftime('%Y-%m-%d')}"
    matching = [q.qid for q in existing if q.qid.startswith(prefix)]
    n = 1
    if matching:
        nums = []
        for qid in matching:
            try:
                nums.append(int(qid.rsplit("-", 1)[-1]))
            except ValueError:
                pass
        if nums:
            n = max(nums) + 1
    return f"{prefix}-{n:03d}"
