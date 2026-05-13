---
type: medication
drug_class: vector-control-insecticide
tags: [malaria/prevention, malaria/vector-control, public-health/intervention]
evidence_grade_max: meta_analysis
claim_count: 16
last_regen: 2026-05-13T18:58:08Z
---

# Indoor Residual Spraying (IRS)

**Therapeutic category:** Malaria vector-control intervention
**Drug group:** Residual insecticide (applied to interior wall surfaces)
**Drug class:** Pyrethroid-like (DDT, deltamethrin) or non-pyrethroid-like (bendiocarb, pirimiphos-methyl, propoxur)
**Controlled substance:** No — programmatic public-health use under WHO PQ-listed insecticides

## Overview

IRS is application of long-acting insecticide to interior walls and ceilings of dwellings to kill resting endophilic *Anopheles* vectors. Deployed at community scale in [[malaria]]-endemic settings, alone or layered with [[insecticide-treated-nets]]. Effect depends on chemical class, vector resistance, and net coverage [c:0496d512] [c:016dcd00].

## Indication (Why is this medication prescribed?)

- Community-level prevention of [[malaria]] transmission in endemic [[sub-saharan-africa]] settings [c:0496d512] [c:016dcd00].
- Prevention of [[plasmodium-falciparum]] infection, 2–10 y children, sub-Saharan Africa [c:016dcd00].
- Reactive focal spraying near index cases for [[plasmodium-falciparum]] elimination, Namibia (pirimiphos-methyl) [c:fdda9571].
- Adjunct to LLINs in Jimma Zone, Ethiopia [c:781b1a95] (pending review).
- Reduce [[plasmodium]] parasite prevalence in ITN-using communities — non-pyrethroid IRS RR 0.61 (0.42–0.88), high-certainty meta-analysis [c:b8dc9e27].

## Mechanism of Action (How does it work?)

Residual insecticide deposited on wall surfaces contacts endophilic [[anopheles]] mosquitoes resting indoors after blood-feeding. Contact toxicity kills vector before sporogonic cycle completes, breaking human-mosquito-human transmission chain.

```mermaid
flowchart LR
    A[IRS deposit on wall] --> B[Resting Anopheles tarsal contact]
    B --> C[Insecticide uptake]
    C --> D[Vector mortality pre-sporogony]
    D --> E[Reduced entomological inoculation rate]
    E --> F[Lower parasite prevalence / incidence]
```

Mechanism inferred from population-level effect on parasite prevalence [c:b8dc9e27] and falciparum infection [c:016dcd00].

## Dosage and Administration

_No per-kg dose claims — IRS is environmental application, not patient dosing._ Chemical class and target structure from claims:

| Class | Agents (claim-supported) | Target | Setting |
|---|---|---|---|
| Pyrethroid-like | DDT, deltamethrin | Interior walls of dwellings | Community, sub-Saharan Africa [c:c0de6166] [c:2bb1e5de] [c:bc57bd82] |
| Non-pyrethroid-like (carbamate/OP) | bendiocarb, pirimiphos-methyl, propoxur | Interior walls of dwellings | Community, sub-Saharan Africa [c:037f304e] [c:f098b7ec] [c:1f74c617] [c:320e8c41] [c:f6af45c4] [c:b8dc9e27] |
| Organophosphate (focal/reactive) | pirimiphos-methyl | Index-case household + neighbours | Namibia, elimination phase [c:fdda9571] |

Spray frequency, dose per m², residual duration not in current claim corpus.

## Contraindications (When not to use it)

_No explicit contraindication claims in current corpus._ Programmatic exclusions (housing type, pyrethroid resistance) not represented.

## Warnings and Precautions

- Pyrethroid-like IRS layered on ITNs shows **no benefit** over ITNs alone — RR parasitaemia 1.11 (0.86–1.44) [c:2bb1e5de] [c:dcd2688e]; RR anaemia 1.12 (0.89–1.40) [c:c0de6166] [c:d61b7e6d]; rate ratio incidence 1.07 (0.80–1.43), pediatric [c:bc57bd82] [c:befd58d4]. Implies cross-resistance with pyrethroid-treated nets — choose non-pyrethroid class where ITNs already deployed.
- Insecticide resistance is decision driver; class rotation needed [c:781b1a95] (pending review).
- Non-pyrethroid IRS + ITN: parasite prevalence RR 0.61 (0.42–0.88), high certainty [c:b8dc9e27] — preferred chemistry in ITN-saturated areas.

## Side Effects

_No human safety/AE claims in current corpus._ Environmental and occupational toxicity profiles per chemical class not surfaced from these sources.

## Drug Interactions

Intervention-level interactions only (no pharmacologic DDIs):

- **[[insecticide-treated-nets]] (ITNs):** layering pyrethroid IRS adds no measurable benefit over ITNs alone across anaemia, parasitaemia, incidence [c:c0de6166] [c:2bb1e5de] [c:bc57bd82] [c:d61b7e6d] [c:dcd2688e] [c:befd58d4]. Non-pyrethroid IRS + ITN → ↓ parasite prevalence (RR 0.61) [c:b8dc9e27], trend ↓ anaemia (RR 0.71, 0.38–1.31) [c:320e8c41], ↓ incidence (rate ratio 0.86, 0.61–1.23) [c:f6af45c4], ↓ parasitaemia non-ITN-stratified (RR 0.67, 0.35–1.28) [c:1f74c617], ↓ anaemia non-ITN-stratified (RR 0.46, 0.18–1.20) [c:f098b7ec], pediatric incidence rate ratio 0.93 (0.46–1.86) [c:037f304e].
- **Reactive focal IRS + index-case response:** pirimiphos-methyl IRS near index cases reduces *P. falciparum* transmission vs no reactive intervention, Namibia, RCT [c:fdda9571].

## Storage and Stability

_No storage/stability claims in current corpus._ Residual duration on sprayed surfaces (typically 3–12 months by chemical class) not represented in source set.

---
*Last regenerated: 2026-05-13T18:58:08Z. Source claims: 16. Evidence mix: 12 meta_analysis · 3 expert_opinion · 1 RCT.*
