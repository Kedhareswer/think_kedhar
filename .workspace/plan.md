# Build Plan

Phased execution against `docs/superpowers/specs/2026-05-01-medbrain-design.md`.

Each phase is independently shippable. Mark `[x]` when phase passes its acceptance test.

---

## Phase 0 — Project skeleton (pre-req) ✅

- [x] Python project: `pyproject.toml`, `.venv`, pip install.
- [x] Directory layout per spec §6 (created on first init).
- [x] SQLAlchemy models for §10 tables (`claims`, `sources`, `evidence_ledger`, `dirty_tracker`, `salience`).
- [x] Init script: `python scripts/init_db.py` creates SQLite schema.
- [x] `.env.example`, requirements declared in pyproject, README pointing to spec.
- [x] Smoke tests green (3/3).

**Acceptance met:** init script creates `brain/brain.db` with all tables; pytest passes.

---

## Phase 1 — Qualified-claim schema + ingestion primitives ✅ (build)

- [x] Claim model with all qualifier fields (spec §4) — landed in Phase 0.
- [x] PubMed fetcher (eutils efetch via httpx + lxml XML parse).
- [ ] WHO doc fetcher (deferred to Phase 1.5; PubMed-only proves the loop).
- [x] Claim extractor: LLM prompt → JSON → pydantic-validated `ExtractedClaim` list.
- [x] Novelty gate: dedup (subject+predicate+object+region+endemic+pregnancy), contradiction (opposing predicates), evidence grade from publication-type metadata.
- [x] Auto-promote vs review-queue routing per spec §5.
- [x] Student CLI (`scripts/student.py <PMID>`).
- [x] 10 unit tests green.

**Acceptance pending live API run:** ingest 3+ PMIDs (e.g. 33579778, 32971908, plus a case report) and verify claims land with correct status. Requires `ANTHROPIC_API_KEY` in `.env`.

---

## Phase 2 — Student concepts/notes regeneration ✅ (build)

- [x] `dirty_tracker` writes on every claim insert (entity + derived topic).
- [x] `concepts/<entity>.md` regenerator with LLM synthesis prompt.
- [x] `notes/<topic>.md` regenerator with predicate-derived topic mapping.
- [x] Atomic write (`.tmp` + `os.replace`).
- [x] Coordinator processes dirty rows + marks `processed_at`.
- [x] Hooked into Researcher tail (auto after ingest); standalone `scripts/regen.py` for catch-up.
- [x] 11 tests green.

**Acceptance pending live run:** ingest a topic; verify `brain/concepts/*.md` + `brain/notes/**/*.md` populated with cited synthesis.

---

## Phase 3 — Brain agent: hourly synthesis ✅ (build)

- [x] Brain agent script: `python scripts/brain.py` (with `--full` flag).
- [x] Reads `.md` files modified since last completed BrainRun (BrainRun SQL table).
- [x] LLM synthesis prompt → `memory.md` (full re-write each run).
- [x] Gap detection prompt → `questions.md` (JSON delta merged into stable-ID Q blocks).
- [x] Status enum (open/in_progress/resolved); priority 1/2/3.
- [x] No-change short-circuit (LLM not called when nothing changed).
- [x] 7 tests green; total 38/38.
- [ ] Cron entry — defer until Phase 6 / wire-up.

**Acceptance pending live run:** after a Researcher topic ingest, run Brain; verify `brain/memory.md` synthesizes cross-concept observations and `brain/questions.md` lists identified gaps with `Q-YYYY-MM-DD-NNN` IDs.

---

## Phase 4 — Graph + retrieval menu ✅ (build)

- [x] **Spec deviation:** SQL-direct networkx builder instead of safishamsi/graphify (rationale in `medbrain/graph/__init__.py`).
- [x] Graph builder + communities + audit; artifacts in `brain/graph/*.json`.
- [x] Graphify agent + `scripts/graphify_run.py`.
- [x] FastAPI server (`medbrain/api/server.py`) on 127.0.0.1:7117; no auth (v1).
- [x] All 8 menu primitives per spec §9.
- [x] JSON envelope per spec §9.
- [x] `derivative_included` flag in envelope (false by default; reserved for Phase 5).
- [x] 14 tests green.

**Acceptance met (in tests):** `lookup`, `neighborhood`, `path`, `community`, `scoped` (region/pregnancy/setting/certainty/current), `recent`, `gaps`, `evidence_pack` all return valid envelopes; contradiction detection surfaces in `gaps`.

---

## Phase 5 — Dream agent: weekly compaction + derivative ✅ (build)

