# MedBrain

Perpetually-learning medical knowledge base for malaria. RAGed by an external CDS.

**Spec:** [`docs/superpowers/specs/2026-05-01-medbrain-design.md`](docs/superpowers/specs/2026-05-01-medbrain-design.md)
**Build status:** [`.workspace/plan.md`](.workspace/plan.md)

## Architecture

Four agents on independent loops:
- **Student** (continuous) — fetches PubMed/WHO sources, extracts qualified claims, regenerates `concepts/*.md` and `notes/*.md`.
- **Brain** (hourly) — synthesizes `memory.md` cross-concept patterns, emits `questions.md` research backlog.
- **Graphify** (hourly) — rebuilds knowledge graph from `.md` corpus, exposes 8-primitive retrieval menu to CDS.
- **Dream** (weekly) — compacts `.md`, generates derivative artifacts (flashcards, mnemonics, analogies, gaps), decays low-salience claims to archive.

SQL (`brain/brain.db`) is source of truth. Everything else is a derived view.

## Setup

LLM backend is the **Claude Code CLI** (`claude` on PATH). No API key needed — uses your Claude Max subscription.

```bash
python -m venv .venv
.venv\Scripts\activate              # Windows
# source .venv/bin/activate         # macOS/Linux
pip install -e ".[dev]"
cp .env.example .env                # adjust LLM_MODEL or PUBMED_EMAIL if desired
python scripts/init_db.py
```

Verify the CLI is available:

```bash
claude --version
```

## Run

```bash
python scripts/student.py "<topic>"   # ingest a research topic
python scripts/brain.py                # hourly synthesis (memory.md + questions.md)
python scripts/graphify_run.py         # rebuild graph artifacts
python scripts/dream.py                # weekly compaction + derivatives + decay
python scripts/dream.py --check        # exit 0 if Dream is due, 1 otherwise
python scripts/active_learner.py       # pick top open question + ingest it
python scripts/active_learner.py --max 3  # research up to 3 questions in one pass
python scripts/api.py                  # retrieval API server (127.0.0.1:7117)
```

## Layout

```
medbrain/         Python package (agents, models, tools, api)
scripts/          Entrypoints (init_db, student, brain, dream, etc.)
prompts/          LLM prompt templates
tests/            Test suite
brain/            Runtime data (gitignored): brain.db, concepts/, notes/, ...
docs/             Design specs
.workspace/       Build scratch (humans only — runtime ignores)
```

## Investor pitch

Open [`medbrain-pitch.html`](./medbrain-pitch.html) in a browser. ~2:30 scripted replay. Reload to replay.
