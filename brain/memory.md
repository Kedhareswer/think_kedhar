# MedBrain Brain — Cross-Concept Synthesis
*memory.md · Last updated 2026-05-09*

---

## 1. Core Resistance Architecture

### 1.1 Artemisinin Resistance — Two Convergent Mechanisms

Both pathways terminate at the same node: **reduced free heme → less ART activation → parasite ring-stage survival**.

```
PATHWAY A — Kelch13 (primary, high certainty)
K13 mutation (C580Y, R539T, Y493H, R561H, A675V, C469Y)
  → ↓ K13-mediated ubiquitination of PfPI3K
  → ↑ PfPI3K stability → ↑ PI3P
  → ↑ autophagy / UPR (ER stress response)
  → enhanced ring-stage proteostatic buffering
  → + ART-induced ER stress → UPR → further autophagy upregulation
  → parasite survives DHA pulse

PATHWAY B — Pfcoronin (secondary, moderate certainty)
Pfcoronin mutation (G50E, R100K, E107V)
  → impaired PfCoronin–PfActin interaction
  → PfCoronin loses ring-stage localization
  → impaired endocytosis
  → ↓ hemoglobin acquisition → ↓ free heme (Fe²⁺)
  → less ART endoperoxide bridge cleavage
  → reduced drug activation → resistance

CONVERGENCE POINT:
Both K13 (via hemoglobin endocytosis disruption) and Pfcoronin (via actin/endocytosis)
limit heme substrate. K13 additionally operates via PI3P/autophagy axis.
Convergence claim: low certainty — needs co-culture / genetic interaction studies.
```

**Key mechanistic dependencies:**
- Hemoglobin endocytosis required for both parasite growth AND artemisinin activation (PMID:32905757, high certainty)
- K13 C580Y → elevated PI3P → upregulated autophagy → MRT68921 (autophagy inhibitor) shows *lower* IC50 in resistant vs WT (synthetic lethality opportunity; in vitro only, no IC50 values)
- ART itself induces ER stress → UPR → autophagy upregulation; C580Y parasites exploit this as survival buffer

---

### 1.2 Resistance Amplifiers / Companion Mutations

Layer on top of primary K13 resistance:

| Mutation | Gene | Effect | Certainty | Evidence |
|----------|------|--------|-----------|---------|
| arps10-V127M | Apicoplast ribosomal protein S10 | Further ↑ RSA₀₋₃ₕ vs K13-C580Y alone | Moderate (low for GWAS) | Expert opinion |
| fd-D193Y | Ferredoxin | Additive with arps10-V127M on C580Y background | Moderate | Expert opinion |
| PfATG18 T38I | Autophagy-related protein 18 | Co-occurs with Y493H, R539T, C580Y in SEA field isolates | Moderate | Expert opinion |
| A212T (K13 second site) | Kelch13 | Amplifies OZ277 + OZ439 resistance on C580Y and R539T backgrounds | Moderate–High | Expert opinion |

**Critical pattern:** A212T is a **generalizable resistance amplifier** — it potentiates multiple primary K13 alleles (C580Y, R539T) against both conventional artemisinins AND next-gen ozonides (OZ277, OZ439). This is the most dangerous next-gen resistance signal currently in the evidence base.

---

### 1.3 Metabolic Reprogramming (Co-occurring, Causal Direction Unclear)

In resistant vs sensitive isolates (meta-analytic, moderate certainty):
- Pentose phosphate pathway downregulated
- Glycolytic pathway downregulated
- Ring-stage fatty acid metabolism ART-insensitive in C580Y mutants (multi-omics, PMID:37385107)

Interpretation: reduced glucose/ROS flux may lower hemoglobin digestion and ART activation — consistent with "quiescence" model. **Cause vs. consequence unresolved.**

---

## 2. Geographic Resistance Map

### 2.1 Artemisinin Partial Resistance (APR)

