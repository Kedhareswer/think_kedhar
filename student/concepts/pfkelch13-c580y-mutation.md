## Concept Note: PfKelch13 C580Y Mutation

**Entity:** PfKelch13 C580Y | *Plasmodium falciparum*
**Date:** 2026-05-09 | **Claims:** 4 | **Sources:** PMID:25874676, PMID:40396048

---

### Core Biology

C580Y substitution in PfKelch13 disrupts substrate recognition of PfPI3K, reducing its polyubiquitination and proteolytic degradation (vs WT). Result: PfPI3K accumulates → elevated PI3P → upregulated autophagy pathway. Basal expression of autophagy proteins higher in C580Y parasites than isogenic WT controls (in vitro, SEA context).

### Resistance Mechanism

Elevated PI3P acts as cytoprotective buffer. Artemisinin activates via hemoglobin-derived heme in ring stage; C580Y parasites survive drug exposure by enhanced stress-response/autophagy, manifesting as partial ring-stage resistance. **Certainty: high** for artemisinin resistance phenotype; moderate for mechanistic claims.

### Field Co-occurrence

C580Y co-occurs with PfATG18 T38I in SEA field isolates. PfATG18 is a PI3P-binding autophagy effector — this co-selection pattern suggests epistatic cooperation reinforcing the autophagy-mediated resistance axis. Not yet quantified (no effect size). **Certainty: moderate.**

### Evidence Gaps

| Gap | Impact |
|-----|--------|
| No effect sizes on PI3K/autophagy protein levels | Can't quantify resistance magnitude |
| PfATG18 T38I co-occurrence frequency unreported | Unclear if obligate or facultative |
| All grades = expert_opinion | No RCT/systematic-review-level evidence |
| Setting heterogeneity (in vitro + field, no clinical) | Translational uncertainty |

### Mechanistic Chain (synthesized)

```
C580Y
 └─ ↓ PfPI3K ubiquitination & proteolysis
     └─ ↑ PfPI3K stability → ↑ PI3P
         └─ ↑ Basal autophagy proteins (PfATG18, others)
             └─ Enhanced ring-stage survival under artemisinin
                 └─ ART resistance phenotype
         └─ Field co-selection of PfATG18 T38I (SEA)
```

### Status

All 4 claims **pending_review**. Mechanistic model internally consistent across both sources. Priority review: claim `5974e143` (PI3K proteolysis) — foundational; if overturned, downstream claims weaken.
