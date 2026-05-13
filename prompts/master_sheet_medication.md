# Master sheet — Medication row

You are filling ONE row of the **Medications** sheet of `Master sheet.xlsx`. The reference Master sheet is consumed by Nigerian clinicians and pharmacists; each row covers one generic-name medicine and lists everything a prescriber needs at point-of-care, plus country-specific brand names so the row works across markets.

Your job: take the supplied claims, concept .md, and any connector data for one medication and emit a single JSON object whose keys are the Master-sheet column names.

## Trusted sources (cite by short_code in `SOURCES`)

| Short code | What it is | When to use |
|---|---|---|
| `ChEMBL` | EMBL-EBI bioactive-compound database | MECHANISM OF ACTION · DRUG CLASS · DRUG INTERACTIONS — call the ChEMBL MCP connector with the drug name |
| `PubMed` | Peer-reviewed biomedical literature | SIDE EFFECTS · INDICATION evidence |
| `WHO` | WHO essential medicines list and treatment guidelines | DOSAGE · INDICATION · CONTRAINDICATIONS for diseases on the WHO essential treatments list |
| `ClinicalTrials` | ClinicalTrials.gov | INDICATION evidence — phase 3 trial outcomes |
| `MedlinePlus` | NIH consumer drug information | THE GIST · OVERVIEW — model for plain-language tone |
| `NAFDAC` | Nigeria's drug regulatory authority | NAFDAC number · BRAND NAMES in Nigeria — manual lookup until scraper exists |

When a connector tool is available (ChEMBL, PubMed, ClinicalTrials), call it for the drug's generic name BEFORE deciding a cell is empty. Record the specific identifier (ChEMBL ID, PMID, NCT number) in `SOURCES`.

## Style — match the reference Master sheet exactly

The reference sheet is dual-audience (layperson + clinician). Look at the supplied reference style example for Lisinopril below:

> **OVERVIEW:** Lisinopril is a medicine that lowers high blood pressure and helps prevent heart attacks, strokes, and kidney damage from high blood pressure or diabetes. It belongs to a class of medicines called ACE inhibitors.

> **INDICATION:** Lisinopril is used to treat:
> - High blood pressure (hypertension)
> - Heart failure
> - To improve survival after a heart attack
> - To protect the kidneys in people with diabetes

> **CONTRAINDICATIONS:** DO NOT take Lisinopril if you:
> - Are allergic to lisinopril or any other ACE inhibitor
> - Are pregnant or planning to become pregnant
> - Have a history of angioedema (swelling under the skin)

Match that register. Plain language first, with the technical term in parens. Direct address ("DO NOT take Lisinopril if you…"). Bullet lists where natural.

## Output schema — JSON only

Return ONE JSON object. Keys MUST be EXACTLY these strings (including trailing spaces, newlines, and capitalisation — they are reproduced from Master sheet.xlsx character-for-character). No extra keys. No missing keys.

```json
{
  "THERAPEUTIC CATEGORY": "<e.g. 'Antimalarial', 'Cardiovascular Medications'>",
  "DRUG GROUP ": "<e.g. 'Artemisinin combination therapy', 'Antihypertensive'>",
  "DRUG CLASS": "<e.g. 'Sesquiterpene endoperoxide', 'ACE Inhibitors'>",
  "DRUG/GENERIC NAME\n\n": "<generic name only — no brand>",
  "NEO  URL": "",
  "OVERVIEW": "<3-5 sentences, plain language, dual register>",
  "INDICATION (Why is this medication prescribed?)": "<bulleted list with intro sentence>",
  "MECHANISM OF ACTION (How does it work?)": "<short paragraph + ChEMBL traceback if used>",
  "DOSAGE AND ADMINISTRATION (How should this medicine be used?)": "<available forms + dose tables by indication and population — never invent doses>",
  "CONTRAINDICATIONS (When not to use it)": "<bullet list, 'DO NOT take…' phrasing>",
  "WARNINGS AND PRECAUTION\n ": "<black-box + serious precautions>",
  "SIDE EFFECTS ": "<grouped by Common / Serious / Rare>",
  "DRUG INTERACTIONS (How this drug affects other drugs or is affected by other drugs)": "<list with direction (↑/↓ exposure) and severity>",
  "CONTROLLED SUBSTANCE": "<'<drug> is not a Controlled substance' OR 'Schedule N — <jurisdiction>'>",
  "STORAGE AND STABILITY ": "<temp range + special handling>",
  "TAGS": "<comma-separated keywords, lowercase>",
  "SOURCES": "<short codes joined by ' | ' with identifiers, e.g. 'ChEMBL:CHEMBL192 | PubMed:38321292 | WHO:ESSENTIAL-MEDS-2023'>",
  "THE GIST": "<2-3 sentences, simplest possible language. 'What is it?' framing.>",
  "BRAND NAMES in Nigeria": "<comma-separated brand names if known; '' otherwise>",
  "NAFDAC number ": "<single NAFDAC reg number if known; '' otherwise>",
  "Price range in naira": "<range '900-3000' or single number; '' if unknown>",
  "BRAND NAMES in UK": "",
  "BRAND NAMES in US": "",
  "BRAND NAMES in South Africa": "",
  "BRAND NAMES in Canada": ""
}
```

## Hard rules

1. **JSON only.** First character `{`, last `}`. No prose, no fences.
2. **Doses are sacred.** If no source supports a dose, write `"Available forms: <as known>. No dose claims in current corpus."` — never invent mg amounts. A wrong dose is the worst possible failure mode of this row.
3. **No hallucinated brand names.** If NAFDAC / WHO / a regulator hasn't been consulted, leave brand-name columns empty.
4. **Population-conditional doses are load-bearing.** Whenever the claim set or a connector provides a pediatric, weight-banded, pregnancy, or renal-adjusted dose, preserve those qualifiers verbatim.
5. **`SOURCES` cell traces every cell.** Whenever you used a connector, append its identifier. Anchor inline citations for any sentence that's load-bearing on one source (e.g. *"…via the carboxylesterase 2 (CES2) hydrolysis pathway (ChEMBL:CHEMBL192)."*).
6. **Controlled substance status default.** If you can't verify Schedule status, write `"Status not verified — please confirm with NAFDAC / DEA before publishing"`.
