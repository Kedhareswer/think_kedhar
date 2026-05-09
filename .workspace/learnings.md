# Learnings

Short observations gathered during build. Stuff future-you would want to know but won't be in the spec.

Categories:
- **Prompt** — what worked / didn't for LLM extraction or synthesis.
- **Parser** — quirks in PubMed XML, WHO PDFs, etc.
- **Perf** — bottlenecks, batch sizes, costs.
- **Tooling** — graphify gotchas, SDK behaviors, library versions.
- **Data** — patterns observed in the malaria corpus.

---

## 2026-05-01

- **Tooling:** Python 3.12.9 on the dev box. SQLAlchemy 2.0 typed `Mapped[]` style works clean.
- **Tooling:** `datetime.utcnow()` is deprecated in 3.12 — use `datetime.now(UTC)` from the start.
- **Tooling:** `pip install -e ".[dev]"` from project root works fine on Windows; no `uv` needed yet.
- **Pattern:** SQLAlchemy `SAEnum` stores enum values as strings; `pytest` reads them back as the enum class. Don't compare against raw strings in tests, use the enum members.
- **Pattern:** Test fixture must `importlib.reload(config_mod, db_mod)` after monkeypatching `BRAIN_DIR` because `engine` is module-level. Acceptable for v1; if it bites, move engine creation behind a factory.
- **REVERSED:** LLM backend is Claude CLI subprocess, not anthropic SDK. User correction. Claude Max subscription, no API key. Reserves option of letting agents use Claude Code's full toolset later (web fetch, file ops) without rewiring.
- **Tooling:** `shutil.which("claude")` resolves to `claude.cmd` (npm-installed) on Windows; `subprocess.run(..., shell=False)` works fine with the resolved path. Don't need `shell=True` if you resolve the executable explicitly.
- **Pattern:** Strip `CLAUDECODE`, `CLAUDE_CODE_*`, `ANTHROPIC_API_KEY` env vars before spawning a nested `claude` subprocess. Inherited env vars cause the inner CLI to think it's running inside another session and behave weirdly.
- **Resolved:** Package manager = pip + venv, not uv. Cross-platform, no extra install step.
- **Parser:** PubMed publication-type lists are noisy — "Journal Article" appears alongside the real type. Mapper picks the strongest grade across the whole list rather than first-match.
- **Parser:** `Phase I` clinical trials are early-stage and not really RCTs; mapper grades them as `cohort` for safety.
- **Pattern:** Novelty dedup key includes `region`, `endemic_status`, `pregnancy` because these are the qualifiers that most often distinguish "same finding restated" from "new news in different population." Skipping `dose_regimen` from the key — different doses of the same drug on the same population is usually a different claim worth keeping separately, but doses vary too much for stable equality.
- **Pattern:** Contradictions never auto-promote. `_OPPOSING` map is conservative (treats↔causes, prevents↔causes, recommends↔contraindicates) — false positives are cheap (sit in review queue), false negatives are expensive (poison brain).
- **Pattern:** Extractor module skips malformed claims rather than failing the whole batch. Per-paper run can ingest 4 of 5 valid claims if one is bad JSON.
- **Pattern:** `populated_count()` is a soft signal, not a hard requirement — if a paper genuinely has no qualifiers (a generic mechanism claim), it lands in pending_review rather than getting force-promoted.
- **REVERSED:** PMID is NOT the input. Topic is. PMID is an internal unit. The Researcher agent decomposes broad topics into PubMed search plans, ingests top hits per query, and uses a saturation-window heuristic (last N papers' duplicate ratio) to stop early. Global paper cap prevents runaway research on "very_broad" topics.
- **Pattern:** Saturation detection uses inserted+duplicates from the last N StudentResults. Empty window (all 0/0) returns saturated=True so we don't loop forever on a query that finds nothing extractable.
- **Pattern:** Planner LLM has 4 scope tiers (very_broad / broad / focused / specific) with explicit guidance on max_papers and decomposition depth per tier. Prevents the LLM from either under-scoping a vague request or over-scoping a precise one.
- **Pattern:** Topic derivation is rule-based (predicate → topic bucket), not LLM-based. Cheap, deterministic, debuggable. If the rule produces wrong groupings in practice, swap to an LLM classifier later — schema doesn't change.
- **Pattern:** Regen runs at the END of a Researcher session, not per-paper. 10 papers about chloroquine = 1 chloroquine.md rewrite, not 10. Keeps LLM cost roughly proportional to topic count, not paper count.
- **Tooling/Pytest:** Modules that capture `BRAIN_DIR` at import time (e.g. `from medbrain.config import CONCEPTS_DIR`) break test fixtures that monkeypatch BRAIN_DIR + reload config. Fix: import the namespace (`from medbrain import config`) and reference `config.CONCEPTS_DIR` at call-time.
- **Tooling/Pytest:** pytest's `tmp_path` fixture occasionally fails on Windows with `PermissionError` on the `pytest-of-suhai` baseid (stale handles or perms from prior runs). Workaround: use `tempfile.mkdtemp(prefix=...)` directly in the test if `tmp_path` errors out.
- **Pattern:** Atomic write is `path.with_suffix(path.suffix + ".tmp")` then `os.replace`. On Windows `os.replace` is atomic and works across filesystems on the same volume — no extra effort needed.
- **Pattern:** questions.md uses stable IDs `Q-YYYY-MM-DD-NNN`. Lets Brain re-emit the same question to update priority/status without losing `created` timestamp. Avoids duplicate-question pile-up.
- **Pattern:** Brain emits a JSON delta (`new_questions[]` + `updates[]`), NOT a full file rewrite. Memory.md is full-rewrite, questions.md is delta-merge. Different shapes for different content lifecycles — memory is a snapshot, questions are a queue.
- **Pattern:** Brain's "what changed since last run" is filesystem mtime vs `BrainRun.completed_at` — not a dirty_tracker query. Decoupled from Student's dirty_tracker on purpose: Brain can run after Dream rewrites or manual edits, picks up everything it should.
- **Pattern:** Brain short-circuits to zero LLM calls when no .md files changed. Hourly cron with quiet hours = nearly-free no-op.
- **Pattern:** `_render_files` packs concept/note bodies into one prompt with `## path\n\n<content>\n\n---\n\n` delimiters. LLM sees both file path (for citing) and full body. Works fine up to ~50 concepts in current context windows.
- **DEVIATION from spec §7.3:** Graphify (safishamsi/graphify) was specced as the graph builder. Replaced with SQL-direct networkx because (1) graphify operates on prose and would lose structured qualifiers/grades/supersession on round-trip, (2) the user's `/graphify` is a Claude Code skill (not a Python lib) — can't `import`, (3) deterministic + zero external runtime dep + qualifier-preserving. Documented in `medbrain/graph/__init__.py`. Output shape stays graphify-compatible so menu primitives are stable across builder swaps.
- **Pattern:** Graph nodes use lowercased entity text as key, preserve original casing in `label` attr. Lets ingest-time variations ("P. falciparum" vs "P falciparum") collapse if normalization improves later, while UI/display keeps the source form.
- **Pattern:** All 8 menu primitives return the same envelope `{version, primitive, args, data, derivative_included, generated_at}`. Lets the CDS write one parser. Schema can evolve additively without breaking consumers.
- **Pattern:** Contradiction detection in audit uses opposing predicate pairs on the SAME (subject, object). Catches "AL treats falciparum" vs "AL causes falciparum" cleanly. Doesn't catch population-scoped contradictions yet (e.g., "drug X works in adults" vs "drug X fails in pediatrics") — that's a v2 enhancement requiring qualifier-aware comparison.
- **Pattern:** Multigraph (MultiDiGraph) lets multiple edges between same node pair when claims have different qualifiers. Important — a drug may "treat" a disease in 5 different populations as 5 different rows; collapsing to one edge loses scope info.
- **Decision:** Default API on 127.0.0.1:7117 (no auth). v1 assumes trusted local consumer. Authn deferred to v2 — would slot in as FastAPI middleware.