| Region | Status | Key K13 variants | Certainty | Notes |
|--------|--------|-----------------|-----------|-------|
| Greater Mekong Subregion (SEA) | Established, dominant | C580Y (dominant), R539T, Y493H | High | C580Y selection coefficient s=0.627 (CI crosses zero, moderate certainty) |
| Uganda | Emerging, confirmed | A675V (s=0.237, CI excludes zero), C469Y (s=0.383, CI excludes zero) | High | Independent emergence, not importation |
| Uganda | Emerging, uncertain | C469F (s=0.324, wide CI), P441L (s=0.494, wide CI) | Low | Underpowered — needs more temporal sampling |
| Rwanda, Horn of Africa | Emerging | Not specified in claims | High | Expert opinion |
| NW Tanzania | Confirmed | R561H | High | Dispensary-level surveillance, children 6–120mo |
| Sub-Saharan Africa + India | Circulating | F476I, R539T, Y561H | Moderate | Meta-analysis, 15 countries MalariaGEN |
| Kenya, Peru, Thailand | Confirmed clinical phenotype | Not specified | High | Multicenter trial, partial resistance confirmed |

**Independence of African emergence is established** (claim 1597e761 — African K13 variants arose independently of SEA lineages, not importation). Different mutations, different evolutionary trajectories, convergent threat.

**High-endemicity complication:** African high-transmission settings create partial immunity in hosts that may mask delayed clearance (partial APR phenotype). Surveillance underestimates clinical resistance. Window before overt clinical failure is narrowing.

### 2.2 Partner Drug Resistance — Geographic Footprint

| Drug | Resistance mechanism | Geography | Prevalence signal |
|------|---------------------|-----------|-------------------|
| Piperaquine | pfpm2/pfpm3 copy number amplification | Cambodia/SEA (established) | High prevalence SEA |
| Piperaquine | PfCRT mutations | Cambodia/SEA (established) | High certainty, both mechanisms co-present |
| Piperaquine | pfpm2 CNV | Southern Angola | 9.8% — low, not yet dominant |
| Lumefantrine | pfmdr1 CNV (amplification) | Southern Angola | 8.9% — low |
| Lumefantrine | pfmdr1 mutations (N86Y, Y184F, D1246Y) | Sub-Saharan Africa + India | Co-occurs with AL failure (meta-analysis) |
| Amodiaquine | PfCRT mutations | SEA, Africa | Cross-resistance with CQ via shared mechanism |
| Chloroquine | PfCRT mutations (K76T) | PNG (167 nM, CI 141–197; threshold 100 nM) | High resistance, established |
| Chloroquine | pfcrt resistance allele | Sub-Saharan Africa + India | Co-occurs with ACT failure (meta-analysis) |

**The "plasmepsin-piperaquine paradox"** (PMID:40720544): CRISPR KO of PMII and/or PMIII individually restores PPQ sensitivity in isogenic Cambodian parasites — causal confirmation, not mere association. Yet field epidemiological data remains discordant. Mechanism: copy number amplification → resistance, but the mechanistic bridge from DV protease copy number to PPQ binding/efflux remains unresolved.

---

## 3. ACT Treatment Failure — Integrated Picture

ACT failure is **polygenic and regimen-specific**:

```
ACT failure = artemisinin resistance component + partner drug resistance component

For AL:    pfmdr1 86Y/184F/1246Y + (K13 or pfcoronin)
For AS+SP: pfdhps 437G + pfdhfr 51I/59R/108N (triple mutant) + ART resistance
For DHA-PPQ: pfpm2/3 CNV + PfCRT mutations + K13

Pfcrt 76T: pan-ACT failure signal, not regimen-specific (moderate certainty)
```

**ACT partner drug protection dependency**: Partner drug efficacy is not freestanding — it is contingent on overall ACT system efficacy. Surveillance must track both components jointly. Monitoring ART resistance alone understates true failure risk.

---

## 4. Head-to-Head Efficacy Data (Uganda, Children 6mo–10yr, PMID:34952573)

| Regimen | PCR-corrected 28-day efficacy | SAE rate | Certainty |
|---------|-------------------------------|----------|-----------|
| DHA-PPQ | 98.9–100% | 0.0 | High (efficacy) / Moderate (SAE) |
| AL | 87.2–94.4% | 0.0 | Moderate |

