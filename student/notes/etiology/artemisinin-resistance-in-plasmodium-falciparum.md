## Topic Note: Etiology of Artemisinin Resistance in *Plasmodium falciparum*

**Synthesized from 5 claims · 2 sources · 2026-05-09**

---

### Core Mechanism

Two converging causal chains explain resistance:

**1. K13 propeller domain mutations** *(high certainty · 3 specific variants + class-level claim)*

Mutations in the propeller domain of *kelch13* (*k13*, PF3D7_1343700) drive resistance. Three validated variants:

| Mutation | Claim ID |
|----------|----------|
| R539T | `bb7a8ce9` |
| I543T | `a480c81f` |
| Y493H | `9db305d3` |

These are the primary genetic markers. WHO-validated; Southeast Asian origin, now tracked globally. [PMID:37269964]

**2. Elevated phosphatidylinositol-3-phosphate (PI3P)** *(moderate certainty)*

PI3P upregulation → artemisinin resistance. Mechanistic bridge: K13 normally ubiquitinates PI3-kinase (PfPI3K); K13 mutations impair this → PfPI3K accumulates → PI3P elevated → parasite gains cytoprotection, enabling ring-stage survival during drug exposure. [PMID:25874676]

---

### Causal Graph

```
K13 propeller mutations (R539T / I543T / Y493H)
        │
        ▼
 ↓ K13-mediated ubiquitination of PfPI3K
        │
        ▼
 ↑ PfPI3K activity → ↑ PI3P
        │
        ▼
 Ring-stage cytoprotection
        │
        ▼
 Artemisinin resistance (prolonged ring survival = clinical partial resistance)
```

---

### Evidence Summary

| Factor | Certainty | Grade | Source |
|--------|-----------|-------|--------|
| K13 propeller domain mutations (class) | High | Expert opinion | PMID:37269964 |
| R539T | High | Expert opinion | PMID:37269964 |
| I543T | High | Expert opinion | PMID:37269964 |
| Y493H | High | Expert opinion | PMID:37269964 |
| Elevated PI3P | Moderate | Expert opinion | PMID:25874676 |

All 5 claims: `pending_review`. Evidence grade uniform: expert opinion — no RCT-level causal confirmation yet. PI3P claim moderate (mechanistic model, not fully confirmed in field isolates).

---

### Gaps

- No effect sizes / OR / HR quantified across any claim
- No population stratification (region, age, immune status absent)
- PI3P claim needs validation in African isolates (most data: Southeast Asia)
- Evidence grade capped at expert opinion — prospective genetic epidemiology needed to upgrade
