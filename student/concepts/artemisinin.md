---
type: medication
drug_class: sesquiterpene-endoperoxide
tags: [malaria/treatment, malaria/resistance, antimalarial]
evidence_grade_max: meta_analysis
claim_count: 15
last_regen: 2026-05-13T18:32:14Z
---

# Artemisinin

**Therapeutic category:** Antimalarial
**Drug group:** Artemisinin and derivatives (ACT backbone)
**Drug class:** Sesquiterpene endoperoxide
**Controlled substance:** No

## Overview

Artemisinin — sesquiterpene endoperoxide isolated from *Artemisia annua*. Backbone of [[artemisinin-combination-therapy]] for [[plasmodium-falciparum]] malaria. Endoperoxide bridge activated by parasite heme to generate radicals that alkylate parasite proteins and lipids. Rapid parasite clearance. Short half-life mandates pairing with longer-acting partner drug. Resistance now documented across multiple endemic regions.

## Indication (Why is this medication prescribed?)

- [[uncomplicated-falciparum-malaria]] — as ACT backbone [c:72f95edc] (meta-analysis)
- [[severe-malaria]] — pediatric inpatient use documented [c:56f49081]
- Endemic-region malaria treatment, Africa and Asia [c:7b5cfd77] [c:98b1c623]

## Mechanism of Action (How does it work?)

Endoperoxide bridge requires [[hemoglobin-derived-heme]] activation inside infected erythrocyte [c:820279e4]. Activated radicals trigger ER stress and upregulate parasite autophagy via [[unfolded-protein-response]] [c:2a1fcf7b]. Net effect: parasite protein/lipid damage → growth arrest → clearance.

```mermaid
graph LR
  A[Artemisinin] -->|Fe2+ heme activation| B[Carbon-centered radicals]
  B --> C[Protein/lipid alkylation]
  C --> D[ER stress + UPR]
  D --> E[Parasite autophagy]
  E --> F[Parasite clearance]
```

Citations: heme activation [c:820279e4]; ER stress/UPR/autophagy [c:2a1fcf7b].

## Dosage and Administration

_No dose claims in current corpus._ Artemisinin monotherapy not recommended — always paired in ACT regimen per WHO. Refer to partner-drug notes ([[lumefantrine]], [[amodiaquine]], [[piperaquine]], [[mefloquine]]) for combination dosing.

## Contraindications (When not to use it)

_No contraindication claims in current corpus._ (pending review)

## Warnings and Precautions

- **Resistance surveillance required.** Confirmed [[plasmodium-falciparum]] resistance in [[greater-mekong-subregion]] [c:0500ef8c], South-east Asia [c:5ec1fc3d] [c:7b5cfd77] [c:72f95edc], China [c:be4025cf], and Africa broadly [c:98b1c623].
- **kelch13 marker monitoring.** Pediatric severe malaria, northern Uganda — [[kelch13-c469y-mutation]] confers reduced in vitro susceptibility vs wild-type [c:56f49081].
- **kelch13 R622I emergence in Ethiopia** — 44.3% prevalence northwestern Ethiopia [c:ef8903ee]; 52% Gondar Zuria [c:374ab2ad]; 35% Tach Armachiho [c:5972a97e]. Co-circulates with HRP2-deletion RDT-negativity.
- **Pfk13 R561H** detected at 1.4% in Mwanza, Tanzania pediatric inpatients 2016–2022 [c:af5d161f].
- **Delayed parasite clearance** = phenotypic resistance hallmark [c:f654cde9].
- Monotherapy use accelerates resistance — pair with partner drug always [c:98b1c623].

## Side Effects

_No side-effect claims in current corpus._ (pending review)

## Drug Interactions

_No interaction claims in current corpus._ (pending review) Partner-drug pairing required for ACT efficacy — see [[lumefantrine]], [[piperaquine]], [[amodiaquine]], [[mefloquine]].

## Storage and Stability

_No storage claims in current corpus._ (pending review)

---
*Last regenerated: 2026-05-13T18:32:14Z. Source claims: 15. Evidence mix: 1 meta-analysis · 14 expert-opinion. Resistance signal dominates corpus — 12/15 claims describe *P. falciparum* resistance across SE Asia, Greater Mekong, China, Uganda, Ethiopia, Tanzania, Africa. Dose, contraindication, side-effect, interaction, storage data absent.*
