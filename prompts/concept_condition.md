# Concept note — Medical Condition (Master-sheet Conditions aligned)

You are writing a single Markdown note about ONE medical condition (disease, syndrome, infection, or clinical state). The headings below match the Master-sheet "Conditions" columns verbatim so an exporter can lift each section directly into the corresponding cell.

You are given:
- The condition name.
- A list of qualified claims about this condition (subject or object), with predicate, qualifiers, certainty, evidence grade, source, and current/superseded status.

Write a focused condition note. The note will be re-generated on every change; do not preserve old text — re-synthesize from the current claim set.

## Output structure

```
# <Condition name>

## Overview

One paragraph (≤ 80 words). What it is in clinical terms. Plain language. No jargon without a parenthetical gloss.

## Symptoms

Bullet list of cardinal symptoms. Group by typical vs. severe if relevant.

## When to See a Doctor

Bullet list of red flags / when to escalate. Write for a layperson reader.

## Causes

Bullet list or short paragraph. Aetiology — organisms, mutations, exposures, mechanisms. Cite inline.

## Risk Factors

Bullet list. Demographic, environmental, comorbidity-based. Separate modifiable from non-modifiable when the claim set supports it.

## Complications

Bullet list of downstream sequelae. Note severity / mortality where claims specify.

## Prevention

Bullet list. Vaccines, prophylaxis, behavioural interventions. Note evidence strength.

## Diagnosis

Bullet list of how it is identified — clinical signs, lab tests, imaging, biopsy. Include sensitivity/specificity if a claim provides it.

## Treatment

Bullet list of management lines. First-line, second-line, supportive. Include dose/regimen if a claim provides qualifiers. Flag drug interactions and contraindications.

## Outlook/Prognosis

One paragraph. Natural history, mortality with/without treatment, long-term sequelae. Anchor to evidence grade.

---
*Last regenerated: <ISO timestamp>. Source claims: <count>. Evidence mix: <e.g. 4 RCT · 8 cohort · 3 expert>.*
```

## Tables beat prose for comparisons (mandatory)

When the claim set carries three or more variants of the same kind — region × prevalence, drug × population × dose, first-line vs second-line treatments, age-banded recommendations — render them as a Markdown table. Clinicians scan tables; they read past prose lists.

Example for the **Treatment** section:

| Patient group | First line | Dose | Evidence |
|---|---|---|---|
| Adults, uncomplicated | Artemether-lumefantrine | 4 tabs ×2/day ×3d | RCT [c:1f5cbe2a] |
| Pregnant (2nd-3rd trim) | Artemether-lumefantrine | same as adult | WHO guideline [c:b8c12390] |
| Severe (any age) | IV Artesunate | 2.4 mg/kg q12h | Cochrane MA [c:7b2298f4] |

Keep tables under five columns (terminal-width safe). Cite the load-bearing claim inside the cell.

## Rules

1. **No hallucination** (fact-checker). Every statement traces to a claim_id. Disagreeing claims must be flagged with both ids.
2. **Cite inline** (academic-researcher). `[c:<8char-claim-id>]` after each statement. Note evidence_grade when it changes how the reader should weigh the statement.
3. **Concision** (technical-writer). ≤ 700 words total for typical conditions.
4. **Layperson + clinician** dual register. Define terms parenthetically the first time; afterwards use the term plainly.
5. **No prose-padding.** Skip a section entirely if no claims populate it — leave the heading with a single line: `_No claims in current corpus._`
6. **Status awareness.** `(pending review)` tag inline for non-promoted claims; supersedence handled by replacing the older claim entirely.
7. **Output ONLY the Markdown.** No code fences, no preamble, no postamble.
