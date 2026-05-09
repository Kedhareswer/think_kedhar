# Dream — knowledge gaps for one entity

Identify what is MISSING for this entity that a clinical decision-support consumer would expect to find.

## Inputs

- Entity + concept synthesis + claim set
- The audit summary (isolated nodes, low-grade-only, contradictions for this entity, if any)

## Output — strict JSON only

```json
{
  "gaps": [
    {
      "topic": "<short topic label>",
      "question": "<the unanswered clinical question>",
      "why_it_matters": "<one sentence>",
      "evidence_so_far": ["<claim_id>", "..."],
      "suggested_search": "<PubMed-style query string>"
    }
  ]
}
```

## Rules

1. A gap is a SPECIFIC missing fact, not "we should know more about X". Examples:
   - "no claim covers paediatric dosing"
   - "all evidence is in vitro; no clinical trial data"
   - "contradicting findings on resistance, no resolving study cited"
2. ≤ 10 gaps per entity. Order by clinical impact (highest first).
3. `evidence_so_far` lists existing claim_ids that motivate the gap (can be empty if the gap is total absence).
4. Do not duplicate gaps already tracked in questions.md if Q-IDs are provided in the input — flag those as `existing_qid` instead of new gap.
5. JSON only.
