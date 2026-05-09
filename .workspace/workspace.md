# MedBrain build workspace

Scratch space for building MedBrain. Ignored by runtime. Notes here are for the humans + agents constructing the system, not for the brain itself.

## Files in this workspace

- `plan.md` — phased build plan tracking which spec sections are implemented
- `todo.md` — concrete next actions, smallest unit of work
- `changelogs.md` — append-only log of build progress (date, what shipped, what's left)
- `gaps.md` — known holes in the spec or implementation, deferred decisions
- `learnings.md` — what we discovered while building (prompts that worked, parser quirks, perf notes, etc.)

## Source-of-truth design

`docs/superpowers/specs/2026-05-01-medbrain-design.md`

This workspace tracks **execution against** that spec. Update the spec only when a design decision changes; track build progress here.

## Conventions

- Append entries with date headers (`## 2026-05-01`).
- `todo.md` items use `[ ]` / `[x]` checkboxes with one-line scope.
- `gaps.md` entries name the gap, link the spec section, propose a resolution.
- `learnings.md` entries are short observations that future-you would want to know.
- Anything in `.workspace/` is ignored at runtime — never read by Student / Brain / Graphify / Dream agents.
