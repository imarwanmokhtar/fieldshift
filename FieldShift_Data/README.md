# FieldShift_Data — provenance-first data layer

Raw files are the single source of truth. `cleaned/` files are reproducible from `raw/` by the
scripts in `../scripts/` (pre-engine placeholders until the engine's `data/` modules exist).

> Every value in `cleaned/crop_reference.yaml` carries a `{v, unit, src, status, note}` object.
> Value-status enum and UI badges: DATA.md §0.2. Retrieval dates: `references/links.md`.
> No value is invented; what could not be verified stays `placeholder` or `missing` with a note.

## Layout

```
raw/
  power/power_31.04_31.38_20110101_20251231_20261030.csv   # NASA POWER daily, pilot point, HTTP 200 2026-10-30
       (+ .request.json sidecar with the exact URL + sha256)
  crops/
    fao56_ch6_tables11_12_fetched_20261030.txt             # FAO-56 Tables 11/12 (fetched; row quotes in extract)
    fao_dhlg_cropcalendar_egy_20261030.json                # FAO crop calendar (DHLG API, 65 Egypt crops)
    fao_crop_calendar_by_country_all_20261030.csv          # FAO calendar export (cross-check; agrees with DHLG)
    EcoCrop_DB.csv / Ecocrop_variable_lookup.csv           # EcoCrop mirror (temp/pH/cycle; latin-1)
    ecocrop_extract_for_fieldshift.json                    # the 8 variety-level rows used by the table
    fao_water_manual/                                      # FAO manual ch.2/3/4 HTML (Tables 5, 6, 7, 14, paddy losses)
    fao29_rev1_salt_tolerance_20261030.htm                 # FAO-29 Rev.1 Table 4 + qualitative groups
    fao_i3500e_berseem_20261030.pdf                        # Egyptian Clover monograph (p.26/32/66 used)
    giews_egy_country_brief_20261030.pdf                   # GIEWS brief 30-06-2026 (maize/rice May sowing)
    crop_table_verification_extract_20261030.md            # QUOTED rows for every value in crop_reference.yaml
    usda_egy_calendar_20261030.png                         # NOT USABLE: HTTP 403 (kept only as the logged attempt)
cleaned/
  climate_daily_31.04_31.38.csv        # 5479 rows 2011-2025, 0 missing; qc column; from raw/power (§5.5)
  climate_seasonal_31.04_31.38.csv     # winter (Nov-Apr) & summer (May-Oct) windows from the daily table (§5.6)
  soil_31.04_31.38.json                # all fields `missing` by design until a human extracts HWSD (§6.3)
  crop_reference.yaml                  # schema_version 2 — 8 crops + fallow, fully sourced
metadata/
  sources.csv                          # source registry (10 sources incl. one blocked attempt)
  data_dictionary.csv                  # field definitions + units + coverage
  retrieval_log.jsonl                  # append-only download log (15 entries, sha256 per file)
  power_31.04_31.38_header.txt         # verbatim POWER header (§5.4)
references/
  links.md                             # every URL touched + first-opened date
../scripts/
  pre_engine_power_clean.py            # V-POWER-002..010 + cleaned/ regeneration from raw/
  pre_engine_crop_validate.py          # V-CROP (§7.4) + provenance/wording checks for crop_reference.yaml
```

## Validated state (2026-10-30)

* POWER record: **5479/5479 days, 0 missing values, 15 complete years** (2011–2025); header confirms
  0.5°×0.625° MERRA-2 grid, CERES SYN1deg solar, LST; API confirms data begins 1981-01-01.
  Seasonal windows: 15 complete summer + 14 complete winter (2025 winter correctly truncated).
* Crop table: **0 validation errors**; extracted windows in both slots; 6 remaining
  `placeholder`/`missing` values, all listed in DATA.md §7.5 (berseem specifics + engine-default
  stage splits for faba/berseem) + the HWSD soil human task.
* Provenance: every fetch has a `metadata/retrieval_log.jsonl` entry with sha256; blocked attempts
  (USDA 403, maize PDF 429) are logged as attempts, not silently dropped.

## Regeneration

```
../.venv/bin/python ../scripts/pre_engine_power_clean.py    # climate cleaned/ from raw/
../.venv/bin/python ../scripts/pre_engine_crop_validate.py  # crop table checks (exit 0 = pass)
```
