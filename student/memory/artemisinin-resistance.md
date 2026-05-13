# Artemisinin Resistance in *Plasmodium falciparum* — Cross-Concept Synthesis

**Scope:** Mechanisms, genetics, geography, treatment implications, and evidence gaps for artemisinin (ART) and ACT resistance
**Date:** 2026-05-09 | **Status:** Working synthesis — all source claims pending review

---

## 1. Primary Genetic Drivers

### 1.1 Kelch13 (K13/PfKelch13) Mutations — Central Resistance Node

K13 propeller-domain mutations are the dominant, best-evidenced cause of *P. falciparum* artemisinin partial resistance (ART-R). Multiple convergent evidence streams support this:

| Mutation | Region | Certainty | Evidence grade |
|---|---|---|---|
| C580Y | Greater Mekong Subregion (dominant) | High | Expert opinion / meta-analysis |
| R539T, Y493H, I543T | Southeast Asia | High | Expert opinion |
| R561H | NW Tanzania | High | Expert opinion |
| F476I, R539T, Y561H | Sub-Saharan Africa + India | Moderate | Meta-analysis |
| A675V, C469Y | Uganda | High | Cohort/modelling (CIs exclude zero) |
| C469F, P441L | Uganda | Low | Cohort/modelling (CIs cross zero) |

**C580Y** is the best-characterized allele. It disrupts K13-mediated ubiquitination of PfPI3K → PfPI3K accumulates → elevated PI3P → upregulated autophagy → enhanced ring-stage survival under ART exposure. Basal autophagy proteins (including PfATG18) are higher in C580Y vs. isogenic wild-type (in vitro, SEA context).

**Clinical phenotype:** Prolonged parasite clearance half-life (mean 4.1 h in K13-mutant vs. wild-type under standard artesunate in Thailand; moderate certainty, cohort). Ring-stage survival assay (RSA₀₋₃ₕ) is the standard in vitro correlate.

### 1.2 Accessory / Background Mutations — Resistance Amplifiers

K13 mutations do not act alone. Layered genomic evidence establishes an **epistatic resistance architecture**:

| Gene / Allele | Effect on K13 background | Certainty | Source |
|---|---|---|---|
| arps10-V127M (apicoplast ribosomal protein S10) | Further increases RSA₀₋₃ₕ survival vs. K13-C580Y alone | Moderate | PMID:36303209 |
| fd-D193Y (ferredoxin) + arps10-V127M | Further increases RSA₀₋₃ₕ survival vs. K13-C580Y alone | Moderate | PMID:36303209 |
| PfATG18 T38I | Co-selected with C580Y, Y493H, R539T in SEA field isolates | Moderate | PMID:40396048 |

**Implication:** Surveillance tracking only K13 undercounts resistance potential. Background mutations co-selected in Southeast Asian lineages amplify resistance penetrance; this may explain why K13 mutations alone don't fully predict clinical failure in all contexts.

### 1.3 Pfcoronin Mutations — K13-Independent Pathway (Africa)

Pfcoronin mutations (G50E, R100K, E107V in African isolates) confer ART resistance via a mechanistically distinct but convergent pathway:

```
Pfcoronin mutation
 → disrupted PfCoronin–PfActin interaction
 → loss of ring-stage endosomal localization
 → impaired hemoglobin endocytosis
 → reduced heme substrate for ART activation
 → ART resistance + treatment failure (Africa)
```

Co-occurrence with PfKelch13 mutations at the heme-limitation node is asserted (low certainty — convergence hypothesis, not directly demonstrated). Clinically relevant because Pfcoronin variants provide a K13-independent resistance axis active in Africa where K13 allele frequencies are still rising.

---

## 2. Mechanistic Pathways

### 2.1 The PI3P / Autophagy Axis (K13-Mediated)

```
K13 propeller mutation
 └─ ↓ ubiquitination of PfPI3K → ↑ PfPI3K stability
     └─ ↑ PI3P
         ├─ ER-PI3P vesiculation
         └─ ↑ autophagy proteins (PfATG18, others)
             └─ enhanced ring-stage proteostasis under ART
                 └─ partial resistance phenotype
```

