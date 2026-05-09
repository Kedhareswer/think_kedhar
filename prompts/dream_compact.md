# Dream — compact a single Markdown file

You rewrite ONE Markdown file from MedBrain so it conveys the same medical information using fewer tokens.

## Hard rules — violation = rejection

1. **Citations MUST survive.** Every `[c:<id>]` token in the input MUST appear in your output, exactly once each, with the same id. Do not invent new citations. Do not delete any.
2. **No new claims.** Do not add facts not present in the input.
3. **No softening.** "first-line treatment" stays "first-line treatment", not "a treatment". Numerical doses, percentages, populations, and time windows are load-bearing — preserve them verbatim.
4. **Keep supersession trail.** If the input says claim X supersedes claim Y, the output must too.
5. **Keep contradictions visible.** If the input notes opposing findings, the output must too.

## What you SHOULD compress

- Throat-clearing prose ("It is worth noting that…", "Studies have shown…")
- Repeated entity names → use pronouns or anaphora when unambiguous
- Multi-sentence definitions that can become one
- Bullet lists with verbose lead-ins → tighter bullets
- Markdown headings deeper than H3 collapse upward unless they carry distinct meaning
- Trailing summary sections that just restate above

## What you must NOT compress

- The bibliography / sources block (last block of citations) — copy it verbatim
- Inline qualifier tags `(region: X, pregnancy: Y, certainty: Z)` — preserve exactly
- Code-fence blocks — copy verbatim

## Output format

Return ONLY the rewritten Markdown. No preamble, no commentary, no code fence around the whole thing. Output starts at the first character of the new file.

If the input is already maximally compact (you cannot reduce token count without violating a rule), return it unchanged.
