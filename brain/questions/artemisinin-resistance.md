# Artemisinin Resistance — Questions Classifier (Answerable / Gaps)

**Topic:** Artemisinin resistance in *Plasmodium falciparum*
**Source base:** 52 concept + topic notes | **Date:** 2026-05-09

---

## ANSWERABLE

Questions the knowledge base can address with moderate–high confidence.

---

### Mechanism

| Question | Answer summary | Certainty | Source |
|---|---|---|---|
| What is the primary genetic driver of artemisinin partial resistance? | *pfkelch13* propeller domain point mutations | High | PMID:37269964, 38321292 |
| Which specific K13 variants are validated? | C580Y (GMS dominant), R539T, Y493H, I543T (SEA); R561H (Tanzania); A675V, C469Y (Uganda) | High | Multiple |
| How does K13 mutation confer resistance mechanistically? | K13 mutation → ↓ PfPI3K ubiquitination → ↑ PI3K stability → ↑ PI3P → autophagy-mediated ring-stage cytoprotection | Moderate | PMID:25874676, 40396048 |
| What role does hemoglobin endocytosis play? | Artemisinin activation requires heme from Hb digestion; K13 mutations reduce endocytosis → less heme → less drug activation | High | PMID:32905757 |
| Do background mutations amplify K13-mediated resistance? | Yes — arps10-V127M and fd-D193Y stack on C580Y to further increase RSA survival | Moderate | PMID:36303209 |
| What is the role of autophagy in resistance? | ART induces ER stress → UPR → autophagy upregulation; C580Y parasites exploit this as survival mechanism | Moderate | PMID:40396048 |
| Do pfcoronin mutations confer resistance independently of K13? | Yes — via actin-binding disruption → impaired ring-stage Hb endocytosis → heme limitation | Moderate | PMID:40964400 |
| Is there metabolic reprogramming in resistant parasites? | Yes — pentose phosphate and glycolytic pathway downregulation co-occur with resistance | Moderate | Meta-analysis |
| Do double K13 mutations threaten next-gen artemisinins? | Yes — C580Y+A212T and R539T+A212T confer resistance to OZ277 and OZ439 vs. single mutants | Moderate–High | PMID:41959371 |

---

### Epidemiology & Geography

| Question | Answer summary | Certainty | Source |
|---|---|---|---|
| Where did artemisinin resistance originate? | Greater Mekong Subregion (Cambodia, Thailand, Vietnam); C580Y clonal expansion | High | Multiple |
| Is resistance now present in Africa? | Yes — eastern Africa (Rwanda, Uganda, Horn of Africa, NW Tanzania) via independent emergence | High | PMID:38321292, 38552654 |
| Did African K13 variants come from SEA via importation? | No — independent de novo emergence; distinct mutations from SEA lineage | High | PMID:38321292 |
| Which African K13 mutations have confirmed positive selection? | A675V (s=0.237, CI excludes zero) and C469Y (s=0.383, CI excludes zero) in Uganda | High | PMID:40112841 |
| How does SEA selection pressure compare to Africa? | C580Y annual s=0.627 (higher point estimate) vs. Uganda 0.237–0.383; but SEA estimate has wider CI | Moderate | PMID:40112841 |
| Is partial resistance present outside SEA and Africa? | Yes — multicenter trial confirms it in Kenya, Peru, Thailand | High | PMID:40614930 |

---

### ACT Efficacy & Treatment Failure

