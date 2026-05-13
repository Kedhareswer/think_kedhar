# Concept note — Medication (Master-sheet Medications aligned)

You are writing a single Markdown note about ONE medication (drug, biologic, or therapeutic agent). The headings match the Master-sheet "Medications" columns so an exporter can lift each section into the corresponding cell.

You are given:
- The drug name (generic).
- A list of qualified claims about this drug, with predicate, qualifiers, certainty, evidence grade, source, and current/superseded status.

Write a focused medication note. Re-synthesize from the current claim set on every regeneration.

## Output structure

```
# <Generic name>

**Therapeutic category:** <e.g. Antimalarial>
**Drug group:** <e.g. Artemisinin combination therapy>
**Drug class:** <e.g. Sesquiterpene endoperoxide>
**Controlled substance:** <Yes — Schedule X · No>

## Overview

≤ 80 words plain-language description.

## Indication (Why is this medication prescribed?)

Bullet list of conditions/uses. Cite inline.

## Mechanism of Action (How does it work?)

Short paragraph. Cite mechanism claims explicitly.

## Dosage and Administration

Table or bullet list, organised by indication and population (adult / pediatric / pregnancy / renal-adjusted). Include dose, route, frequency, duration. Only state what claims support — never invent a dose.

## Contraindications (When not to use it)

Bullet list. Distinguish absolute from relative.

## Warnings and Precautions

Bullet list of black-box warnings, severe precautions, monitoring requirements.

## Side Effects

Bullet list grouped by frequency (common / serious / rare). Flag the ones with mortality risk.

## Drug Interactions

Bullet list. For each interaction, state effect direction (↑/↓ exposure, additive toxicity, etc.) and severity.

## Storage and Stability

Short paragraph or bullet list.

---
*Last regenerated: <ISO timestamp>. Source claims: <count>. Evidence mix: <e.g. 6 RCT · 4 guideline · 2 cohort>.*
```

## Rules

1. **Dose safety first.** If no claim supports a dose, write `_No dose claims in current corpus._` rather than guess. This is a hard constraint.
2. **No hallucination** (fact-checker). Every statement traces to a claim_id; disagreements flagged with both ids.
3. **Cite inline** (academic-researcher). `[c:<8char-claim-id>]` after each statement. Note evidence_grade when load-bearing.
4. **Concision** (technical-writer). ≤ 800 words total.
5. **Population qualifiers are load-bearing.** Always preserve population/setting qualifiers when surfacing dose, contraindication, or warning claims.
6. **Brand names and prices** are out of scope for this note — they live in the Master sheet's per-country columns and are sourced separately.
7. **Status awareness.** `(pending review)` inline for non-promoted; supersedence by replacement.
8. **Output ONLY the Markdown.** No code fences, no preamble, no postamble.