- [x] Dream agent script: `python scripts/dream.py` with `--check`/`--force`/`--dry-run`/`--skip`/`--cadence-days`/`--keep-snapshots`.
- [x] **Spec deviation, documented:** snapshot-dir rollback (`brain/.dream-snapshots/<ts>/`), not git branch. Rationale: `brain/` is gitignored per README — nested git repo just for rollback adds infra without buying anything snapshot dirs don't. GC bounded by `keep_snapshots`.
- [x] Compaction prompt + per-file LLM rewriter with citation-set gate (rejects drops/adds).
- [x] Derivative generators (flashcards, mnemonics, analogies, gaps) into `brain/derivative/<type>/<slug>.md`.
- [x] Salience decay: per-entity (Salience.grace_score), 6mo idle threshold, 0.1 decay step, archive at ≤ 0.3.
- [x] Archive: claims dumped to `brain/archive/claims_<ts>.jsonl` then DELETEd from claims + EvidenceLedger + Salience.
- [x] Retrieval API wired: `lookup`/`neighborhood`/`evidence_pack` call `decay.touch()` to bump `last_accessed`.
- [x] DreamRun SQL table tracks each pass (snapshot_path, counts, restored flag, error).
- [x] 18 tests green; total 70/70.
- [ ] Cron / Task Scheduler entry — README documents recipes; user installs.

**Acceptance pending live run:** dream run on real corpus produces compacted .md files (verifiably smaller, citations preserved); derivative/ populated; archive/ contains decayed entities.

---

## Phase 6 — Active learning loop ✅ (build)

- [x] `medbrain/agents/active_learner.py`: `pick_next()` (priority asc, created asc), `run_once()`, `run_batch()`.
- [x] Picks top open question, atomic-flips `open → in_progress`, hands `Q.body` to existing `Researcher.ingest_topic()`.
- [x] Two-step lifecycle: active learner = "I tried"; Brain agent (next run) judges resolution.
- [x] `prompts/brain_questions.md` extended with explicit in_progress evaluation rules — Brain LLM now flips `in_progress → resolved` only when new evidence convincingly answers the specific question.
- [x] `scripts/active_learner.py` CLI: `--max N`, `--dry-run`, `--no-regen`, `--check`.
- [x] 9 tests green; total 79/79.

**Acceptance pending live run:** Brain emits a gap → `python scripts/active_learner.py` → status flips to in_progress, ingest runs → next `python scripts/brain.py` → Brain judges resolution and flips to resolved.

---

## Phase 7 — End-to-end validation corpus ✅ (build)

- [x] **Spec deviation, documented:** topic-driven corpus instead of pre-baked PMID list. `corpus/topics.json` defines 17 topics across all required categories (rct, cohort, case_report, contradicting, geographic, pediatric, adult, pregnancy, guideline_proxy). The Researcher's PubMed planner discovers actual PMIDs at run time. Acceptance retargeted from "exactly these 50 PMIDs" to "≥ 50 distinct PMIDs landed AND every category covered" — fairer to the topic-driven architecture and avoids fabricating PMIDs we can't verify.
- [x] WHO doc trio: deferred (blocked on Phase 1.5). `corpus/who_docs.md` documents the planned trio + workaround (T17 IDSA society guideline ingested via existing PubMed path exercises the `recommends` predicate flag).
- [x] 10 CDS sample queries: `corpus/cds_queries.json` — every retrieval primitive (lookup/neighborhood/path/community/scoped/recent/gaps/evidence_pack) hit at least once, geo + pregnancy + certainty filters exercised.
- [x] Threshold knobs: `corpus/thresholds.json` — 6 knobs (3 in StopCriteria, 3 in salience decay) with sweep ranges, success metrics, and source-of-truth pointers.
- [x] Orchestrator: `scripts/phase7_run.py` — ingest → graphify → brain → CDS queries → `brain/phase7_report.md` with category coverage + acceptance verdict + per-query envelope excerpts. Flags: `--skip-ingest`, `--queries-only`, `--no-brain`, `--no-regen`, `--topics`, `--dry-run`.
- [x] Standalone harnesses: `scripts/phase7_query.py` (CDS pack only), `scripts/phase7_tune.py` (sensitivity report on current corpus).
- [x] 6 tests green; total 85/85.

**Acceptance pending live run:** `python scripts/phase7_run.py` end-to-end emits `brain/phase7_report.md` with `overall_pass: True` (≥ 50 PMIDs, all 8 primitives ok, contradictions surfaced in `gaps`, current/superseded flags accurate in `evidence_pack`). Costs LLM tokens — drive via codex skill.
