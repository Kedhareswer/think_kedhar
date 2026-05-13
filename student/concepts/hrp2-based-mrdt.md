---
type: medication
drug_class: malaria-rapid-diagnostic-test
tags: [malaria/diagnosis, malaria/falciparum]
evidence_grade_max: expert_opinion
claim_count: 3
last_regen: 2026-05-13T18:53:24.437224+00:00
---

# HRP2-based mRDT

**Therapeutic category:** Diagnostic — malaria rapid test
**Drug group:** Antigen-detection lateral-flow immunoassay
**Drug class:** Histidine-rich protein 2 (HRP2) antigen capture
**Controlled substance:** No

## Overview

HRP2-based mRDT = lateral-flow immunoassay detect *Plasmodium falciparum* histidine-rich protein 2 antigen in finger-prick blood. Point-of-care diagnostic, no lab needed. Used [[falciparum-malaria]] case detection in [[endemic-settings]]. Not a therapeutic — diagnostic device. Dose/pharmacology sections N/A.

## Indication (Why is this medication prescribed?)

- Diagnose [[plasmodium-falciparum-infection]] at community care level vs alternative antigen-based RDTs [c:552da9fe] (pending review)
- Diagnose [[severe-falciparum-malaria]] inpatient, endemic setting [c:d1a2e02e] (pending review)
- Detect [[submicroscopic-falciparum-malaria]] vs [[microscopy]] comparator, endemic setting [c:a721209a] (pending review)

## Mechanism of Action (How does it work?)

Monoclonal antibody on nitrocellulose strip bind HRP2 antigen from lysed *P. falciparum*-infected erythrocytes. Antigen-antibody complex migrate via capillary action, visualize on test line [c:552da9fe].

```mermaid
flowchart LR
  A[Finger-prick blood] --> B[RBC lysis buffer]
  B --> C[HRP2 antigen released]
  C --> D[Capture antibody binds HRP2]
  D --> E[Visible test line]
  E --> F[Clinical Pf diagnosis]
```

[c:552da9fe]

## Dosage and Administration

_No dose claims in current corpus._ Diagnostic device — single-use cassette, per manufacturer IFU.

## Contraindications (When not to use it)

_No contraindication claims in current corpus._

## Warnings and Precautions

- Caveats around HRP2 detection performance flagged in source [c:d1a2e02e] [c:a721209a] (pending review) — interpret with clinical context.
- Submicroscopic infection detection vs microscopy is qualifier-dependent; sensitivity not quantified in current claims [c:a721209a] (pending review).

## Side Effects

N/A — in-vitro diagnostic device, no patient pharmacological exposure.

## Drug Interactions

_No interaction claims in current corpus._

## Storage and Stability

_No storage claims in current corpus._ Follow manufacturer IFU.

---
*Last regenerated: 2026-05-13T18:53:24.437224+00:00. Source claims: 3. Evidence mix: 3 expert_opinion (all pending review).*
