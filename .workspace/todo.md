# TODO

Concrete next actions. Smallest unit of work. Check off as completed.

---

## Phase 1 — Ingestion primitives ✅ (build complete, live ingest pending)

Done:
- [x] LLM wrapper (Claude CLI subprocess), PubMed fetcher (`efetch` + `esearch`), pub-type→grade mapper, extractor prompt, pydantic schema, novelty gate, Student per-PMID agent.
- [x] Researcher agent: topic → plan (scope/decomposition/queries) → search → ingest loop with saturation early-stop + global paper cap.
- [x] CLI rewire: `student.py "<topic>"` is the production path; `ingest_pmid.py` is debug.
- [x] 20 unit tests green.

Live-ingest todo (user runs):
- [ ] Verify Claude CLI on PATH: `claude --version`.
- [ ] `python scripts/student.py --plan-only "what is malaria"` — inspect plan first.
- [ ] `python scripts/student.py "artemisinin resistance in pregnancy"` — focused topic.
- [ ] `python scripts/student.py "what is malaria"` — broad topic, expects decomposition.
- [ ] Inspect `brain/brain.db`: claims table populated, statuses correct, multiple sources per topic.

## Phase 1.5 — WHO PDF ingestion (deferred)

- [ ] WHO fetcher + pypdf parser.
- [ ] Adapter so existing extractor handles guideline-style prose (predicate=`recommends`).

## Phase 2 — Student concepts/notes regeneration ✅ (build)

Done:
- [x] Slug, atomic write, predicate→topic mapper, concept + topic LLM prompts, regenerators, coordinator, Student/Researcher hooks, standalone `scripts/regen.py`. 11 tests green.

Live-test todo (user runs):
- [ ] `python scripts/student.py "vaginal yeast infection treatment"` (focused topic, ~10-20 papers).
- [ ] Inspect `brain/concepts/*.md` — should see one .md per entity touched, cited synthesis inline.
- [ ] Inspect `brain/notes/treatment/*.md` — topic notes synthesized from claims.
- [ ] Verify `dirty_tracker` shows all rows with `processed_at` populated post-run.

## Phase 3 — Brain agent ✅ (build)

Done:
- [x] BrainRun SQL table; questions_io parser/serializer/merger; synth + gap prompts; brain agent; CLI; 7 tests green.

Live-test todo (user runs):
- [ ] Run Researcher first to populate concepts/notes: `python scripts/student.py "<topic>"`.
- [ ] Then run Brain: `python scripts/brain.py --full` (first time) or `python scripts/brain.py` (incremental).
- [ ] Inspect `brain/memory.md` — should have themes + cross-concept observations.
- [ ] Inspect `brain/questions.md` — should have priority-sorted Q-IDs.
- [ ] Re-run Brain without changes — should report 0 reads, no LLM cost.

## Phase 4 — Graph + retrieval menu ✅ (build)

Done:
- [x] SQL-direct networkx graph builder (deviation from spec graphify; documented).
- [x] Communities (greedy modularity); audit (isolated/low-grade/stub/contradictions).
- [x] `scripts/graphify_run.py` rebuilds artifacts to `brain/graph/`.
- [x] FastAPI server with all 8 primitives; `scripts/api.py` runs on 127.0.0.1:7117.
- [x] 14 new tests green; total 52/52.

Live-test todo (user runs):
- [ ] `python scripts/student.py "<topic>"` — populate claims first.
- [ ] `python scripts/graphify_run.py` — build graph artifacts.
- [ ] `python scripts/api.py` — start API server (background or new shell).
- [ ] `curl 'http://127.0.0.1:7117/lookup?entity=chloroquine'` — sanity.
- [ ] `curl 'http://127.0.0.1:7117/scoped?population_region=Greater%20Mekong&min_certainty=high'` — filter test.
- [ ] `curl 'http://127.0.0.1:7117/gaps'` — see contradictions + questions.

## Phase 5 — Dream agent ✅ (build complete, live run pending)

Done:
- [x] `prompts/dream_compact.md` + 4 derivative prompts (flashcards, mnemonics, analogies, gaps).
- [x] `medbrain/dream/{snapshot,compactor,derivative,decay}.py`.
- [x] `medbrain/agents/dream.py` orchestrator with snapshot-rollback (deviation from spec git-branch — see plan.md).
- [x] Salience decay (per-entity Salience.grace_score) → `brain/archive/claims_<ts>.jsonl`.
- [x] Retrieval API now bumps `Salience.last_accessed` via `decay.touch()`.
- [x] DreamRun SQL table.
- [x] `scripts/dream.py` with `--check`/`--force`/`--dry-run`/`--skip`/`--cadence-days`/`--keep-snapshots`.
- [x] 18 tests green; total 70/70.

