# Dream — mnemonics for one entity

Produce memory aids tying together the most important grouped facts for an entity.

## Inputs

- Entity name
- Concept synthesis (concepts/<entity>.md)
- Claim set with predicates + qualifiers

## Output — strict JSON only

```json
{
  "mnemonics": [
    {
      "scope": "<short label, e.g. 'first-line antimalarials' or 'contraindications'>",
      "device": "<acronym | rhyme | sentence>",
      "expansion": "<each letter or phrase mapped to its referent, with [c:<id>] citations>",
      "evidence": ["<claim_id>", "..."]
    }
  ]
}
```

## Rules

1. ≤ 5 mnemonics per entity. Each must cover ≥ 2 claims.
2. Acronym mnemonics: each letter MUST map to a real entity / drug / step from the claims.
3. Every claim referenced in `expansion` or `evidence` must exist in the input.
4. No mnemonic for trivia (single-claim entities, dose-only facts).
5. If no group of ≥ 2 related claims exists, return `{"mnemonics": []}`.
6. JSON only. No prose, no fences around the whole reply.
