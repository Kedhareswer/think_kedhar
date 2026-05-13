# Phase 7 — End-to-End Validation Report

- Started:   `2026-05-13T17:07:48.578180+00:00`
- Completed: `2026-05-13T17:07:48.578180+00:00`
- Overall:   **FAIL**

## Acceptance verdict
- `pmid_target_met`: **False**
- `category_coverage_met`: **False**
- `queries_all_passed`: **True**
- `overall_pass`: **False**

## Coverage
- distinct PMIDs ingested: **0** (target ≥ 50)
- categories_seen: `{'rct': 3}`
- categories_missing: `['cohort']`

## Topic outcomes
| id | category | topic | papers | claims | dupes | error |
|---|---|---|---:|---:|---:|---|
| T01 | rct | x | 3 | 5 | 0 |  |

## CDS query outcomes
| id | primitive | ok | ms | summary |
|---|---|---|---:|---|
| Q01 | lookup | yes | 4 | ok |

## CDS query envelope excerpts
### Q01 — `lookup` args=`{"entity": "x"}`
```json
{
  "primitive": "lookup"
}
```
