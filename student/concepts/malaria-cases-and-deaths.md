---
type: medication
drug_class: not-applicable
tags: [malaria/epidemiology, india/spatial-ecology]
evidence_grade_max: expert_opinion
claim_count: 3
last_regen: 2026-05-13T19:06:12.947251+00:00
---

# Malaria cases and deaths

**Therapeutic category:** _Not a medication — epidemiologic outcome entity._
**Drug group:** _N/A_
**Drug class:** _N/A_
**Controlled substance:** _N/A_

## Overview

"Malaria cases and deaths" not drug. Outcome variable in spatiotemporal epidemiology. Current claim corpus link three ecological/demographic correlates in [[india]] endemic [[community-setting]]: [[scheduled-tribe-population]] proportion, annual rainfall, forest cover. Note misclassified as medication — flag for retype to `epidemiologic_outcome` or `condition`.

## Indication (Why is this medication prescribed?)

_Not applicable — entity is disease burden, not therapeutic agent._

## Mechanism of Action (How does it work?)

_Not applicable._ Ecological correlates only (pending review):

- [[scheduled-tribe-population]] proportion co-occurs spatially with malaria cases and deaths in India endemic community settings, with socioeconomic-disadvantage comorbidity qualifier [c:3910f2bc] (pending review).
- Annual rainfall co-occurs spatially with malaria cases and deaths in India endemic community settings [c:e8c175ab] (pending review).
- [[forest-cover]] co-occurs spatially with malaria cases and deaths in India endemic community settings [c:5682d19a] (pending review).

## Dosage and Administration

_No dose claims in current corpus._

## Contraindications (When not to use it)

_Not applicable._

## Warnings and Precautions

- Entity-type mismatch: tagged `medication` but corpus describes outcome variable. Re-classify before downstream export.
- All three claims `expert_opinion` grade, `low` certainty, `pending_review` — do not load-bear policy.
- Effect-size metric stated as "spatial correlation" but value/CI null across all claims [c:3910f2bc][c:e8c175ab][c:5682d19a].

## Side Effects

_Not applicable._

## Drug Interactions

_Not applicable._

## Storage and Stability

_Not applicable._

---
*Last regenerated: 2026-05-13T19:06:12.947251+00:00. Source claims: 3. Evidence mix: 3 expert_opinion (all pending review, single PMID:38772359).*
