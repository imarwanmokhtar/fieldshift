# DECISIONS.md — Field Shift

Decisions made outside the written specs, per CLAUDE.md Part 0 rule 8 ("Don't silently deviate").
Session date: 2026-10-30.

## Part 0 answers (reported to the human, 2026-10-30)

| Question | Answer |
|---|---|
| Build platform | This Linux machine (x86_64), Python 3.14.4 |
| Internet access to POWER | Confirmed working (HTTP 200 to power.larc.nasa.gov) |
| Real field coordinates | Not available → pilot point 31.04°N 31.38°E only, everything tagged `coordinates_illustrative` |

## Order-of-work decision
The data sprint (POWER fetch + crop-table research) was run **before** Phase 0 so the engine is
built on verified data instead of the seed's `placeholder` values. Phases still follow CLAUDE.md
Part 11 in order.

## Data decisions (each with its reason)

1. **POWER fetched once for 2011–2025** (superset of both 5-year and 15-year needs) instead of
   two ranges — one request per location/period per DATA.md §5.2 politeness rules. The wizard
   can slice 2020–2025 or use the full 15 years.
2. **Soil stays all-`missing` by design** (`cleaned/soil_31.04_31.38.json`): HWSD extraction is a
   human/QGIS task (DATA.md §6.3). No values were invented.
3. **Sorghum duration 130 kept, printed total 140 ignored.** The fetched FAO-56 Table 11 row
   prints stages 20/35/45/30 (= 130) with a printed total of 140 — the inconsistency exists in the
   original table (a second row 20/35/40/30 = 130 also exists). §7.4 requires stages to sum.
4. **Wheat stage row 20/50/60/30 = 160 kept** ("Barley/Oats/Wheat, Dec, Calif. Desert"): the row
   exists in the fetched table. Egypt-checked alternative: FAO calendar Delta growing_period
   150–190 d contains it. Egypt range recorded in the note; value unchanged so stages sum.
5. **Faba duration replaced with FAO-calendar value** (growing_period "180 - 190", midpoint 185,
   Delta region) — supersedes the seed's `placeholder` 160. EcoCrop's shorter 100–150 d span is
   global-variety and kept in the note.
6. **Berseem duration stays `placeholder` 200**: FAO i3500e prints a span ("October to May",
   multi-cut), not a day count. A computed number would pretend precision the source does not have.
7. **Maize sowing window {05-01 .. 07-01}** from the North-Delta peer-reviewed trial
   (Hegab et al. 2019; dates 1 May/1 June/1 July; later = worse), corroborated by GIEWS ("maize
   sowing began in May"). Window END = latest trial date; noted as needing local confirmation
   (no grain-maize row exists in either FAO calendar).
8. **Cotton sowing window {03-01 .. 05-31}**: FAO-56 Table 11's only Egypt-labelled row prints
   "Mar–May" (months). Day-level bounds are a mechanical expansion, documented in the note.
9. **Rice/sorghum windows come from the FAO calendar's only Egypt sessions** (Middle Egypt /
   Upper Egypt; no Delta rows exist in either calendar). Notes record this explicitly.
10. **Drought-collapse rule** (engine heuristic, documented in the YAML's `drought_class_mapping`):
    FAO manual Table 14 prints compound classes; each is collapsed to the MORE-SENSITIVE bound
    (low-medium → medium; medium-high → high) because the class feeds water-short warnings.
    Numeric Ky values from FAO-66 Table 1 are quoted in notes as supporting evidence.
11. **Faba salinity threshold corrected 1.6 → 1.5 dS/m** (FAO-29 Table 4 row "Broadbean
    (Vicia faba) 1.5"); the old value was an unverified recollection.
12. **Berseem salinity stays `missing`** although FAO-29 lists "Clover, Berseem" qualitatively as
    moderately sensitive: the enum wants a dS/m number, and EcoCrop's different salinity scale
    ("high >10 dS/m") is not addable to FAO-29's ECe. Mixing the two would be a false number.
13. **Midpoints for FAO-calendar ranges** (faba 185, nothing else needed; rice/sorghum kept at the
    FAO-56 stage-sum values): the schema has one `growth_duration_days` per crop, and §7.4 makes
    stages sum to it. Where an FAO-56 stage row exists, its stage-sum value is used and the
    Egypt range is stated in the note.
14. **pandas 3.1.0 quirk**: `day_of_year` used instead of the deprecated `dayofyear`;
    `EcoCrop_DB.csv` read as latin-1.
15. **USDA FAS calendar PNG blocked (403)** — no attempt to work around; source noted as
    unusable in the registry.

## Reminder of the standing rule
Every remaining `placeholder`/`missing` must be replaced by a cited value (or confirmed
locally) before any result is presented as a finding. Current leftovers are listed in
`crop_reference.yaml`'s status counts and in DATA.md §7.5.