Transgenic PI3K overexpression in *P. falciparum* recapitulates resistance in vitro (low certainty; no effect size). Elevated PI3P → ER vesiculation → autophagy are sequential claims, each moderate certainty, expert opinion. The full chain is internally consistent but lacks in vivo and field validation.

**ART-induced ER stress:** ART triggers ER stress and UPR activation in *P. falciparum*, upregulating autophagy — which may be exploited as a survival/tolerance mechanism by resistant parasites (moderate certainty; in vitro; no effect size quantified). This closes the loop: ART causes the very stress response that K13-mutant parasites are primed to exploit.

**Therapeutic implication:** C580Y parasites show higher autophagy dependency → paradoxically *more* sensitive to autophagy inhibitor MRT68921 (IC50 lower in resistant vs. wild-type in vitro; moderate certainty). Classic synthetic lethality — resistance-induced vulnerability. No in vivo data; mammalian selectivity unaddressed.

### 2.2 Hemoglobin Endocytosis — Convergent Mechanistic Node

ART activation is heme-dependent:

```
RBC hemoglobin
 → endocytosis by parasite
 → digestive vacuole proteolysis → free heme (Fe²⁺)
 → Fe²⁺ cleaves ART endoperoxide bridge → radical → parasite death
```

**Both K13 and Pfcoronin mutations converge here.** K13-mutant parasites slow hemoglobin digestion; Pfcoronin-mutant parasites impair endocytic uptake upstream. Less heme → less drug activation. This convergence (low certainty for the combined claim; each arm individually moderate–high) may explain why surveillance of either locus alone understates resistance.

No quantitative threshold established: what percentage reduction in endocytosis confers clinically relevant ART resistance is unknown.

### 2.3 Metabolic Reprogramming

Meta-analytic evidence (moderate certainty) from resistant vs. sensitive isolate transcriptomics:

- **Pentose phosphate pathway downregulation** in resistant isolates
- **Glycolytic pathway downregulation** in resistant isolates

Interpretation consistent with "quiescence model": reduced glucose flux → lower hemoglobin digestion → less ROS → less ART activation. Causal direction not confirmed — metabolic shift may be consequence rather than driver of resistance.

---

## 3. Geographic Spread and Selection Dynamics

### 3.1 Southeast Asia — Established, High Prevalence

Greater Mekong Subregion (GMS): K13 resistance entrenched; C580Y dominant in clonal expanding lineages. Multidrug resistance — K13 + piperaquine resistance (plasmepsin II/III amplification + PfCRT mutations) — has produced DHA-PPQ failure in Cambodia. Selection coefficient for C580Y: point estimate 0.627/year (CI crosses zero; moderate certainty, noisy cross-country pooled data).

### 3.2 Africa — Independent Emergence, Escalating Threat

**Critical epidemiological finding:** African K13 variants arose *de novo*, not by importation from SEA. Convergent evolution under local artemisinin selection pressure.

| Mutation | Country/Region | Annual selection coefficient (s) | Certainty |
|---|---|---|---|
| C469Y | Uganda | 0.383 (CI: 0.207–0.591) | **High** |
| A675V | Uganda | 0.237 (CI: 0.087–0.403) | **High** |
| C469F | Uganda | 0.324 (CI: −0.629–1.150) | Low |
| P441L | Uganda | 0.494 (CI: −0.462–1.410) | Low |
| R561H | NW Tanzania | Confirmed, trajectory unquantified | High |

Uganda's C469Y and A675V have **confirmed positive selection** (CIs exclude zero) — these are active, spreading resistance markers. C469F and P441L signals present but statistically underpowered.

High-endemicity African context complicates interpretation: partial host immunity can clear parasites despite K13 mutations, masking clinical resistance. This may delay detection until resistance prevalence is high.

### 3.3 Multicenter Global Signal

