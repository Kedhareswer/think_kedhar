---
type: medication
drug_class: vector-control-insecticide
tags: [malaria/prevention, vector-control/indoor-residual-spraying]
evidence_grade_max: meta_analysis
claim_count: 2
last_regen: 2026-05-13T19:28:54Z
---

# Indoor Residual Spraying Insecticides (IRS)

**Therapeutic category:** Vector-control insecticide (malaria prevention)
**Drug group:** Indoor residual spraying agents
**Drug class:** Pyrethroid-like (DDT, deltamethrin) and non-pyrethroid-like (carbamates, organophosphates)
**Controlled substance:** No (regulated pesticide; WHO PQ-listed)

## Overview

Indoor residual spraying applies long-acting insecticide to interior wall surfaces of dwellings to kill resting *Anopheles* mosquitoes. Deployed adjunct to [[insecticide-treated-nets]] in [[sub-saharan-africa]] for [[falciparum-malaria]] control. Efficacy on [[plasmodium-parasite-prevalence]] depends on chemical class and local pyrethroid-resistance status.

## Indication (Why is this medication prescribed?)

- Reduction of [[plasmodium-parasite-prevalence]] in endemic community settings already covered by [[insecticide-treated-nets]] — non-pyrethroid-like agents only [c:b8dc9e27] *(pending review)*
- Pyrethroid-like IRS layered on ITNs: no added benefit on parasite prevalence vs ITNs alone [c:dcd2688e]

## Mechanism of Action (How does it work?)

Contact neurotoxicity on resting adult *Anopheles*. Pyrethroid-likes ([[ddt]], [[deltamethrin]]) — sodium-channel modulators; cross-resistance with ITN pyrethroids blunts marginal effect when ITNs present [c:dcd2688e]. Non-pyrethroid-likes ([[bendiocarb]], [[pirimiphos-methyl]], [[propoxur]]) — acetylcholinesterase inhibitors; distinct target site bypasses pyrethroid resistance, restoring vector kill on top of ITNs [c:b8dc9e27].

```mermaid
flowchart LR
  A[Non-pyrethroid IRS on walls] --> B[AChE inhibition in resting Anopheles]
  B --> C[Vector mortality + reduced biting]
  C --> D[↓ Plasmodium parasite prevalence vs ITNs alone]
```
Mechanism-to-outcome chain supported by [c:b8dc9e27].

## Dosage and Administration

_No dose claims in current corpus._ Drug-level mg/kg, spray concentration, cycle frequency, residual duration — not present in claim set. Refer WHO PQ specs before deployment.

| Agent | Class | Use context |
|---|---|---|
| [[ddt]], [[deltamethrin]] | Pyrethroid-like | Community + ITN co-deployment, sub-Saharan Africa [c:dcd2688e] |
| [[bendiocarb]], [[pirimiphos-methyl]], [[propoxur]] | Non-pyrethroid-like | Community + ITN co-deployment, sub-Saharan Africa [c:b8dc9e27] |

## Contraindications (When not to use it)

_No contraindication claims in current corpus._

## Warnings and Precautions

- Pyrethroid-like IRS layered on ITNs shows no parasite-prevalence reduction (RR 1.11, 95% CI 0.86–1.44) — likely cross-resistance; not recommended where ITN coverage already high [c:dcd2688e]
- Non-pyrethroid claim status: *pending review* — confirm before policy use [c:b8dc9e27]

## Side Effects

_No adverse-event claims in current corpus._

## Drug Interactions

- **Co-intervention with [[insecticide-treated-nets]]:** non-pyrethroid-like IRS ↓ parasite prevalence (RR 0.61, 95% CI 0.42–0.88) vs ITNs alone — additive vector control [c:b8dc9e27]
- **Co-intervention with [[insecticide-treated-nets]]:** pyrethroid-like IRS — null effect vs ITNs alone (RR 1.11, 95% CI 0.86–1.44) — antagonism via shared resistance pathway [c:dcd2688e]

## Storage and Stability

_No storage claims in current corpus._

---
*Last regenerated: 2026-05-13T19:28:54Z. Source claims: 2. Evidence mix: 2 meta_analysis (1 auto-promoted, 1 pending review).*
