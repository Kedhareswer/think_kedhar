## Concept Note: Hemoglobin Endocytosis

**Entity:** `hemoglobin endocytosis`
**Claims:** 2 | **Source:** PMID:32905757 | **As of:** 2026-05-09

---

### Definition

Hemoglobin endocytosis — process by which intraerythrocytic *Plasmodium falciparum* ingests host red blood cell hemoglobin via receptor-mediated or bulk endocytosis into the parasite's digestive vacuole.

---

### Role in Parasite Biology

**P. falciparum* growth requires hemoglobin endocytosis** (certainty: high). Parasite digests ~60–80% of host cell hemoglobin for amino acids and to create space for replication. Block endocytosis → starve parasite, halt growth.

---

### Role in Drug Mechanism

**Artemisinin activation requires hemoglobin endocytosis** (certainty: high). Hemoglobin digestion releases free heme (ferrous iron, Fe²⁺). Fe²⁺ cleaves artemisinin's endoperoxide bridge → reactive radical species → alkylates parasite proteins → parasite death.

**Implication:** Reduced hemoglobin uptake (e.g., in ring-stage parasites or artemisinin-resistant strains with *kelch13* mutations) = less Fe²⁺ = less artemisinin activation = resistance phenotype.

---

### Mechanistic Summary

```
RBC hemoglobin
      │
      ▼ endocytosis (parasite)
 digestive vacuole
      │
      ├─► proteolysis → amino acids → parasite growth
      │
      └─► free heme (Fe²⁺)
                │
                ▼
          artemisinin + Fe²⁺ → radical → parasite death
```

---

### Evidence Quality

| Claim | Certainty | Grade |
|---|---|---|
| Growth requires Hb endocytosis | High | Expert opinion |
| Artemisinin activation requires Hb endocytosis | High | Expert opinion |

Both claims from single source (PMID:32905757). No RCT-level mechanistic data recorded. Status: **pending review**.

---

### Knowledge Gaps

- No quantitative thresholds (what % reduction in endocytosis sufficient to confer resistance?)
- No population/setting qualifiers — unclear if endocytosis rate varies by host immune status or parasite strain
- Evidence grade capped at expert opinion — mechanistic biochemistry studies (e.g., heme quantification assays) not yet linked as supporting claims

---

### Related Entities to Explore

- `kelch13 mutation` — upstream regulator of endocytosis rate in resistant strains
- `artemisinin resistance` — downstream consequence of reduced endocytosis
- `digestive vacuole` — organelle executing endocytosis
- `free heme / ferrous iron` — intermediate linking endocytosis to drug activation