**Site-level alert:** AL efficacy CI upper bound touches 90% (WHO action threshold) at Busia and Arua, Uganda. Site-specific resistance signal — warrants enhanced surveillance and consideration of DHP rotation if repeat surveys confirm.

**Grading flag:** Evidence grade logged as `expert_opinion` across this RCT dataset — likely miscategorized. Upgrade warranted.

---

## 5. Next-Generation Artemisinin Derivatives — Resistance Status

OZ277 (arterolane) and OZ439 (artefenomel) are synthetic ozonides developed as ART-resistance workarounds. Both threatened by K13 double mutations:

| Double mutant | OZ277 | OZ439 | Region | Certainty |
|---------------|-------|-------|--------|-----------|
| C580Y + A212T | Moderate | Moderate | Cambodia | A212T amplifies both |
| R539T + A212T | Moderate | High | Cambodia | A212T amplifies both |

**A212T acts as resistance amplifier across primary K13 alleles AND across drug classes (artemisinins + ozonides).** This is the arms-race signal: pipeline compounds under selective pressure before wide deployment.

Longer ozonide half-life (potential advantage over artemisinins per PMID:41959371) does not protect against K13-mediated resistance. Partner drug reliance remains critical.

---

## 6. Resistance Phenotyping Tools

| Assay | Advantage | Evidence | Reference |
|-------|-----------|----------|-----------|
| RSA (Ring-stage Survival Assay, 6h DHA) | Gold standard in vitro correlate | High certainty | PMID:24867976 |
| Flow cytometry RSA | 250,000 erythrocytes/assay; throughput + ↓ operator bias vs Giemsa | High certainty | PMID:24867976 |
| eRRSA (extended recovery RSA) | Superior predictor of in vivo patient clearance half-life; higher throughput | Moderate certainty | PMID:32005233 |
| DHA IC50 | Moderate correlation with both RSA (rs=+0.424) and eRRSA (rs=−0.412) | Moderate | PMID:39545737, Uganda |

IC50 alone insufficient — resistance phenotyping needs survival assay confirmation. eRRSA = scalable RSA alternative for African field isolates.

---

## 7. Treatment Strategy Against MDR Falciparum

**Efficacy by disease severity:**

| Severity | Agent | Setting | Certainty |
|----------|-------|---------|-----------|
| Uncomplicated | ACT (AL, ASAQ, DHA-PPQ) | Outpatient, global endemic | High |
| Severe | IV artesunate (parenteral) | Inpatient | High |
| Severe | Artemisinin-based combination regimens | Inpatient, SSA | High |

**Against MDR *P. falciparum* (policy-level recommendations):**
1. Multiple first-line therapies in rotation/combination (system-level resistance mitigation; moderate certainty)
2. Triple drug combination (TDC) therapy over dual ACT (patient-level; moderate certainty)

Both recommendations: expert opinion, no effect size data, no specific drug names captured.

---

## 8. Novel / Experimental Signals

| Agent | Mechanism | Signal | Certainty | Gap |
|-------|-----------|--------|-----------|-----|
| MRT68921 (autophagy inhibitor) | Blocks ULK1/2 autophagy pathway | Lower IC50 in C580Y-resistant vs WT parasites (synthetic lethality) | Moderate | No IC50 values; in vitro only; mammalian selectivity unknown |
| Paclitaxel + DHA | β-tubulin disruption (distinct from ART) | Synergy against ART-resistant strains (in silico) | Low | Computational only; mammalian toxicity uncharacterized |

---

## 9. Critical Evidence Gaps (Cross-Cutting)

