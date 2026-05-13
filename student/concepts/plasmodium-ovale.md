---
type: medication
drug_class: not-applicable-pathogen
tags: [malaria/etiology, parasitology]
evidence_grade_max: expert_opinion
claim_count: 4
last_regen: 2026-05-13T19:27:20Z
---

# Plasmodium ovale

**Therapeutic category:** _Not applicable — Plasmodium ovale is a protozoan parasite (etiologic agent), not a therapeutic agent._
**Drug group:** _Not applicable._
**Drug class:** _Not applicable._
**Controlled substance:** _Not applicable._

## Overview

Plasmodium ovale is a human malaria parasite [c:a80fd411] causing [[malaria]] in endemic settings [c:bba1d3b2]. Current claim corpus classifies it as a pathogen, not a medication. No pharmacologic claims (mechanism, dose, contraindication, interaction) exist. Note retained in medication schema per pipeline contract but every drug-specific field is null. For treatment of P. ovale infection, see notes on [[chloroquine]], [[artemisinin-combination-therapy]], and [[primaquine]] (radical cure of hypnozoites) — sourced from separate claim sets.

## Indication (Why is this medication prescribed?)

_Not applicable. P. ovale is not prescribed. It is an organism that causes disease:_

- Causes [[malaria]] in endemic settings [c:bba1d3b2] (pending review)
- Causes human malaria [c:a80fd411] (pending review)

## Mechanism of Action (How does it work?)

_No mechanism-of-action claims in current corpus._ P. ovale is a pathogen; "mechanism" would describe pathogenesis (hepatocyte infection, erythrocytic schizogony, hypnozoite dormancy) — not represented in current claims.

## Dosage and Administration

_No dose claims in current corpus._ Field not applicable — P. ovale is not administered.

## Contraindications (When not to use it)

_Not applicable._ No contraindication claims in current corpus.

## Warnings and Precautions

_No warning claims in current corpus._

Epidemiologic notes from corpus (not pharmacologic warnings):

- Co-occurs with [[plasmodium-vivax]] in endemic regions [c:e780c90c] (pending review, low certainty)
- Co-occurs with [[plasmodium-falciparum]] in endemic regions [c:36a8795a] (pending review, moderate certainty) — mixed infections complicate diagnosis and species-specific treatment selection

## Side Effects

_Not applicable._ P. ovale causes disease; it does not have side effects. Clinical manifestations of P. ovale infection (fever, hemolysis, splenomegaly, relapse from hypnozoites) belong in a disease note, not a medication note.

## Drug Interactions

_Not applicable._ No interaction claims in current corpus.

## Storage and Stability

_Not applicable._

---

## Classification flag

This entity (`Plasmodium ovale`) appears miscategorized as `medication`. All 4 source claims describe it as an etiologic agent of [[malaria]] [c:bba1d3b2][c:a80fd411] with epidemiologic co-occurrence with [[plasmodium-vivax]] [c:e780c90c] and [[plasmodium-falciparum]] [c:36a8795a]. Recommend reclassification to `pathogen` / `organism` and re-emit under disease/parasitology schema.

---
*Last regenerated: 2026-05-13T19:27:20Z. Source claims: 4. Evidence mix: 4 expert_opinion. All claims pending review.*
