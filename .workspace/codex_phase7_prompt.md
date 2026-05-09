Project: MedBrain (no-git directory)
Working directory: d:/MedBrain

Files in scope:
- scripts/phase7_run.py
- scripts/phase7_query.py
- scripts/phase7_tune.py
- corpus/topics.json
- corpus/cds_queries.json
- corpus/thresholds.json
- corpus/who_docs.md
- tests/test_phase7.py
- brain/ (output target)

---
IMPORTANT: Work only with the local files listed above. Do not search the web. Use the project's .venv: d:/MedBrain/.venv/Scripts/python.exe (Windows). The LLM backend is the Claude Code CLI (claude.cmd on PATH); no ANTHROPIC_API_KEY is required.
---

TASK: Drive a real Phase 7 SMOKE validation run for MedBrain.

Steps (do all, in order):

1. Pre-flight checks
   - Run: .venv/Scripts/python.exe -m pytest -q tests/test_phase7.py
     Expect 6 passed. If not, STOP and print failures.
   - Run: claude.cmd --version
     Expect a version string (e.g. "2.1.88 (Claude Code)"). If it fails, STOP and surface stderr.
   - Skip the ANTHROPIC_API_KEY check; the project does not need one.

2. Initialize DB if missing
   - If brain/brain.db absent, run: .venv/Scripts/python.exe scripts/init_db.py

3. Smoke validation run (LIMITED to 3 topics)
   - Run: .venv/Scripts/python.exe scripts/phase7_run.py --topics T01,T08,T15 2>&1 | tee brain/phase7_smoke.log
   - This ingests 3 topics covering: RCT (T01 artemisinin vs chloroquine), contradicting evidence (T08 hydroxychloroquine for COVID), and pregnancy (T15 IPTp).
   - Expect runner to: ingest -> graphify -> run brain -> run 10 CDS queries -> write brain/phase7_report.md.
   - Each topic does N PubMed fetches + N LLM extract/synth calls; expect 10-20 minutes total.

4. Inspect the report
   - Read brain/phase7_report.md. Surface in your response:
     - The acceptance verdict block (overall_pass and the 4 sub-flags)
     - The category coverage line (distinct PMIDs, categories_seen, categories_missing)
     - The CDS query outcomes table (all 10 rows)
   - Note: distinct_pmids will be < 50 in smoke mode -- that is expected. The interesting verdicts are queries_all_passed and category_coverage_met for the 3 categories we covered.

5. Sensitivity probe
   - Run: .venv/Scripts/python.exe scripts/phase7_tune.py
   - Surface the corpus snapshot + the salience.archive_floor row.

6. Final summary file
   - Write a concise summary to brain/phase7_codex_summary.md with:
     - Pre-flight results
     - Topics actually ingested (id, papers, claims)
     - Verdict block from the report
     - Any failed CDS queries with the error message verbatim
     - 1-3 follow-ups (e.g., missing categories, knobs to retune, next-step commands)

Constraints:
- Do not modify scripts/, corpus/, tests/, or medbrain/ files. Read-only on those.
- You MAY create or modify files under brain/ and .workspace/ only.
- If a step fails, do not paper over -- stop, surface the exact stderr, and write the partial summary.
- Hard wall-clock budget: 25 minutes. If approaching it, stop after the current topic and write the summary anyway.
