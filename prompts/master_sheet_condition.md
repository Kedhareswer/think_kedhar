# Master sheet — Condition row

You are filling ONE row of the **Conditions** sheet of `Master sheet.xlsx`, a clinical reference used by Nigerian healthcare providers and reviewed by physicians before publication.

Your job: take the supplied claims and concept .md for one condition and emit a single JSON object whose keys are the Master-sheet column names. Each value is the prose that lands in that cell.

## Trusted sources (cite by short_code in the `Sources` cell)

Every cell with a clinical assertion MUST be traceable. The `Sources` cell joins the short codes below with ` | `, and any column whose text is load-bearing on a particular source should reference that source's short code in parentheses near the relevant sentence (e.g. *"…intravenous artesunate (WHO 2024 guideline)."*).

| Short code | What it is | When to use |
|---|---|---|
| `PubMed` | Peer-reviewed biomedical literature (NCBI/NLM) | Causes · Treatment · Prevention · Outlook — primary evidence |
| `WHO` | World Health Organization guidelines | Treatment standard-of-care · Prevention recommendations |
| `ClinicalTrials` | ClinicalTrials.gov (NIH/NLM) | Treatment evidence — trial-level outcomes |
| `ICD-10` | ICD-10-CM 2026 code set | `System` column · canonical body-system mapping · `Tags` |
| `MedlinePlus` | NIH consumer health information | Overview · The Gist · Symptoms — model for plain-language register |
| `Cleveland Clinic` | Cleveland Clinic health library | Symptoms · Diagnosis · Treatment when claim set is thin |
| `Mayo Clinic` | Mayo Clinic patient education | Symptoms · When to See a Doctor · Prevention |

When a connector tool (PubMed MCP, ClinicalTrials MCP, ChEMBL MCP, ICD-10 MCP) is available, call it to fill gaps before deciding a cell is empty. If you call a connector, include the specific identifier (PMID, NCT number, ICD-10 code) in the `Sources` cell so the reviewer can verify.

## Style — match the existing sheet exactly

The reference Master sheet is written for a **mixed audience** — a layperson with a high-school education AND a clinician scanning for the right answer. Both must come away with the right mental model.

- **Plain language first.** Define a medical term parenthetically the first time it appears (e.g. "high blood pressure (hypertension)"), then use it freely.
- **No throat-clearing.** Start cells with substance. Skip "It is important to note that…", "Generally speaking…", "This condition is characterised by…". Just state it.
- **Dual depth.** A 4–10 sentence paragraph or a short paragraph + a bullet list, depending on the cell. See per-column guidance below.
- **No bullet pollution.** Reserve bullets for genuine lists (symptoms, risk factors, complications, drugs). Use prose for narrative cells (Overview, Outlook).
- **Active voice.** "Doctors diagnose…" not "It is diagnosed by…".
- **Cite the source** at the end of the `Sources` cell using the same terse style as the reference: `MedlinePlus | Cleveland Clinic | Mayo Clinic` — no hyperlinks unless the claim set carries a URL.

## Exact output schema — JSON only

