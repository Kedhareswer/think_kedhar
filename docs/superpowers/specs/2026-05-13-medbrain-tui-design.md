# MedBrain TUI — Design Spec

**Date:** 2026-05-13
**Status:** Draft
**Scope:** v1 terminal UI for human curators of the MedBrain corpus.

---

## 1. Goal

Give a clinician-curator a fast, keyboard-driven view of the MedBrain
corpus so they can:

1. **Browse** concepts, notes, memory, flashcards by slug — see all four
   parallel files for any concept in one screen.
2. **Watch the loop** — see what Student just ingested, what Brain just
   synthesised, what's open in `questions.md`.
3. **Approve / reject** claims in the review queue.
4. **Trigger** runs (Student on a topic, Brain synth, Dream, Export master sheet).
5. **Read** the Master-sheet preview before exporting.

Out of scope for v1: editing concept .md content (use VS Code), graph
visualisation (use the existing graph.html), authentication.

Visual reference: [opencode](https://github.com/anomalyco/opencode),
[amux](https://github.com/andyrewlee/amux),
[ATAC](https://github.com/Julien-cpsn/ATAC). All three use Rust + Ratatui.
MedBrain is Python so we use [Textual](https://textual.textualize.io/) —
same design idiom (panels, key bindings, command palette), renders in a
modern terminal, and crucially has a built-in web-export renderer so the
same UI works in a browser for demo / remote review.

## 2. Layout

Three columns, full-screen by default. Status bar at the bottom, key-hint
strip across the top.

```
┌─ Med·Brain ─ student/brain/dream ─ exports/master_sheet.xlsx ─────────────┐
│  q quit  /  search  ⏎  open  ↑↓ nav  ⇧S student  ⇧B brain  ⇧D dream  ⇧E export │
├──────────────────┬────────────────────────────────┬───────────────────────┤
│ ▸ CONCEPTS  52   │ ▾ artemisinin-resistance       │ THE GIST              │
│ ▾ NOTES                                            │  Two-sentence brain   │
│   resistance     │ # Artemisinin Resistance        │  synthesis here…      │
│   treatment      │ in P. falciparum               │                       │
│ ▾ QUESTIONS  14  │                                 │ ── FLASHCARDS  12 ──  │
│ ▸ MEMORY    18   │ ## Synthesis                    │  Q: First-line treat… │
│ ▸ FLASHCARDS 8   │ Partial artemisinin resistance  │  A: Artesunate IV…    │
│ ▸ ARCHIVE   142  │ in P. falciparum is now…        │                       │
│                  │ [c:a4f2b8c1]                    │ ── QUESTIONS  3 ──   │
│  ── filters ──   │                                 │  ① pediatric dose     │
│  ☐ pending only  │ ## Status                       │  ② pregnancy IV art   │
│  ☐ recent <7d    │ - C580Y dominant in GMS         │  ③ AKI safety profile │
│  ☑ malaria       │ - Spread to E. Africa (R561H)   │                       │
│                  │ - WHO validated [c:8e72b1d9]   │ ── EVIDENCE ────────  │
│                  │                                 │  4 RCT · 9 cohort     │
│                  │ ## Evidence                     │  2 guideline · 1 MA   │
│                  │ Meta-analysis covers 15 country│                       │
│                  │ studies (n=12,500). Cohort dat… │                       │
├──────────────────┴────────────────────────────────┴───────────────────────┤
│ ● running · Student ingesting "ACT regimens" · 4/12 papers · 2m elapsed   │
└───────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Left pane — corpus tree

Collapsible groups, each shows count:

- **CONCEPTS** (`student/concepts/*.md`) — flat list of slugs, alphabetical
- **NOTES** (`student/notes/<topic>/*.md`) — grouped by topic folder
- **QUESTIONS** — open questions from `brain/questions.md` and per-topic
- **MEMORY** (`student/memory/*.md`) — per-concept Brain gist
- **FLASHCARDS** (`student/flashcards/*.md`) — Dream output
- **ARCHIVE** (`dream/archive/*.jsonl`) — decayed claims, read-only

Filter chips below the tree apply across all groups:
`pending only`, `recent <7d`, slug substring.

### 2.2 Centre pane — focused .md

Renders the focused file's markdown with light syntax (headings bold,
`[c:xxxxxxxx]` styled as a dim chip, table rows aligned). Scrollable.
`e` opens the file in `$EDITOR` (VS Code for most users).

### 2.3 Right pane — companions

For the focused concept, show the three sibling files inline:

- **THE GIST** — `student/memory/<slug>.md` (Brain output, 2–4 sentences)
- **FLASHCARDS** — `student/flashcards/<slug>.md` (Dream output, first 3 cards visible, scroll for more)
- **QUESTIONS** — open questions naming this entity, with priority
- **EVIDENCE** — claim count by grade (pulled from SQL)

This is the "learner view" — one screen, everything about one concept.

### 2.4 Bottom bar — runner status

Streaming log line for any background agent. Colours:
🟢 idle · 🔵 running · 🟡 review needed · 🔴 error.

## 3. Modal screens

Triggered by uppercase shortcuts. All modals: `Esc` cancels, `Enter` runs.

| Shortcut | Modal | Action |
|----------|-------|--------|
| `⇧S` | **Student** | Input box for a topic. Optionally pick from top-3 open questions (suggestion list). On Enter: spawn `python scripts/student.py "<topic>"` in background, status bar streams progress. |
| `⇧B` | **Brain** | Confirm hourly synth. Run `python scripts/brain.py` in background. |
| `⇧D` | **Dream** | Show what would compact (`python scripts/dream.py --check`). Enter to run. |
| `⇧E` | **Export** | Toggle `--llm` checkbox. Show estimated time (concepts × ~15s). Run `python scripts/export_master_sheet.py [--llm]`. |
| `⇧R` | **Review queue** | List of `pending_review` claims. `a` approve, `r` reject, `s` skip, `j/k` nav. |
| `⇧Q` | **Questions** | Full view of all open questions, ranked. `Enter` on one → triggers Student with that question as topic. |
| `/` | **Search** | Fuzzy slug search across all groups. |
| `:` | **Command** | Command palette (Textual's built-in) for everything else. |

## 4. State sync

The TUI is **read-mostly**. State sources:

- **SQL** (`brain/brain.db`) — claims, salience, dirty_tracker, BrainRun, DreamRun
- **Filesystem** — all .md files, mtime-watched via `watchdog` for live refresh
- **Subprocess** — agent runs spawned with `subprocess.Popen`; stdout is
  piped into the status-bar log.

No global lock. The TUI never writes corpus files directly — actions are
always "trigger the existing agent script and watch it". Single source of
truth stays SQL + the filesystem; the TUI is a viewer.

## 5. Tech stack

- **Textual** — UI framework. Stable, async-friendly, easy to test.
- **watchdog** — fs change events → trigger panel refresh.
- **rich** — markdown rendering inside the centre pane (Textual uses Rich
  underneath, so this is essentially free).
- **subprocess** — agent spawning, with stdout streamed to the status bar.

No new dependencies on the corpus side; the TUI is a pure consumer.

## 6. File layout

```
medbrain/
  tui/
    __init__.py
    app.py            # MedBrainApp(textual.App) — root, key bindings
    widgets/
      tree.py         # CorpusTree widget
      viewer.py       # MarkdownViewer centre pane
      companions.py   # Gist/Flashcards/Questions/Evidence right pane
      status.py       # RunnerStatus bottom bar
    screens/
      student.py      # ⇧S modal
      brain.py        # ⇧B modal
      dream.py        # ⇧D modal
      export.py       # ⇧E modal
      review.py       # ⇧R review queue
      questions.py    # ⇧Q questions board
    services/
      corpus.py       # filesystem scanning, watch
      runner.py       # subprocess launcher
      sql.py          # thin layer over medbrain.db for TUI reads
scripts/
  tui.py              # entrypoint: `python scripts/tui.py`
```

## 7. Key design choices

- **Read-mostly TUI.** Edits go through agents, not direct fs writes. This
  preserves the existing safety invariants (atomic writes, snapshot before
  Dream, etc.).
- **One screen = one concept.** The right pane bundles everything Brain and
  Dream produced *about the focused concept* so reviewers don't context-switch.
- **Status bar is the runner.** A clinician shouldn't need a second terminal
  to know whether Student is currently working. Streaming log lives at the
  bottom.
- **Textual's web export** — `textual serve scripts/tui.py` exposes the
  TUI over HTTP for demos and remote review. Same code, no Electron.
- **No mouse required.** Every action has a keybind. Mouse works but is
  optional.

## 8. Out of scope (v1)

- Editing .md files in-place — out (use $EDITOR).
- Graph visualisation — out (the existing graph.html covers this).
- Authentication / multi-user — out (single-host curator only).
- Real-time collaboration — out.
- Dream rollback UI — out (use git on `brain/.dream-snapshots/`).

## 9. Phasing

- **TUI-1:** Layout shell — three panes, corpus tree, viewer. Read-only.
- **TUI-2:** Companions pane (gist/flashcards/questions/evidence).
- **TUI-3:** Status bar with subprocess streaming.
- **TUI-4:** Modal screens for Student / Brain / Dream / Export.
- **TUI-5:** Review queue (`⇧R`) for pending claims.
- **TUI-6:** Web-serve mode (`textual serve scripts/tui.py`).
