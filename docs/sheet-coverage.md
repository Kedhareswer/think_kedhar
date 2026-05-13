# Master sheet coverage — what's filled, what isn't, and why

The exporter mirrors `Master sheet.xlsx` exactly: nine sheets, identical column
headers, same order. Only **Conditions** is populated today. This file
explains the data path for every sheet so the gap is honest and actionable.

## Coverage matrix

| Sheet | Status | Rows | Why | What it needs |
|---|---|---|---|---|
| **Conditions** | ● populated | 8 | Existing malaria corpus has 8 condition-shaped concepts (severe falciparum, uncomplicated, MDR strains, etc.). LLM exporter writes reference-style prose for each. | More condition concepts via `python scripts/student.py "<condition>"` |
| **Medications** | ○ schema only | 0 | We have drug concepts (chloroquine, artemether-lumefantrine, artesunate, etc.) but the current claim set is resistance-research, not pharmacology. We don't carry `dose_regimen`, `contraindications`, `brand_names` per country. | Add a `_medications_rows()` builder + ingest WHO formulary papers that carry dose/safety qualifiers + run a per-country brand-name enrichment pass |
| **Lab tests** | ○ schema only | 0 | Corpus has zero claims about microscopy / RDT / PCR diagnostics. Resistance papers cite tests in passing but don't describe them. | Targeted ingestion of diagnostic-evaluation papers (e.g. *"rapid diagnostic test malaria sensitivity"*) + new `_lab_tests_rows()` builder |
| **RadiologyImaging** | ○ schema only | 0 | Outside the malaria scope. Malaria isn't imaging-driven. | Out of v1 scope. Would require a different specialty corpus. |
| **Special Diagnostic Studies** | ○ schema only | 0 | EKG / EEG / PFT — outside malaria scope. | Out of v1 scope. |
| **HistopathologyCytology** | ○ schema only | 0 | Biopsy / smear interpretation — outside malaria scope. Even thick/thin blood smear isn't carried as a structured claim. | Future work, would need a histopathology corpus. |
| **SurgeriesProcedures** | ○ schema only | 0 | No surgical procedure literature ingested. | Out of v1 scope. |
| **Provider type & Specialty** | ◐ directory data | 0 | This is NOT PubMed data. It's a directory of provider types and what services they render. | Needs a CSV import from MOH / professional council registries. |
| **Hospital Addressbook** | ◐ directory data | 0 | Same as above — not extractable from research literature. The reference sheet has 50,637 rows of Nigerian facilities. | Needs CSV import from Nigerian Federal Ministry of Health / DHIS2 / similar registry. Geocoding pass on lat/lng. |

Legend:
- **●** populated — corpus + builder both exist, rows are reviewer-ready
- **○** schema only — header row written, no data rows. Either the corpus is thin or the row builder isn't implemented yet
- **◐** directory data — not derivable from PubMed; needs a CSV import path

## What it would take to populate the remaining sheets

The work splits cleanly into three buckets:

### 1. Sheets blocked on corpus, not code (Medications, Lab tests)

These are within the medical-knowledge scope. The exporter just needs:
1. A row builder in `medbrain/exporters/master_sheet.py` (~80 lines each, mirrors `conditions_rows_llm` pattern)
2. A reference-style prompt at `prompts/master_sheet_<sheet>.md` (~80 lines each, mirrors `master_sheet_condition.md`)
3. Targeted Student runs to enrich the claim base for that domain. Suggested topics:
   - For Medications: *"artemether-lumefantrine pediatric dosing"*, *"chloroquine contraindications G6PD"*, *"WHO antimalarial formulary 2024"*
   - For Lab tests: *"rapid diagnostic test pfHRP2"*, *"malaria PCR sensitivity specificity"*, *"thin smear microscopy training"*

Estimate: half a day per sheet, including LLM export time.

### 2. Sheets out of malaria scope (Radiology / Special Diagnostics / Histopath / Surgeries)

These need a different specialty corpus. The architecture is topic-agnostic
(see `docs/superpowers/specs/2026-05-01-medbrain-design.md` §2) — repoint
Student at a different specialty (cardiology, oncology, etc.) and the same
flow produces those sheets for that specialty.

Estimate: phased per-specialty rollout. Each specialty is a multi-week
ingestion campaign.

### 3. Sheets that aren't research data (Providers, Hospitals)

These are operational reference data. The exporter needs a simple
CSV-loader path:

```python
def _hospitals_rows() -> Iterable[dict[str, str]]:
    csv_path = config.ROOT_DIR / "data" / "hospitals_ng.csv"
    if not csv_path.exists():
        return []
    with csv_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            yield {col: row.get(col, "") for col in HOSPITALS_COLS}
```

The data itself comes from:
- **Provider type & Specialty:** Nigerian Medical and Dental Council (NMDC) / MDCAN registries
- **Hospital Addressbook:** Federal Ministry of Health master facility list,
  DHIS2 exports, or a curated CSV maintained by the operations team. Reference
  sheet has 50,637 rows so the curation lift is significant.

Estimate: one engineer-day for the loader + however long it takes to source
the CSVs and clean column names.

## How to fill Conditions further (right now)

The Conditions sheet is the working example. To grow it from 8 → 30+ rows:

```bash
# Ingest broader condition coverage
python scripts/student.py "uncomplicated malaria treatment guidelines"
python scripts/student.py "cerebral malaria pathophysiology"
python scripts/student.py "placental malaria epidemiology"
python scripts/student.py "blackwater fever clinical features"
# … Brain auto-runs to update memory
# Then re-export with LLM-quality prose
python scripts/export_master_sheet.py --llm
```

Each Student run takes ~5-15 minutes (PubMed fetch + extraction +
regeneration). LLM export of an 8-condition corpus is ~2 minutes. Scaling
the corpus is the bottleneck, not the export.
