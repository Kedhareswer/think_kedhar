# Phase 7 — End-to-End Validation Report

- Started:   `2026-05-04T13:02:27.673766+00:00`
- Completed: `2026-05-04T13:05:44.887712+00:00`
- Overall:   **FAIL**

## Acceptance verdict
- `pmid_target_met`: **False**
- `category_coverage_met`: **False**
- `queries_all_passed`: **True**
- `overall_pass`: **False**

## Coverage
- distinct PMIDs ingested: **0** (target ≥ 50)
- categories_seen: `{}`
- categories_missing: `['rct', 'cohort', 'case_report', 'contradicting', 'geographic', 'pediatric', 'adult', 'pregnancy', 'guideline_proxy']`

## Topic outcomes
| id | category | topic | papers | claims | dupes | error |
|---|---|---|---:|---:|---:|---|
| T01 | rct | artemisinin-based combination therapy versus chloroquine for uncomplicated ma... | 0 | 0 | 0 | `LLMError: Planner returned invalid plan: 2 validation errors for ResearchPlan
scope
  Field required [type=missing, input_value={'topic': 'Artemisinin-Ba...obally for falciparum.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.13/v/missing
queries
  Field required [type=missing, input_value={'topic': 'Artemisinin-Ba...obally for falciparum.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.13/v/missing` |
| T08 | contradicting | hydroxychloroquine for covid-19 efficacy contradictory evidence | 0 | 0 | 0 | `LLMError: Planner returned invalid plan: 2 validation errors for ResearchPlan
scope
  Field required [type=missing, input_value={'topic': 'Hydroxychloroq...ection harder to land.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.13/v/missing
queries
  Field required [type=missing, input_value={'topic': 'Hydroxychloroq...ection harder to land.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.13/v/missing` |
| T15 | pregnancy | intermittent preventive treatment of malaria in pregnancy sulfadoxine-pyrimet... | 0 | 0 | 0 | `LLMError: Planner returned invalid plan: 2 validation errors for ResearchPlan
scope
  Field required [type=missing, input_value={'topic': 'Intermittent P...firmation for IPTp use'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.13/v/missing
queries
  Field required [type=missing, input_value={'topic': 'Intermittent P...firmation for IPTp use'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.13/v/missing` |

## CDS query outcomes
| id | primitive | ok | ms | summary |
|---|---|---|---:|---|
| Q01 | lookup | yes | 11 | node=no neighbors=0 |
| Q02 | lookup | yes | 11 | node=no neighbors=0 |
| Q03 | neighborhood | yes | 4 | nodes=0 edges=0 |
| Q04 | path | yes | 0 | paths=0 |
| Q05 | scoped | yes | 0 | nodes=0 edges=0 |
| Q06 | scoped | yes | 0 | nodes=0 edges=0 |
| Q07 | recent | yes | 0 | nodes=0 edges=0 |
| Q08 | gaps | yes | 1 | contradictions=0 questions_md_chars=87 |
| Q09 | evidence_pack | yes | 3 | claims=0 with_source=0 |
| Q10 | community | yes | 0 | present=no members=0 |

## CDS query envelope excerpts
### Q01 — `lookup` args=`{"entity": "artemisinin"}`
```json
{
  "primitive": "lookup",
  "args": {
    "entity": "artemisinin"
  },
  "derivative_included": false,
  "node_present": false,
  "neighbors_count": 0,
  "edges_count": 0
}
```

### Q02 — `lookup` args=`{"entity": "chloroquine"}`
```json
{
  "primitive": "lookup",
  "args": {
    "entity": "chloroquine"
  },
  "derivative_included": false,
  "node_present": false,
  "neighbors_count": 0,
  "edges_count": 0
}
```

### Q03 — `neighborhood` args=`{"entity": "malaria", "hops": 2}`
```json
{
  "primitive": "neighborhood",
  "args": {
    "entity": "malaria",
    "hops": 2
  },
  "derivative_included": false,
  "nodes_count": 0,
  "edges_count": 0
}
```

### Q04 — `path` args=`{"from": "chloroquine", "to": "resistance", "max_paths": 3}`
```json
{
  "primitive": "path",
  "args": {
    "from": "chloroquine",
    "to": "resistance"
  },
  "derivative_included": false,
  "paths_count": 0
}
```

### Q05 — `scoped` args=`{"population_region": "Greater Mekong", "min_certainty": "high", "current_only": true}`
```json
{
  "primitive": "scoped",
  "args": {
    "population_region": "Greater Mekong",
    "population_pregnancy": null,
    "setting_endemic": null,
    "setting_care_level": null,
    "min_certainty": "high",
    "current_only": true
  },
  "derivative_included": false,
  "nodes_count": 0,
  "edges_count": 0
}
```

### Q06 — `scoped` args=`{"population_pregnancy": "safe", "current_only": true}`
```json
{
  "primitive": "scoped",
  "args": {
    "population_region": null,
    "population_pregnancy": "safe",
    "setting_endemic": null,
    "setting_care_level": null,
    "min_certainty": null,
    "current_only": true
  },
  "derivative_included": false,
  "nodes_count": 0,
  "edges_count": 0
}
```

### Q07 — `recent` args=`{"since": "2020"}`
```json
{
  "primitive": "recent",
  "args": {
    "since": "2020"
  },
  "derivative_included": false,
  "nodes_count": 0,
  "edges_count": 0
}
```

### Q08 — `gaps` args=`{}`
```json
{
  "primitive": "gaps",
  "args": {},
  "derivative_included": false,
  "audit_keys": [
    "contradictions",
    "isolated",
    "low_grade_only",
    "stub_entities"
  ],
  "contradictions_count": 0,
  "isolated_count": 0
}
```

### Q09 — `evidence_pack` args=`{"claim_ids_from": "auto_top_n_high_grade", "n": 10, "resolved_claim_ids": []}`
```json
{
  "primitive": "evidence_pack",
  "args": {
    "claim_ids": []
  },
  "derivative_included": false,
  "claims_count": 0,
  "claims_with_source": 0,
  "claims_current": 0
}
```

### Q10 — `community` args=`{"topic": "malaria"}`
```json
{
  "primitive": "community",
  "args": {
    "community_id": null,
    "topic": "malaria"
  },
  "derivative_included": false,
  "community_present": false,
  "members_count": 0
}
```
