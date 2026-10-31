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

## Optional satellite context (Phase 9)

The run can display local, quality-screened SMAP and MODIS extracts without adding either source
to the rotation score. Store one point/pixel extract per location using these exact filenames:

* `cleaned/smap_daily_<lat>_<lon>.csv`
* `cleaned/modis_mod13q1_<lat>_<lon>.csv`

Use two-decimal coordinates in the filename, matching the climate and soil files. SMAP is the
NASA/NSIDC Enhanced L3 radiometer product `SPL3SMP_E`, Version 6 (9 km). Its CSV columns are
`observation_date,soil_moisture,quality_flag,quality_status,product_id,spatial_resolution_km,product_version,retrieved`.
`soil_moisture` is volumetric fraction (m³/m³); preserve the product flag in `quality_flag` and
record its product-specific interpretation in `quality_status` (`recommended`, `good`, `uncertain`,
`bad`, or `missing`). Only recommended/good retrievals enter monthly medians. Earthdata access is
required for the source product; the app does not log in or download it.

MODIS is Terra `MOD13Q1.061`, 250 m, 16-day composites. Its CSV columns are
`observation_date,ndvi,evi,pixel_quality,product_id,product_version,scale_factor,retrieved`. Keep the product's
raw integer NDVI/EVI and reliability code (`0` good, `1` marginal, `2` snow/ice, `3` cloudy).
`scale_factor` must be `0.0001`; the app applies it and excludes fill/out-of-range and non-good
quality values. Both inputs must retain product version and retrieval date. Do not interpolate
missing observations. MODIS greenness is not a soil-health measure; both products are regional pixel
context, not field observations or irrigation advice.

Official product references: [SMAP SPL3SMP_E Version 6](https://nsidc.org/data/spl3smp_e/versions/6)
and [MODIS MOD13Q1.061](https://doi.org/10.5067/MODIS/MOD13Q1.061).
