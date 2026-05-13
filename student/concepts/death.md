---
type: medication
drug_class: not-applicable-entity-is-outcome
tags: [malaria/mortality, malaria/pediatric, malaria/treatment]
evidence_grade_max: meta_analysis
claim_count: 10
last_regen: 2026-05-13T18:44:47Z
---

# Death (entity mis-classified as medication)

**Therapeutic category:** _Not applicable — "death" is a clinical outcome, not a drug._
**Drug group:** _Not applicable._
**Drug class:** _Not applicable._
**Controlled substance:** _Not applicable._

## Overview

Entity "death" routed to medication template by classifier error. Claim corpus describes death as mortality outcome of [[malaria]], [[cerebral-malaria]], [[plasmodium-knowlesi-malaria]], [[plasmodium-vivax-malaria]], and [[hiv-aids]] — not pharmacology of a therapeutic agent. Note preserved for traceability; recommend re-route to disease/outcome template.

## Indication (Why is this medication prescribed?)

_No indication claims — entity is an outcome, not a therapy._

## Mechanism of Action (How does it work?)

_No mechanism-of-action claims. Causal drivers of mortality in corpus:_
- [[cerebral-malaria]] → pediatric mortality, case-fatality 16.7% inpatient endemic settings [c:def21fb4] (pending review).
- [[plasmodium-knowlesi-malaria]] with delayed IV antimalarial therapy → 35.5% of fatal adult cases in Southeast Asia tied to treatment delay [c:93d72be2] (pending review, meta_analysis).
- Recurrent and chronic [[plasmodium-vivax]] infection → mortality in pediatric and <5 yr populations [c:a371cec5][c:ba8a9f67] (pending review).
- [[hiv-aids]] → 5× rise in mortality incidence Chinese children/adolescents 6–22 yr 2011–2017 [c:e55f7c4b] (pending review).

## Dosage and Administration

_No dose claims in current corpus._

## Contraindications (When not to use it)

_Not applicable._

## Warnings and Precautions

Mortality burden flags (population-qualified):
- Children <5 yr, sub-Saharan Africa: 67% of 409,000 global malaria deaths 2019 [c:5c75235f] (meta_analysis, pending review).
- Global pediatric <5 yr endemic: ~405,000 annual malaria deaths 2018 [c:df2b4d9e] (pending review).
- UK travelers (imported [[malaria]]): 2–11 deaths/year [c:57848b90] (pending review).
- US travelers: case-fatality 0.3% [c:d81551c5] (pending review).
- Treatment delay in [[plasmodium-knowlesi-malaria]] adults Southeast Asia: load-bearing driver of fatality [c:93d72be2].

## Side Effects

_Not applicable — entity is outcome, not exposure._

## Drug Interactions

_No interaction claims. One treatment-timing signal:_
- Prompt antimalarial treatment ↓ mortality in children <5 yr, sub-Saharan Africa, vs delayed/no treatment [c:1160c9bf] (pending review).

## Storage and Stability

_Not applicable._

---
*Last regenerated: 2026-05-13T18:44:47Z. Source claims: 10. Evidence mix: 2 meta_analysis · 8 expert_opinion. **Classifier flag:** entity "death" is an outcome — recommend re-route to disease/outcome note schema.*