Live-test todo (user runs):
- [ ] `python scripts/student.py "<topic>"` — populate corpus first.
- [ ] `python scripts/dream.py --dry-run` — confirm intent, no mutations.
- [ ] `python scripts/dream.py --force` — first real run; inspect `brain/.dream-snapshots/`.
- [ ] `ls brain/derivative/{flashcards,mnemonics,analogies,gaps}/` — verify generated.
- [ ] Inspect compacted concepts/notes — file sizes should be smaller; all `[c:<id>]` preserved.
- [ ] `python scripts/dream.py --check` — should now exit 1 (not due).
- [ ] To exercise decay: manually backdate a Salience row's `last_accessed`, run again, verify archive.

## Phase 6 — Active learning loop ✅ (build complete, live run pending)

Done:
- [x] `medbrain/agents/active_learner.py` — pick + flip + delegate to Researcher.
- [x] `scripts/active_learner.py` CLI: `--max N`, `--dry-run`, `--no-regen`, `--check`.
- [x] `prompts/brain_questions.md` — Brain now evaluates in_progress questions for resolution.
- [x] No code change in `medbrain/agents/brain.py` needed: in_progress questions were already in the LLM context (filter is `status != "resolved"`).
- [x] 9 tests green; total 79/79.

Live-test todo (user runs):
- [ ] After Brain has emitted at least 1 open question:
- [ ] `python scripts/active_learner.py --check` — confirms top open question.
- [ ] `python scripts/active_learner.py --dry-run` — shows what would be picked.
- [ ] `python scripts/active_learner.py` — real run; picks top, flips to in_progress, ingests.
- [ ] Inspect `brain/questions.md` — Q is now `status: in_progress`, `updated:` set.
- [ ] `python scripts/brain.py` — re-synthesize; Brain LLM may flip to `resolved` if answer landed.
- [ ] Repeat with `--max 3` once flow is verified.

---

## Phase 7 — End-to-end validation corpus ✅ (build complete, live run pending)

Done:
- [x] `corpus/topics.json` — 17 topics across rct/cohort/case_report/contradicting/geographic/pediatric/adult/pregnancy/guideline_proxy.
- [x] `corpus/cds_queries.json` — 10 CDS-style queries hitting all 8 primitives.
- [x] `corpus/thresholds.json` — 6 tunable knobs (StopCriteria + salience decay) with sweep ranges + metrics.
- [x] `corpus/who_docs.md` — deferred plan (blocked on Phase 1.5 PDF fetcher; T17 IDSA proxy in PubMed path).
- [x] `scripts/phase7_run.py` — full pipeline orchestrator; emits `brain/phase7_report.md` with verdict.
- [x] `scripts/phase7_query.py` — CDS pack runner (no ingest).
- [x] `scripts/phase7_tune.py` — corpus-state sensitivity report.
- [x] 6 tests green; total 85/85.

Live-test todo (drive via codex skill):
- [ ] `python scripts/phase7_run.py --dry-run` — sanity (already verified).
- [ ] `python scripts/phase7_run.py` — full end-to-end (LLM-billed; ~17 topics × ~30 papers = up to 500 fetch+extract calls).
- [ ] Inspect `brain/phase7_report.md` — `overall_pass: True`?
- [ ] Inspect `brain/concepts/*.md`, `brain/notes/**/*.md`, `brain/memory.md`, `brain/questions.md` — populated and cited?
- [ ] `curl http://127.0.0.1:7117/gaps` (after `python scripts/api.py` in another shell) — contradictions from T08/T09 surfaced?
- [ ] `python scripts/phase7_tune.py` — post-run sensitivity table; tune defaults if a sweep value clearly wins.

## Open questions blocking work (`gaps.md`)

- ~~LLM library: `anthropic` SDK direct.~~ Resolved.
- ~~Package manager: `pip + venv`.~~ Resolved.
- Pin graphify to which commit? (Defer to Phase 4.)

---

## Done

- 2026-05-01: Phase 0 — skeleton, models, db, init script, smoke tests (3 green).
