# MedBrain

Perpetually-learning medical knowledge base. Read by an external CDS via the
8-primitive retrieval menu; verified by humans against the Master sheet xlsx.

**Spec:** [`docs/superpowers/specs/2026-05-01-medbrain-design.md`](docs/superpowers/specs/2026-05-01-medbrain-design.md)
**Visual:** open [`medbrain-agents.html`](./medbrain-agents.html) in a browser
**Pitch replay:** open [`medbrain-pitch.html`](./medbrain-pitch.html)

## Agents (three loops + Graphify)

- **Student** (continuous) — fetches PubMed / WHO sources, extracts qualified claims, regenerates `student/concepts/*.md` and `student/notes/*.md`.
- **Brain** (hourly) — synthesises `brain/memory.md` and emits `brain/questions.md` (Student's research backlog).
- **Graphify** (hourly, +15 min) — rebuilds the graph from the markdown corpus, exposes 8 retrieval primitives.
- **Dream** (weekly) — compacts `.md`, generates flashcards / mnemonics / analogies / gaps, decays cold claims to archive.

The active-learning loop closes through `brain/questions.md`: Brain writes
priority-ranked open questions; Student picks the top one each cycle and
treats it as a fresh research topic.

## Layout (learner-centric)

```
student/                  what a learner sees per concept
  concepts/               (Student writes)
  notes/                  (Student writes)
  memory/                 (Brain writes — per-concept gist)
  flashcards/             (Dream writes — per-concept cards)

brain/                    Brain's working area + global outputs
  brain.db                SQL source of truth
  memory.md               global cross-concept synthesis
  questions/              per-concept research backlog
  questions.md            global research backlog
  graph/                  Graphify outputs

dream/                    Dream's other derivatives (firewalled)
  mnemonics/  analogies/  gaps/
  archive/                decayed claims (never deleted)

exports/                  human-verification artefacts
  master_sheet.xlsx       multi-sheet Excel matching Master sheet.xlsx schema

medbrain/                 Python package (agents, models, tools, exporters, api)
prompts/                  LLM prompt templates
scripts/                  CLI entrypoints
tests/                    Test suite (shared fixture in tests/conftest.py)
```

For each concept slug, four parallel files exist (when populated):
`student/concepts/<slug>.md` (Student) · `student/notes/<topic>/<slug>.md`
(Student) · `student/memory/<slug>.md` (Brain) · `student/flashcards/<slug>.md`
(Dream). Predictable per-key view, modular per agent.

SQL is the only source of truth. Every `.md` is a derived view. Every graph
is derived from `.md`.

## Setup

LLM backend is the **Claude Code CLI** (`claude` on PATH). No API key needed.

```bash
python -m venv .venv
.venv\Scripts\activate              # Windows
# source .venv/bin/activate         # macOS / Linux
pip install -e ".[dev]"
cp .env.example .env                # adjust LLM_MODEL or PUBMED_EMAIL if desired
python scripts/init_db.py
```

Path overrides (all optional, defaults shown):

```
MEDBRAIN_ROOT=.        # parent for the four runtime trees
STUDENT_DIR=./student
BRAIN_DIR=./brain
DREAM_DIR=./dream
EXPORTS_DIR=./exports
```

## Run

```bash
python scripts/student.py "<topic>"          # ingest a research topic
python scripts/brain.py                      # hourly synthesis
python scripts/graphify_run.py               # rebuild graph artefacts
python scripts/dream.py                      # weekly compaction + derivatives + decay
python scripts/dream.py --check              # exit 0 if Dream is due, 1 otherwise
python scripts/active_learner.py             # pick top open question + ingest it
python scripts/active_learner.py --max 3     # research up to 3 questions in one pass
python scripts/api.py                        # retrieval API (127.0.0.1:7117)
python scripts/export_master_sheet.py        # write exports/master_sheet.xlsx
python scripts/export_master_sheet.py --llm  # reference-style prose via Claude (slow)
python scripts/tui.py                        # launch the curator TUI
```

## Curator TUI

`python scripts/tui.py` opens a Textual three-pane terminal UI:

- **Left** — corpus tree (concepts · notes · memory · flashcards · questions)
- **Centre** — focused .md file rendered as Markdown
- **Right** — per-concept companions (gist · flashcards preview · open questions · evidence count by grade)

Keybinds: `q` quit · `r` refresh tree · `s/b/d/e` Student/Brain/Dream/Export
(stubs in v1 — print intent to status bar). Spec at
[`docs/superpowers/specs/2026-05-13-medbrain-tui-design.md`](docs/superpowers/specs/2026-05-13-medbrain-tui-design.md);
visual mock at [`medbrain-tui.html`](medbrain-tui.html).

## Master sheet output

`exports/master_sheet.xlsx` is the **human-verification artefact**. It
mirrors `Master sheet.xlsx` exactly: nine sheets (Conditions · Medications ·
Lab tests · RadiologyImaging · Special Diagnostic Studies ·
HistopathologyCytology · SurgeriesProcedures · Provider type & Specialty ·
Hospital Addressbook), same column headers character-for-character,
including the `Completed` / `Reviewed` columns reviewers use to track sign-off.

Each run rewrites the file from scratch. Domains we don't yet ingest keep
their headers but stay empty — the schema is stable even before data lands.

Sheet status today (see [`docs/sheet-coverage.md`](docs/sheet-coverage.md)
for full detail):

| Sheet | Status | Notes |
|---|---|---|
| Conditions | ● populated (8 rows, LLM) | malaria condition concepts → reference-style prose |
| Medications | ● builder ready | `--llm` writes drug rows once concept set is enriched |
| Lab tests, Radiology, Special Diag, Histopath, Surgeries | ○ schema only | need targeted ingestion or different specialty corpus |
| Provider type & Specialty, Hospital Addressbook | ◐ directory data | need CSV import from MOH / professional registries |

## Trusted sources & traceability

Every claim that lands in the knowledge base cites at least one source from
[`medbrain/sources_registry.py`](medbrain/sources_registry.py). The registry
declares each source's tier (peer-reviewed / curated / operational /
encyclopedic), access mechanism (API / MCP / manual), and which Master-sheet
columns it's authorised to populate:

