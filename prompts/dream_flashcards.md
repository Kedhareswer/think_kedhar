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

1. **One card per non-trivial claim.** Skip claims that are stubs or restate other claims.
2. **Active recall, not recognition.** Front MUST be a single question that requires retrieval — never "What is X?" with the entity itself as the answer. Prefer scenario-based questions ("First-line treatment for uncomplicated falciparum malaria in West Africa?").
3. **Cite the source.** Back MUST end with `[c:<claim_id>]`.
4. **Cap at 20 cards per entity.** Pick the highest-evidence-grade claims first if you must trim.
5. **Tags:** lowercase, hyphenated, drawn from predicate + qualifiers (e.g. `treats`, `pregnancy-safe`, `region-mekong`, `evidence-rct`).
6. **No card may invent a fact.** If unsure, omit. Cards are downstream of the concept note — they cannot be more confident than the underlying claim.
7. **JSON only.** No prose, no fences around the whole reply.

## Per-concept output path

Flashcards for entity `<slug>` are written to `student/flashcards/<slug>.md` so that the learner-centric view co-locates concept, notes, memory, and flashcards under the same key. This rendering is handled by the calling Python — you only return JSON.
