# Dream — analogies for one entity

Build analogies that explain a clinical entity's mechanism, role, or behaviour by mapping it to a familiar non-medical system.

## Inputs

- Entity + concept synthesis
- Top-grade claims about mechanism, action, resistance, or interaction

## Output — strict JSON only

```json
{
  "analogies": [
    {
      "concept_being_explained": "<single sentence>",
      "analogy_domain": "<everyday system, e.g. 'lock and key', 'traffic intersection', 'smoke alarm'>",
      "mapping": [
        {"medical": "<medical element>", "everyday": "<analogue>", "evidence": "<claim_id>"}
      ],
      "where_it_breaks": "<one sentence — the limit of the analogy>"
    }
  ]
}
```

## Rules

1. ≤ 3 analogies per entity. Quality over quantity.
2. Every `evidence` id MUST be a real claim_id from the input.
3. `where_it_breaks` is mandatory — no analogy is perfect; naming the limit prevents misuse.
4. Skip analogies that require fabricating mechanism not in the claims.
5. If the entity has no mechanism-level claims, return `{"analogies": []}`.
6. JSON only.
