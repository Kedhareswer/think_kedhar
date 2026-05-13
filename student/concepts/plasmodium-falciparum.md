## Concept Note: *Plasmodium falciparum* Drug Resistance

**Entity:** *Plasmodium falciparum* | **Claims synthesized:** 17 | **Date:** 2026-05-09

---

### Core Thesis

*P. falciparum* has evolved multi-drug resistance across geographic strata, threatening the two pillars of frontline malaria treatment: artemisinins and their partner drugs. The parasite causing the greatest malaria burden in sub-Saharan Africa (3ed3a704) is now exporting Southeast Asian resistance genetics into Africa (fc5e75f7).

---

### 1. Artemisinin Resistance

**Primary driver: kelch13 (k13) mutations**

Multiple high-certainty claims converge here (0022b2de, 6ebe3019, 80d82d1a, 403eae89, 0e0e664c). Mechanistically:

- k13-mutant parasites survive 6-hr dihydroartemisinin pulse; measured by ring-stage survival assay (RSA) and patient clearance half-life (0022b2de)
- Resistance is *partial* — parasites slow, not halt, artemisinin killing
- Co-mutations **fd-D193Y** and **arps10-V127M** on k13-C580Y background further increase RSA survival vs. k13-C580Y alone (114aea30, moderate certainty) — epistatic stacking amplifies resistance

**Geographic pattern:**

| Region | Status | Certainty |
|--------|--------|-----------|
| Southeast Asia (Cambodia) | Established, multidrug-resistant lineages | High |
| Eastern Africa | Emerging — k13 mutations spreading (fc5e75f7) | High |
| Uganda (3 sentinel sites) | Pfk13 resistance-associated mutations: 0% prevalence at time of study (24521ea9) | Low |
| Sub-Saharan Africa (broader) | Partial resistance emerging | High |

The Uganda finding (24521ea9, low certainty) is a snapshot — absence at sentinel sites ≠ regional absence.

---

### 2. Partner Drug Resistance

Artemisinin-based combination therapies (ACTs) rely on partner drugs to clear residual parasites. Both major partners are compromised in Southeast Asia.

**Piperaquine (PPQ) resistance — dual mechanism:**

| Mechanism | Claim | Certainty |
|-----------|-------|-----------|
| Increased *plasmepsin II/III* gene copy number | 75d3630a | High |
| CRT mutations (chloroquine resistance transporter) | 72e10d04 | High |

Both mechanisms independently confer PPQ resistance in Cambodian strains. This underpins the **DHA-PPQ resistance** of Cambodian *P. falciparum* (e4350a1c) and is described as the "plasmepsin-piperaquine paradox" — plasmepsin copy number predicts resistance epidemiologically but mechanistic sufficiency is debated (source: PMID:40720544).

**Artemether-lumefantrine (AL) resistance:**

In Uganda, PCR-corrected 28-day efficacy upper CI bound approached the WHO 90% threshold in Busia and Arua (ea4fb695, moderate certainty) — borderline, not yet failed, but a warning signal.

---

### 3. Other Drug Resistance

- **Chloroquine** — geometric mean IC50 167 nM (CI: 141–197) in Papua New Guinea vs. 100 nM resistance threshold (87309127, high certainty). Established resistance.
- **Azithromycin** — geometric mean IC50 8,351 nM (CI: 5,418–12,871) in PNG (55996006, moderate certainty). Intrinsically poor activity; not a viable monotherapy.

---

### 4. Resistance Architecture Summary

```
P. falciparum resistance network
│
├── Artemisinin partial resistance
│   ├── PRIMARY: k13 mutations (C580Y dominant in SEA)
│   │   └── AMPLIFIED BY: fd-D193Y + arps10-V127M co-mutations
│   └── SPREADING: SEA → East Africa
│
├── Piperaquine resistance (Cambodia)
│   ├── Plasmepsin II/III copy number ↑
│   └── CRT mutations
│       → Combined: DHA-PPQ ACT failure
│
└── Legacy resistance
    ├── Chloroquine (PNG, widespread globally)
    └── Azithromycin (intrinsically low activity)
```

---

### 5. Evidence Gaps & Caveats

| Gap | Impact |
|-----|--------|
| All 17 claims graded `expert_opinion` (except 34707d5e = meta-analysis) | Evidence base is expert-driven, not RCT-confirmed for most resistance phenotypes |
| Most effect sizes null — no quantitative resistance magnitude for artemisinin claims | Cannot model ACT population-level efficacy decay without effect sizes |
| Uganda k13 prevalence = 0% (low certainty, single timepoint) | Under-surveillance risk; Africa resistance emergence may be faster than captured |
| Plasmepsin-piperaquine causal mechanism debated | Marker utility for surveillance ≠ proven mechanistic resistance driver |

---

### 6. Clinical Implications

1. **Southeast Asia:** DHA-PPQ is compromised by dual k13 + plasmepsin/CRT resistance. Triple ACTs or alternative partners needed.
2. **Africa:** Artemisinin partial resistance spreading. AL still functional but margin narrowing in Uganda hotspots.
3. **PNG:** CQ-resistant baseline; azithromycin not viable. ACT selection critical.
4. **Molecular surveillance priority:** k13, plasmepsin II/III copy number, CRT genotyping must expand beyond SEA sentinel sites into high-burden Africa.

---

*Sources: 10 unique PMIDs. All claims status: pending\_review.*
