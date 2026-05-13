---
type: medication
drug_class: not-applicable
tags: [malaria/pregnancy, obstetrics/first-trimester]
evidence_grade_max: expert_opinion
claim_count: 2
last_regen: 2026-05-13T18:51:26Z
---

# First-Trimester Malaria Infection

**Therapeutic category:** _Not applicable — entity is a clinical condition, not a medication._
**Drug group:** _N/A_
**Drug class:** _N/A_
**Controlled substance:** _N/A_

## Overview

First-trimester malaria infection refers to *Plasmodium* infection during weeks 1–13 of pregnancy in endemic settings. Current claim corpus frames it as a risk exposure linked to adverse pregnancy outcomes [c:6cab89a1] [c:c9adccaf] (pending review). Entity classified upstream as `medication` but corpus content is condition-level — no pharmacologic data present.

## Indication (Why is this medication prescribed?)

_Not applicable. Entity is a condition, not a therapeutic agent. See [[malaria-in-pregnancy]], [[uncomplicated-falciparum-malaria]] for management entries._

## Mechanism of Action (How does it work?)

_No mechanism-of-action claims in current corpus._ Pathophysiology (placental sequestration, [[var2csa]]-mediated cytoadherence, maternal anemia) not represented in present claim set.

## Dosage and Administration

_No dose claims in current corpus._ Treatment regimens for [[malaria-in-pregnancy]] live on partner drug notes (e.g. [[quinine]], [[artemether-lumefantrine]]).

## Contraindications (When not to use it)

_Not applicable — condition, not drug._ For first-trimester antimalarial contraindications, see drug-specific notes.

## Warnings and Precautions

- First-trimester *Plasmodium* infection in endemic settings carries risk of adverse pregnancy outcomes [c:6cab89a1] [c:c9adccaf] (pending review, expert_opinion).
- Specific outcome categories (miscarriage, stillbirth, low birth weight, congenital infection) not enumerated in current claims — qualifier `object: "adverse pregnancy outcomes"` only.
- Both supporting claims share single source (PMID:35916532) — evidence base narrow.

## Side Effects

_Not applicable — condition, not drug._

## Drug Interactions

_No interaction claims in current corpus._

## Storage and Stability

_Not applicable._

---

## Data integrity flag

Entity-type classifier flagged this as `medication` but subject is clinical exposure. Recommend reclassification to `condition` or `exposure` and re-routing to appropriate template (obstetric-risk / disease-state). Both available claims are predicate `causes` → adverse pregnancy outcomes, evidence_grade `expert_opinion`, status `pending_review`, same source. Claims c9adccaf and 6cab89a1 are near-duplicates (differ only in `age_range` qualifier: `adults` vs null) — candidate for dedup.

---
*Last regenerated: 2026-05-13T18:51:26Z. Source claims: 2. Evidence mix: 2 expert_opinion (both pending review, single source PMID:35916532).*