| Question | Answer summary | Certainty | Source |
|---|---|---|---|
| Do K13 mutations reduce ACT efficacy? | Yes — prolongs parasite clearance half-life (mean 4.1 h vs. WT under artesunate in Thailand) | Moderate | PMID:40614930 |
| What causes ACT treatment failure mechanistically? | Artemisinin partial resistance + partner drug resistance co-occurring eliminates both components | High | PMID:37269964 |
| Which partner-drug resistance markers co-occur with ACT failure? | Pfmdr1 86Y/184F/1246Y (AL failure); Pfdhps 437G + Pfdhfr 51I/59R/108N (AS+SP failure); Pfcrt 76T (pan-ACT) | Moderate | PMID:33556786 |
| What is DHA-PPQ efficacy in Uganda children? | PCR-corrected 28-day efficacy 98.9–100% vs. AL 87.2–94.4% | High / Moderate | PMID:34952573 |
| Is DHA-PPQ resistance documented? | Yes — Cambodia *P. falciparum*; dual mechanism (plasmepsin II/III CNV + CRT mutations) | High | PMID:40720544 |
| What strategy is recommended against MDR *P. falciparum*? | Multiple first-line therapies in rotation + triple drug combination (TDC) therapy | Moderate | PMID:34267045 |
| Does ACT remain first-line for uncomplicated *P. falciparum*? | Yes globally; DHA-PPQ, AL, ASAQ are primary regimens | High | Multiple |
| Is IV artesunate still standard for severe malaria? | Yes — inpatient first-line; but ART-R emergence is qualifying caveat in Africa | High | PMID:38321292, 38552654 |

---

### Resistance Detection & Surveillance

| Question | Answer summary | Certainty | Source |
|---|---|---|---|
| What is the standard in-vitro resistance assay? | Ring-stage Survival Assay (RSA); flow cytometry-based RSA counts 250,000 erythrocytes | High | PMID:24867976 |
| Is there a better RSA variant for field use? | Extended recovery RSA (eRRSA) correlates with patient clearance half-life better than standard 6-hr RSA | Moderate | PMID:32005233, 39545737 |
| Does DHA IC50 correlate with RSA/eRRSA? | Yes — Spearman rs ~±0.42 with both assays (moderate, not strong) | Moderate | PMID:39545737 |
| Should surveillance track only K13 mutations? | No — partner drug markers and background mutations (arps10, fd) must be co-monitored | High | Multiple |
| What is pfpm2 CNV prevalence in southern Angola? | ~9.8% — low but non-negligible piperaquine resistance signal | Moderate | PMID:39794826 |
| What is pfmdr1 CNV prevalence in southern Angola? | ~8.9% — low lumefantrine/mefloquine resistance signal | Moderate | PMID:39794826 |

---

## GAPS

Questions the knowledge base **cannot adequately answer** — missing data, null effect sizes, or single-source expert opinion insufficient for clinical inference.

---

### Quantitative Effect Sizes (Critical Gap — Universal)

> **Gap 1:** No quantitative effect sizes (ORs, HRs, IC₅₀ fold-changes, RSA survival %, clearance half-life values with CIs) are captured across virtually any claim.
>
> - Cannot model ACT population-level efficacy decay
> - Cannot set molecular resistance thresholds for treatment switching
> - Cannot compare resistance magnitude across K13 alleles
> - All mechanistic claims qualitative only

**Unanswerable questions:**
- What RSA₀₋₃ₕ survival % does C580Y alone vs. C580Y+A212T produce?
- By how much does A675V reduce artemisinin susceptibility vs. wild-type?
- What is the clearance half-life delta between K13-mutant and WT in African high-transmission settings?
- What IC₅₀ fold-change does C101F confer for artemisinin vs. Dd2 background?

---

### Mechanistic Validation

| Gap question | Why unanswerable |
|---|---|
| Does autophagy upregulation causally drive resistance or is it a correlate? | In vitro only; UPR→autophagy→resistance chain not mechanistically closed; no ATG knockouts or UPR inhibitor data |
| What is the causal role of PI3P elevation in ring-stage survival — confirmed in field isolates? | Lab strains only; African isolate validation absent |
| Do reduced pentose phosphate/glycolytic pathways cause resistance or result from it? | Causal direction unconfirmed; meta-analytic association only |
| Is the pfcoronin + pfkelch13 heme-limitation convergence additive, synergistic, or epistatic? | Low certainty; no co-culture or genetic interaction data |
| What is MRT68921 (autophagy inhibitor) selectivity for parasite vs. mammalian ULK1/2? | Not addressed in any concept note |

