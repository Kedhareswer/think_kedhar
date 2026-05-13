---
type: medication
drug_class: not-applicable
tags: [malaria/prevention, vector-control]
evidence_grade_max: meta_analysis
claim_count: 2
last_regen: 2026-05-13T19:08:42Z
---

# Malaria parasitaemia

**Therapeutic category:** Not applicable — entity is a clinical finding, not a medication
**Drug group:** N/A
**Drug class:** N/A
**Controlled substance:** N/A

## Overview

Malaria parasitaemia = presence of *Plasmodium* parasites in peripheral blood. Not a drug. Current claim corpus describes vector-control interventions (indoor residual spraying, IRS) aimed at preventing parasitaemia in [[sub-saharan-africa]] communities already using [[insecticide-treated-nets]]. No pharmacologic agent claims present for this entity.

## Indication (Why is this medication prescribed?)

_Not applicable — entity is a disease state. Related preventive interventions in corpus:_
- IRS with pyrethroid-like insecticide ([[ddt]] or [[deltamethrin]]) added to ITNs for community-level prevention in sub-Saharan Africa [c:2bb1e5de]
- IRS with non-pyrethroid-like insecticide ([[bendiocarb]] or [[pirimiphos-methyl]]) added to ITNs, same setting (pending review) [c:1f74c617]

## Mechanism of Action (How does it work?)

_No drug mechanism applies._ Vector-control logic in claims: insecticide on indoor surfaces → kills/repels resting *Anopheles* mosquitoes → cuts human-vector contact → reduces parasite transmission. Not pharmacologic.

## Dosage and Administration

_No dose claims in current corpus._ Claims describe insecticide class (pyrethroid-like vs non-pyrethroid-like) but no mg/kg, frequency, or duration.

## Contraindications (When not to use it)

_No contraindication claims in current corpus._

## Warnings and Precautions

_No warning claims in current corpus._

## Side Effects

_No adverse-effect claims in current corpus._

## Drug Interactions

_No interaction claims in current corpus._

## Storage and Stability

_Not applicable._

## Efficacy signal (vector-control, not pharmacologic)

| Intervention | Comparator | RR parasite prevalence | 95% CI | Grade | Status |
|---|---|---|---|---|---|
| IRS pyrethroid-like + ITN | ITN alone | 1.11 | 0.86–1.44 | meta-analysis | auto-promoted [c:2bb1e5de] |
| IRS non-pyrethroid-like + ITN | ITN alone | 0.67 | 0.35–1.28 | meta-analysis | pending review [c:1f74c617] |

Both CIs cross 1.0 → no statistically significant benefit over ITN alone in cited Cochrane review (PMID:31120132). Pyrethroid-like point estimate suggests possible harm direction; non-pyrethroid-like trends toward benefit but low certainty.

## Note on entity classification

Classifier tagged "malaria parasitaemia" as `medication` — likely misclassification. Entity is a parasitologic finding (object of "prevents" predicate in both claims, never subject of a drug claim). Recommend reclassify to `condition` or `clinical_finding`. Drug-style sections left empty rather than fabricated.

---
*Last regenerated: 2026-05-13T19:08:42Z. Source claims: 2. Evidence mix: 2 meta-analysis (1 auto-promoted, 1 pending review).*
