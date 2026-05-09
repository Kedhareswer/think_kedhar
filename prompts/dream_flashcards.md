# Dream — flashcards for one entity

Generate spaced-repetition flashcards for a clinical entity from its claim set.

## Inputs

- Entity name + concept_md (existing concept synthesis)
- List of claims, each with id + subject/predicate/object + qualifiers + evidence_grade

## Output — strict JSON only

```json
{
  "cards": [
    {
      "front": "<question, ≤120 chars>",
      "back": "<answer, ≤200 chars> [c:<claim_id>]",
      "tags": ["<tag>", "..."]
    }
  ]
}
```

## Rules

1. One card per non-trivial claim. Skip claims that are stubs or restate other claims.
2. Front MUST be a single question. Back MUST cite the source claim id with `[c:<id>]`.
3. Cap at 20 cards per entity. Pick the highest-evidence-grade claims first if you must trim.
4. Tags: lowercase, hyphenated, drawn from predicate + qualifiers (e.g. `treats`, `pregnancy-safe`, `region-mekong`, `evidence-rct`).
5. No card may invent a fact. If unsure, omit.
6. JSON only. No prose, no fences around the whole reply.