1. **Effect sizes absent everywhere** — no IC50 values, no ORs/HRs/CIs across the majority of claims. Cannot model ACT efficacy decay or resistance spread rate without quantitative data.
2. **Evidence grade ceiling = expert opinion** for most mechanistic and surveillance claims — no RCT-level causal confirmation for resistance mechanisms.
3. **All claims pending review** — zero validated nodes in current knowledge base.
4. **African K13 selection trajectory unquantified** — Ala675Val and Cys469Tyr confirmed positive selection in Uganda but magnitude insufficient for projections.
5. **A212T field prevalence unknown** — key threat but no epidemiological prevalence data in C580Y/R539T backgrounds.
6. **pfcoronin clinical correlation absent** — mechanism described, population-level epidemiological data linking mutation prevalence to clinical failure rates missing.
7. **PI3P → autophagy → resistance chain**: established in lab strains; field validation limited.
8. **Pediatric/pregnancy/immune-status stratification**: null across virtually all claims.
9. **pfpm2 paradox mechanistic resolution**: CRISPR confirms causality but PPQ-plasmepsin binding mechanism unresolved.
10. **Southeast Asia–specific resistance landscape diverges from Africa**: do not generalize GMS findings to sub-Saharan Africa without region-specific data.

---

## 10. Surveillance Priority Matrix

| Target | Drug at risk | Region priority | Signal strength |
|--------|-------------|----------------|----------------|
| K13 mutations (A675V, C469Y) | All ACTs | Uganda (confirmed) | High — CIs exclude zero |
| K13 C580Y + A212T | OZ277, OZ439, artemisinins | Cambodia → SEA | Moderate (expert opinion) |
| pfmdr1 N86Y/Y184F/D1246Y | AL | SSA + India | Moderate (meta-analysis) |
| pfpm2/3 copy number | DHA-PPQ (piperaquine) | SEA (high); Angola (low, 9.8%) | High SEA / Moderate Angola |
| PfCRT mutations | Piperaquine, CQ, AQ | SEA, global | High |
| pfdhfr/pfdhps triple mutants | AS+SP | SSA | Moderate |
| Pfcoronin mutations | All ACTs | Africa | Low–Moderate |
| PfATG18 T38I | ACTs (mechanistic) | SEA field isolates | Moderate (co-occurrence only) |

---

## 11. Entity Cross-Reference Index

| Entity | Connected to | Relationship |
|--------|-------------|--------------|
| K13 mutations | PI3P, autophagy, hemoglobin endocytosis, ART resistance | Causes via multiple paths |
| PI3P elevation | K13 mutation, UPR, autophagy upregulation | Downstream of K13; upstream of proteostatic buffer |
| PfATG18 T38I | C580Y, R539T, Y493H, PI3P pathway | Co-selected background mutation in SEA |
| arps10-V127M | K13-C580Y, fd-D193Y | Resistance potentiator; apicoplast compartment |
| Pfcoronin mutations | Hemoglobin endocytosis, heme limitation, K13 | Convergent heme-limitation mechanism |
| Hemoglobin endocytosis | Artemisinin activation, PfCoronin, K13 | Required for both parasite growth and drug activation |
| PfCRT mutations | CQ, AQ, piperaquine resistance | Cross-resistance via digestive vacuole transporter |
| pfmdr1 | Lumefantrine, mefloquine, heme-binding drugs | Point mutations (susceptibility shift) + amplification (efflux) |
| pfpm2/3 copy number | Piperaquine (DHA-PPQ) | Resistance marker; causal (CRISPR confirmed) |
| A212T (K13 second site) | C580Y, R539T, OZ277, OZ439 | Resistance amplifier across primary alleles + drug classes |
| ACT partner drug efficacy | ACT overall efficacy, artemisinin resistance | Dependent — cannot be evaluated in isolation |
| DHA-PPQ | pfpm2 CNV, PfCRT, piperaquine resistance | Threatened by dual resistance in SEA |
| AL | pfmdr1, Busia/Arua sites, WHO 90% threshold | Borderline efficacy signal in Uganda |
| MRT68921 | Autophagy, C580Y, synthetic lethality | Experimental therapeutic — resistance-induced dependency |

---

*All concepts status: pending_review · No effect sizes captured across majority of claims · Evidence grade predominantly expert_opinion · Do not use for clinical decision support without validation*
