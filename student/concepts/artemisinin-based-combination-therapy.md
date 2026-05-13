## Concept Note: Artemisinin-Based Combination Therapy (ACT)

**As of:** 2026-05-09 | **Claims synthesized:** 4 | **Status:** All pending review

---

### Core Identity

ACT = artemisinin derivative + partner drug. First-line standard for uncomplicated *Plasmodium falciparum* malaria in endemic settings and outpatient care.

---

### Claim Synthesis

#### Treatment efficacy (3 claims, high certainty)

| Claim ID | Object | Setting | Regimen note |
|----------|--------|---------|--------------|
| `6fa78150` | Uncomplicated falciparum malaria | Endemic | ACT (generic) |
| `a0b4fd86` | Uncomplicated *P. falciparum* malaria | Outpatient | Artemisinin derivative + partner drug |
| `44e5407a` | *P. falciparum* malaria | Endemic | ACT (generic) |

**Synthesis:** Claims converge — ACT is established treatment across endemic and outpatient contexts. No dose/kg, duration, or effect size captured; evidence grade is expert opinion across all three. Claims `44e5407a` and `6fa78150` share endemic setting; `a0b4fd86` adds outpatient specificity and names the structural mechanism (combination = derivative + partner).

#### Resistance threat (1 claim, high certainty)

| Claim ID | Subject | Predicate | Region |
|----------|---------|-----------|--------|
| `0e0e664c` | *P. falciparum* | resists ACT | Endemic areas |

**Synthesis:** Same endemic settings where ACT is first-line also host documented resistance. High certainty, expert opinion (PMID:37269964 — molecular resistance review). This claim is in direct tension with `44e5407a` (same source paper), reflecting the dual-narrative of the original literature: ACT treats, yet resistance undermines it.

---

### Tensions & Gaps

| Issue | Detail |
|-------|--------|
| **Efficacy vs. resistance** | Three claims assert treatment; one asserts resistance — same endemic region, one overlapping source |
| **No quantitative effect size** | Zero claims carry metric/value/CI — efficacy strength unmeasured |
| **Evidence grade ceiling** | All 4 = expert opinion. No RCT-level grading present |
| **Population blanks** | Age, pregnancy, immune status null across all claims |
| **Resistance mechanism missing** | Claim `0e0e664c` notes resistance exists; no pfkelch13/pfcoronin variant detail captured at claim level |

---

### Source Map

| PMID | Claims | Topic |
|------|--------|-------|
| 34452235 | `6fa78150` | pfcoronin mutations & quinoline susceptibility |
| 38321292 | `a0b4fd86` | Artemisinin partial resistance emergence in Africa |
| 37269964 | `0e0e664c`, `44e5407a` | Molecular artemisinin resistance mechanisms |

Note: PMID:37269964 yields both a treatment claim and a resistance claim — consistent with a review paper covering both efficacy context and resistance data.

---

### Recommended Next Steps

1. **Upgrade evidence grade** — link RCT/meta-analysis sources for efficacy claims; expert opinion insufficient for clinical decision support
2. **Populate dose regimen** — 3-day course, specific ACT regimens (AL, ASMQ, DHA-PPQ) should be discrete claims
3. **Stratify by partner drug** — resistance profiles differ by ACT partner; merge into `0e0e664c` variants
4. **Add region specificity** — SEA partial resistance vs. emerging African resistance require separate claims
5. **Resolve claim overlap** — `6fa78150` and `44e5407a` near-duplicate; candidate for supersession after regimen detail added
