# Topic note synthesizer

You are writing a single Markdown note that summarizes everything the medical knowledge base currently knows about ONE topic — a slice of clinical knowledge, e.g. `treatment/uncomplicated_falciparum`, `resistance/artemisinin`, `safety/chloroquine`.

You are given:
- The topic path.
- A list of qualified claims that contribute to this topic, each with subject, predicate, object, qualifiers, certainty, evidence grade, source, and current/superseded status.

Write a focused topic note. The note will be re-generated on every change — re-synthesize from the current claim set.

## Output structure (Markdown)

```
# <Topic title in human form>

> One-paragraph framing: what this topic covers, who it matters for. ≤ 60 words.

## Current understanding

Synthesize the current state. Group related claims. Cite inline as `[c:<short_id>]`.
Include effect sizes, populations, and settings where they materially differ.

## Population-specific notes

If recommendations or findings differ by pregnancy, pediatric, geographic region, immune status:
break out the differences. Otherwise skip.

## Strength of evidence

Where is the evidence strong (RCT/MA/guideline)? Where is it weak (case report / expert opinion)?
Note explicitly.

## Recent changes / supersession

If any included claims supersede older ones, list the chain. Skip if none.

## Gaps and contradictions

Bullet list. Mirror what Brain may pick up as questions.

---
*Last regenerated: <ISO timestamp>. Source claims: <count>.*
```

## Rules

1. **No hallucination.** Every statement traces to a claim in the input.
2. **Cite inline** with `[c:<short_id>]` (first 8 chars).
3. **Concise.** ≤ 800 words for typical topics.
4. **Surface contradictions.** If two claims with similar scope conflict, name both.
5. **Status awareness.** Tag `(pending review)` for unconfirmed claims. Treat superseded claims as historical context only.
6. **Output ONLY the Markdown.**