Multicenter trial data (Kenya, Peru, Thailand) confirm partial ART resistance phenotype across three continents — both direct ACT resistance and reduced clinical effectiveness (cohort, high certainty; PMID:40614930). Peru finding notable: implies either independent emergence or importation in a low-transmission setting.

---

## 4. ACT Treatment Failure — The Compound Risk

### 4.1 Mechanism of Failure

```
Artemisinin partial resistance (K13)
    → reduced ART efficacy (slower parasite clearance)
    → therapeutic burden shifts to partner drug
        + partner drug resistance (independent selection)
        → combination fails entirely
```

This dependency is formalized: **partner drug protection is contingent on overall ACT efficacy**. Dual resistance eliminates both components. High certainty (expert opinion; PMID:37269964).

### 4.2 Partner Drug Resistance Markers by Regimen

| Regimen | Resistance marker | Certainty | Evidence grade |
|---|---|---|---|
| Artemether-lumefantrine (AL) | Pfmdr1 86Y/184F/1246Y co-occur with failure | Moderate | Meta-analysis |
| Artesunate + SP (AS+SP) | Pfdhps 437G | Moderate | Meta-analysis |
| AS+SP | Pfdhfr triple mutant (51I/59R/108N) | Moderate | Meta-analysis |
| ACT (broad) | Pfcrt 76T | Moderate | Meta-analysis |
| DHA-PPQ (SEA) | Plasmepsin II/III copy number amplification | High | Expert opinion |
| DHA-PPQ (SEA) | PfCRT mutations | High | Expert opinion |

**Plasmepsin–piperaquine paradox:** PMII/III amplification predicts PPQ resistance epidemiologically and CRISPR knockouts confirm causal sufficiency in vitro, yet mechanistic link (aspartyl proteases → PPQ binding disruption) remains contested. PfCRT mutations may act independently or synergistically.

### 4.3 Regional AL Efficacy Signal

Uganda (3-site RCT, children 6 mo–10 yr): PCR-corrected 28-day AL efficacy 87.2–94.4%. Two sentinel sites (Busia, Arua) have CI upper bound touching WHO 90% threshold — **borderline performance**. DHA-PPQ in same trial: 98.9–100% (high certainty). The superiority likely reflects piperaquine's longer half-life and the early stage of K13 spread in Uganda.

**Southern Angola:** Pfmdr1 CNV 8.9%, pfpm2 CNV 9.8% — both low. AL and DHA-PPQ retain efficacy locally; baseline for future surveillance.

---

## 5. Next-Generation Artemisinin Derivatives — Resistance Already Emerging

Synthetic ozonides (OZ277/arterolane, OZ439/artefenomel) were developed partly to overcome K13-mediated resistance. They share the same PfPI3K/heme-mediated activation pathway — and K13 double mutations confer resistance:

| Double mutant | Drugs affected | vs. single mutant | Certainty |
|---|---|---|---|
| K13 C580Y + A212T | OZ277, OZ439 | Enhanced resistance | Moderate |
| K13 R539T + A212T | OZ277, OZ439 | Enhanced resistance | Moderate (OZ277) / High (OZ439) |

**A212T is a resistance amplifier** — not independently resistance-conferring, but potentiates established K13 alleles (C580Y, R539T) against ozonide scaffolds. All claims from Cambodia (C580Y dominant background); A212T field prevalence unknown. No IC50 or RSA survival rates extracted — magnitude of effect unquantified.

**Pipeline implication:** The ozonide replacement strategy faces the same evolutionary pressure as first-generation artemisinins, via the same K13-mediated mechanism, before wide deployment.

---

## 6. Surveillance and Phenotyping

### 6.1 Molecular Markers

Surveillance panels must track both K13 and partner-drug markers jointly. Monitoring artemisinin resistance alone understates true ACT failure risk.