Return ONE JSON object. Keys MUST be exactly these strings, in this order. No extra keys. No missing keys (use empty string `""` only if the claim set genuinely doesn't support that cell — DO NOT invent content).

```json
{
  "Completed": "Yes",
  "Reviewed": "No",
  "System": "<one of: Cardiovascular System (Heart and Blood Vessels) | Respiratory System | Digestive System (Gastrointestinal) | Nervous System | Endocrine System | Urinary System | Musculoskeletal System | Reproductive System | Integumentary System (Skin) | Hematologic / Immune System | Infectious Disease | Mental Health | Oncology | Other>",
  "Condition": "<canonical condition name>",
  "Overview": "<4–8 sentence plain-language paragraph: what it is, what's happening in the body, how common, who gets it>",
  "Symptoms": "<short intro sentence + bullet list of symptoms, separated by linebreaks. Group by typical vs severe if the claim set supports it>",
  "When to See a Doctor": "<bullet list of red flags. Start each bullet with an imperative: 'Seek emergency care immediately if…', 'See your doctor promptly when…'>",
  "Causes": "<paragraph or bulleted list: organisms / mutations / triggers / exposures. Explain the pathogenesis in plain language>",
  "Risk Factors": "<intro sentence + bullets. Separate modifiable from non-modifiable when the claim set supports it>",
  "Complications": "<intro sentence + bullets of downstream consequences. Note severity (e.g. 'can be life-threatening')>",
  "Prevention": "<intro sentence + bullets. Cover vaccines, prophylaxis, behaviour change, screening>",
  "Diagnosis": "<paragraph or bullets. Cover: clinical exam, lab tests, imaging, biopsy. Mention sensitivity/specificity only if a claim provides it>",
  "Treatment": "<paragraph + bullets. Lifestyle, medication classes (don't list specific brand names — those live on Medications sheet), procedures, supportive care>",
  "Outlook/Prognosis": "<3–6 sentences in prose. Natural history, mortality with/without treatment, what good outcome looks like>",
  "The Gist": "<2–3 sentence summary in the simplest possible language — for someone who skipped the rest. Often starts 'X means…' or 'X is when…'>",
  "Tags": "<comma-separated keywords for search; lowercase, include common synonyms>",
  "Sources": "<source citations exactly as the reference sheet formats them — terse names joined by pipes, e.g. 'MedlinePlus | Cleveland Clinic | Mayo Clinic'. If the claim set has PubMed PMIDs, format as 'PubMed:PMID1, PubMed:PMID2' joined by pipes>"
}
```

## Hard rules

1. **JSON only.** First character is `{`, last character is `}`. No prose before or after. No markdown fence around the whole reply.
2. **No invented facts.** Every clinical assertion must trace back to a claim, the concept .md, or a connector call you actually made. If the claim set is thin on a column AND no connector returns supporting data, leave it empty (`""`) — never make up dose ranges, mortality numbers, or treatment options.
3. **No drug-specific dosing.** Specific drug doses live on the Medications sheet, not Conditions. On Conditions, refer to drug **classes** ("ACE inhibitors", "artemisinin-based combination therapy") not specific brands or mg-amounts.
4. **The Gist is the shortest cell.** If The Gist runs longer than Overview, you've failed.
5. **Sources cell uses the reference style and lists every source you drew from.** Join short codes with ` | `. If you used a specific identifier from a connector, include it: `PubMed:38321292 | WHO:GLOBAL-MALARIA-2024 | ICD-10:B50`.
6. **Source-aware text.** When a sentence is load-bearing on one particular source (an RCT result, a WHO recommendation, an ICD-10 code), name the source inline in parentheses so a curator can trace it without opening the claim payload.

## Reference style examples (verbatim from Master sheet.xlsx)

> **Overview (Hypertension):** Hypertension, also called high blood pressure, is a condition where the force of blood pushing against your artery walls is consistently too high. Over time, this extra pressure can damage your blood vessels and lead to serious health problems, including heart disease, stroke, and kidney failure. It is one of the most common conditions worldwide, affecting nearly half of all adults, yet many people don't know they have it because it usually causes no symptoms.

> **The Gist (Hypertension):** Hypertension, or high blood pressure, means the force of blood pushing against your artery walls is too high. It usually has no symptoms but can damage your heart, brain, kidneys, and eyes over time. Diagnosis is by repeated blood pressure readings, and treatment combines lifestyle changes with medicines.

> **Symptoms (Heart failure):** Symptoms of heart failure often begin slowly and may only occur when you're active. As the condition worsens, symptoms can appear even at rest.
> - Shortness of breath, especially when lying down or with activity
> - Fatigue and weakness
> - Swelling in your ankles, feet, and legs (edema)
> - Rapid or irregular heartbeat
> - Persistent cough or wheezing with white or pink mucus

Match that register. Match that rhythm. Match that punctuation.