---

### African Resistance Trajectory

| Gap question | Why unanswerable |
|---|---|
| What is the rate of K13 allele frequency increase in African populations over time? | No temporal trend data; Uganda sentinel sites showed 0% at single timepoint (low certainty) |
| Will African partial resistance progress to full treatment failure at current trajectory? | No modeling data for Africa resistance spread velocity |
| Is A675V or C469Y spreading clonally or arising independently at multiple foci? | Convergent vs. clonal expansion unresolved |
| What is C469F prevalence and selection trajectory? | CI crosses zero in current data; underpowered |

---

### Clinical Outcomes

| Gap question | Why unanswerable |
|---|---|
| What treatment failure rate corresponds to any specific K13 allele at population level? | Zero claims carry treatment failure rates linked to specific alleles |
| Does host immunity in high-transmission Africa mask clinical ART-R (delayed detection)? | Asserted as hypothesis; not quantified |
| What is the threshold K13 allele frequency at which WHO recommends ACT switch in Africa? | Not encoded; policy threshold absent from knowledge base |
| Does partial resistance reduce ACT efficacy enough to cause excess mortality? | No mortality data in any claim |

---

### Partner Drugs & Combination Strategies

| Gap question | Why unanswerable |
|---|---|
| Which specific drugs belong in triple drug combination (TDC) therapy? | Drugs unnamed in PMID:34267045 claims |
| Is A212T resistance to OZ277/OZ439 additive or synergistic with primary K13 allele? | Effect sizes null; mechanism uncharacterized |
| Does A212T alone confer ozonide resistance without a primary K13 mutation? | Unresolved; no data |
| What is the fitness cost of K13 double mutants (C580Y+A212T, R539T+A212T) — do they transmit efficiently? | Not reported |
| How does CRT mutation type interact with plasmepsin CNV in PPQ resistance — are they redundant or additive? | Paradox unresolved; mechanism unstudied in claims |

---

### Population-Specific Gaps

| Gap | Status |
|---|---|
| Pregnancy — artemisinin safety/efficacy in ART-R context | No pregnancy data across any claim |
| Pediatric dosing — mg/kg for any ACT regimen | Null across all claims |
| Immune status stratification | All population qualifiers null |
| Neonatal/infant-specific data | Absent |

---

### Pipeline / Novel Therapeutics

| Gap question | Why unanswerable |
|---|---|
| What is paclitaxel's therapeutic window for antiparasitic use given mammalian toxicity? | In silico only; no in vitro/in vivo data |
| Does MRT68921 have an acceptable safety profile for clinical development? | Not addressed |
| Can OZ439 be salvaged by partner drug optimization despite double K13 mutations? | No data |

---

## Summary Matrix

| Domain | Answerable | Gaps |
|---|---|---|
| Primary resistance mechanism (K13 → PI3P → autophagy) | ✓ Moderate–High | Effect sizes absent |
| K13 variant catalog (SEA + Africa) | ✓ High | Africa trajectory unquantified |
| Companion mutations (arps10, fd, pfcoronin) | ✓ Moderate | Causal roles unconfirmed in vivo |
| ACT first-line status | ✓ High | Dose regimens, comparators missing |
| Partner drug resistance markers | ✓ Moderate | No effect sizes; drug-specific gaps |
| Double K13 mutations vs. next-gen artemisinins | ✓ Moderate | Quantitative RSA/IC₅₀ absent |
| Piperaquine resistance mechanisms | ✓ High | Paradox unresolved; interaction unstudied |
| Clinical failure rates by allele | ✗ | Not in knowledge base |
| African resistance spread velocity | ✗ | No temporal modeling |
| Population subgroups (pregnancy, pediatric) | ✗ | Universally absent |
| Novel therapeutics (paclitaxel, MRT68921) | Partial (in silico) | No clinical-translatable data |

---

*Generated: 2026-05-09 | Base: 52 concept/topic notes | All claims status: pending_review*