| Tier 1 (primary)         | PubMed · WHO · ClinicalTrials.gov |
| Tier 2 (curated)         | ChEMBL · ICD-10-CM/PCS · MedlinePlus |
| Tier 3 (operational)     | NAFDAC · FMOH Master Facility List · MDCN |
| Tier 4 (encyclopedic)    | Wikipedia (orientation only, never sole source) |

Every Master-sheet row's `Sources` cell joins these short codes with ` | `
and, where a connector was actually called, appends the specific identifier
(`PubMed:38321292 | ChEMBL:CHEMBL192 | ICD-10:B50`). Reviewers can trace
any cell back to the URL that supports it.

Run `python -c "from medbrain.sources_registry import registry_markdown; print(registry_markdown())"`
to dump the full registry as a Markdown table.

## Skills baked into prompts

The four research-voice skills are embedded in the agent prompts rather
than invoked per-run, so every cycle runs with the same discipline:

- **academic-researcher** — `prompts/concept_*.md`, `prompts/research_plan.md`: rigorous inline citation `[c:<id>]`, evidence-grade awareness, MeSH-first query design.
- **fact-checker** — `prompts/concept_*.md`, `prompts/brain_synthesize.md`, `prompts/dream_compact.md`: no hallucinated claims; contradictions surfaced explicitly with both ids.
- **deep-research** — `prompts/research_plan.md`, `prompts/brain_synthesize.md`: cross-concept synthesis as the deliverable; active-learning bias on backlog-driven runs.
- **technical-writer** — every prompt: tight clinical prose, no padding, layperson + clinician dual register where the column reader is mixed (e.g. Conditions sheet).

## Tests

```bash
pytest
```

All test fixtures route runtime through a tmp dir via the shared
`tests/conftest.py::setup_tmp_root` helper — they set
`MEDBRAIN_ROOT/STUDENT_DIR/BRAIN_DIR/DREAM_DIR/EXPORTS_DIR` together and
reload `medbrain.config` + `medbrain.db`.

## Investor pitch

Open [`medbrain-pitch.html`](./medbrain-pitch.html) — ~2:30 scripted
replay, reload to replay.
