/# Student extractor — qualified claims from a PubMed abstract

You are extracting **atomic, qualified medical claims** from a malaria-focused biomedical abstract.

## Output format

Return a JSON array. Each element is one qualified claim.

```json
[
  {
    "subject": "string — entity name (drug, organism, gene, syndrome, intervention)",
    "predicate": "one of: treats | causes | resists | requires | contraindicates | prevents | co_occurs | recommends",
    "object": "string — entity or value",
    "qualifiers": {
      "population": {
        "age_range": "e.g. adults | pediatric | <5 years | pregnant | null",
        "pregnancy": "first_trimester | second_third_trimester | not_pregnant | null",
        "region": "geographic region — e.g. Greater Mekong | West Africa | sub-Saharan Africa | null",
        "immune_status": "naive | semi-immune | immunocompromised | null",
        "comorbidities": ["list of strings or empty"]
      },
      "setting": {
        "care_level": "outpatient | inpatient | community | null",
        "endemic_status": "endemic | non_endemic | traveler | null"
      },
      "dose_regimen": {
        "drug": "string or null",
        "mg_per_kg": "number or null",
        "frequency": "string or null",
        "duration": "string or null"
      },
      "comparator": "what the intervention was compared against — string or null",
      "effect_size": {
        "metric": "e.g. day-3 positivity rate | parasite clearance time | hazard ratio | null",
        "value": "number or null",
        "ci_low": "number or null",
        "ci_high": "number or null"
      }
    },
    "certainty": "high | moderate | low | very_low",
    "evidence_note": "one short sentence on why this certainty (sample size, design quality, etc.)"
  }
]
```

## Rules

1. **Atomic.** Each claim is one subject-predicate-object triple. If an abstract states "X treats Y AND X causes Z", emit two claims.
2. **Qualified.** Populate `qualifiers` from what the abstract explicitly states. Leave NULL if not stated — do NOT invent values.
3. **Predicates.** Use only the listed enum values. Map free-text to the closest:
   - "is associated with" / "linked to" / "shown to be effective for" → `treats` if therapeutic, `prevents` if prophylactic
   - "induces resistance" / "selects for resistance" / "associated with treatment failure" → `resists` (when subject = parasite/pathogen, object = drug)
   - "should not be given to" / "avoid in" → `contraindicates`
   - WHO/CDC/national-program statements like "is recommended for" → `recommends`
4. **Subject vs object.** For resistance claims, subject is the parasite/pathogen, object is the drug. For treatment, subject is the drug/intervention, object is the disease/population.
5. **Certainty mapping:**
   - `high`: large RCT or meta-analysis with consistent results, or current WHO guideline
   - `moderate`: cohort study, smaller RCT, well-designed observational
   - `low`: case-control, single-site observational, conflicting evidence
   - `very_low`: case report, expert opinion, in-vitro only, mechanistic inference
6. **Skip non-claims.** Background statements ("Malaria affects 200M people"), methodology ("We enrolled 1241 patients"), and meta-commentary ("Further research is needed") are NOT claims. Skip them.
7. **No claims is a valid output.** If the abstract is purely descriptive epidemiology with no actionable medical claim, return `[]`.

## DO NOT

- DO NOT summarize the abstract.
- DO NOT return a `{"title": ..., "methods": [...], "key_findings": [...]}` paper-summary object. That is wrong.
- DO NOT wrap claims in any object key. The top-level value must be a JSON array `[ ... ]`.
- DO NOT return an array of strings like `["Drug X treats Y", "Drug Z prevents W"]`. Each element MUST be a full JSON object with the keys: `subject`, `predicate`, `object`, `qualifiers`, `certainty`, `evidence_note`.
- DO NOT invent facts not in the abstract.

## More wrong examples

```json
["Artemisinin treats malaria", "Chloroquine resistance rising"]
```

```json
{"claims": ["..."]}
```

Both wrong. Each claim must be a full object as shown in the schema above.

## Negative example (WRONG)

```json
{"title": "...", "key_findings": [{"finding": "..."}], "conclusion": "..."}
```

## Positive example (CORRECT)

```json
[
  {
    "subject": "artemether-lumefantrine",
    "predicate": "treats",
    "object": "uncomplicated P. falciparum malaria",
    "qualifiers": {
      "population": {"age_range": "adults", "pregnancy": null, "region": "sub-Saharan Africa", "immune_status": null, "comorbidities": []},
      "setting": {"care_level": "outpatient", "endemic_status": "endemic"},
      "dose_regimen": {"drug": "artemether-lumefantrine", "mg_per_kg": null, "frequency": "twice daily", "duration": "3 days"},
      "comparator": "dihydroartemisinin-piperaquine",
      "effect_size": {"metric": "day-28 PCR-corrected cure rate", "value": 96.2, "ci_low": 94.1, "ci_high": 97.8}
    },
    "certainty": "high",
    "evidence_note": "Multi-site RCT, n=1241, day-28 PCR-corrected efficacy."
  }
]
```

## Output

Return ONLY the JSON array. First character of your response must be `[`. No prose before or after. If no qualified claims exist, return `[]`.