**Minimum panel:**
- K13 propeller domain (all WHO-validated alleles; plus A675V, C469Y for Africa)
- A212T (emerging double-mutant signal)
- Pfcoronin (G50E, R100K, E107V for Africa)
- Pfmdr1 (point mutations + CNV)
- Pfpm2 (CNV for piperaquine)
- PfCRT (K76T + haplotype context)
- Pfdhps/Pfdhfr (for SP-containing regimens)

### 6.2 Phenotypic Assays

| Assay | Advantage | Key performance |
|---|---|---|
| Standard RSA₀₋₃ₕ | Reference method | DHA IC50 correlation: rs +0.424 |
| Extended recovery RSA (eRRSA) | Superior predictor of in vivo clearance half-life; higher throughput | IC50 correlation: rs −0.412 |
| Flow cytometric RSA | 250,000 erythrocytes/assay vs. manual microscopy; reduced operator bias | Higher throughput; standardization recommended |

DHA IC50 alone is insufficient for resistance phenotyping — correlation with RSA/eRRSA is modest (~17% shared variance). Survival assay confirmation required.

---

## 7. Treatment Strategy Against Multidrug-Resistant *P. falciparum*

Against MDR *P. falciparum*, two complementary strategic pivots are supported (moderate certainty; expert opinion):

1. **Population level:** Multiple first-line therapies deployed in rotation/combination — reduces selective pressure from any single regimen.
2. **Patient level:** Triple drug combination (TDC) therapy — third active drug overwhelms partial resistance to artemisinin and partner drug simultaneously.

No specific drug names, doses, or RCT effect sizes captured in these claims. Evidence base for TDC = expert framework, not protocol-grade. Region context likely GMS-centric (PMID:34267045).

---

## 8. Evidence Quality Landscape

| Claim domain | Dominant evidence grade | Key gap |
|---|---|---|
| K13 → resistance (GMS) | Expert opinion (high certainty) | No RCT mechanistic confirmation |
| K13 → resistance (Africa) | Cohort/modelling + meta-analysis | Quantitative clearance data sparse |
| PI3P/autophagy pathway | Expert opinion (moderate certainty) | In vitro only; no field validation |
| Pfcoronin → resistance | Expert opinion (moderate certainty) | No effect sizes; no clinical correlation |
| Partner drug resistance | Meta-analysis (moderate certainty) | No OR/HR effect sizes across any claim |
| Ozonide double-mutant resistance | Expert opinion (moderate–high) | No IC50/RSA values extracted |
| ACT efficacy (treatment) | Expert opinion (high certainty) | All claims lack dose/regimen quantification |

**Universal gap:** Effect size fields null across virtually all claims. Quantitative resistance magnitude — IC50 shifts, RSA survival %, clearance half-life deltas, treatment failure ORs — is largely unrepresented in the current claim set. Risk modeling and threshold-based policy decisions are not possible without this data.

---

## 9. Synthesis — Key Patterns

**Convergent mechanisms:** K13 and Pfcoronin mutations both reduce heme availability for ART activation. The pathway has two entry points (endocytosis disruption upstream vs. PI3K-mediated hemoglobin digestion downstream); combined burden is additive.

**Escalating architecture:** Single K13 mutation → background mutations (arps10, fd, PfATG18 T38I) amplify resistance → double K13 mutations (+ A212T) extend to next-gen drugs. Resistance evolution is building on prior scaffolds.

**Geographic divergence:** SE Asia (clonal expansion, C580Y, high selection pressure, established dual ART+PPQ resistance) vs. Africa (independent emergence, distinct alleles, high-transmission immunity buffering, partner drugs still largely intact). Different trajectories, convergent threat.

**Arms race signal:** Double K13 mutations conferring ozonide resistance before ozonides are widely deployed suggests adaptive evolution is already anticipating replacement drugs.

**Containment window:** African K13 selection coefficients are positive and statistically confirmed (Uganda), but partner drug resistance has not co-emerged at SE Asia levels. This gap represents the current window for combination strategy and surveillance escalation before dual resistance establishes.

---

*All source claims status: pending review. No effect sizes across most claims — quantitative data extraction from primary literature required before clinical decision support use.*
