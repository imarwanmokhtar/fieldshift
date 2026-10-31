# DATA.md — Field Shift Engine: everything about the data

Companion to `CLAUDE.md` (agent instructions). **Read this file before touching anything that loads, validates, joins or scores data.**
Basis: the team's PPTX *"Field Shift – Egypt Data Research Plan"* (25 slides; pilot area Dakahlia) plus the official NASA Space Apps challenge text. Where this file goes beyond the PPTX, it says so.

---

## 0. How to read this file

### 0.1 Provenance tags used on facts in this document
| Tag | Meaning |
|---|---|
| **[PPTX]** | Stated in the team's research plan. Treat as the specification. |
| **[VERIFIED]** | Fetched from the named source during the session that wrote this file. Still re-check before publishing results. |
| **[RECALLED]** | Written from general knowledge by the AI assistant. **Not verified.** Check on first use. |
| **[TODO]** | Unknown. A human or the build agent must find it and cite the source. |

### 0.2 Value-status enum (used inside the crop table, soil records and profile)
| `status` | Meaning | UI badge | Effect on confidence |
|---|---|---|---|
| `verified` | A human checked the value against the original source. | `✔ verified` (green) | none |
| `extracted` | Taken from a cited source by software/AI, not yet human-checked. | `● extracted` (cyan) | none, but listed in "check locally" |
| `general_fact` | Textbook fact (e.g. botanical family, legumes fix nitrogen). | `○ general` (dim) | none |
| `placeholder` | A stand-in value so the engine can run. **Must be replaced.** | `▲ placeholder` (yellow) | lowers confidence one level per strategy |
| `missing` | No value. Indicators that need it become `unknown`. | `✖ missing` (red) | lowers confidence; indicator excluded |
| `farmer` | Entered by the farmer/user. | `◆ farmer` (magenta) | none; raises confidence for soil/EC |

### 0.3 What is ready and what is not (honest status at hand-over)
| Item | State |
|---|---|
| Source list, URLs, field names, pilot coordinates | Ready ([PPTX]) |
| NASA POWER request URL and parameters | Ready ([PPTX]); **live response fetched and verified 2026-10-30** (HTTP 200; §5.3 all confirmed; 15 complete years 2011–2025 stored in `raw/power/`) |
| FAO-56 stage lengths & Kc, Tables 11/12 | **[VERIFIED]** fetched 2026-10-30; footnote-digit artifacts & sorghum 140/130 inconsistency documented |
| Sowing windows | **extracted** for all 8 crops (FAO Egypt calendar ×2, FAO i3500e berseem, North-Delta maize trial, FAO-56 cotton months) — local Delta checks listed in §7.5 |
| Durations | wheat/maize/rice/cotton/sugar beet/sorghum extracted (FAO-56 rows, stage sums consistent); faba extracted (FAO calendar Delta 180–190); berseem `placeholder` 200 (book prints a span, not a count) |
| Reference water needs | **extracted** for 7 crops (manual Table 5); berseem `missing` (row absent) |
| Drought sensitivity | **extracted** for 7 crops (manual Table 14 + FAO-66 Table 1 Ky; collapse rule documented); berseem `missing` |
| Salinity thresholds (FAO-29) | **table-verified** for 7 crops (faba corrected 1.6 → 1.5); berseem `missing` (qualitative group only) |
| Crop temperature ranges & pH (EcoCrop mirror) | **extracted** for all 8 crops (units confirmed; variety-level rows) |
| Crop-table validation | `scripts/pre_engine_crop_validate.py` passes: 0 errors; 6 documented `placeholder`/`missing` values remain (§7.5) |
| HWSD soil values for the pilot point | `missing` — requires manual extraction (see §6.3) |
| SMAP / MODIS data | Phase 9 local-extract context panels implemented; no product data downloaded yet (optional) |

---

## 1. Data principles (from the PPTX — non-negotiable)

*(Slide numbers in this file = position in the PPTX file, 1–25. The printed page numbers on the Arabic slides run 2 higher.)*

1. **Start small.** A working pipeline first; extra datasets later (slide 2, 16). Priority order: **1 NASA POWER → 2 FAO crop calendar & water references → 3 HWSD soil → 4 SMAP → 5 MODIS NDVI/EVI**. SMAP and MODIS must never delay a working prototype.
2. **Every dataset carries its provenance into the prototype** (slide 12): source name + URL, dataset/product version, retrieval date, time coverage, spatial resolution / grid cell, units, missing-value codes.
3. **Do not silently fill gaps.** Keep quality flags. Unknown stays unknown and is shown as unknown.
4. **Do not mix incompatible units or resolutions** (slide 12). Convert explicitly and record the conversion.
5. **Store raw downloads separately from cleaned data** so results are reproducible (slide 12).
6. **Record whether each source is point-based, gridded or field-measured** (slide 3).
7. **Location rules** (slide 3): store latitude, longitude, coordinate reference system, and selection date. One satellite pixel may not represent the whole field.
8. **Collect only what the prototype needs.** Avoid identifiable farmer information unless necessary and consented (slide 10).
9. **No promises.** Do not present outputs as a yield forecast, an exact irrigation amount, or a universally "best" rotation (slides 2, 11).
10. **Every recommendation shows its source, update date and accuracy limits** (slide 25). The tool never gives a definitive verdict from a single indicator (slide 23).
11. **Definition of done for data** (slide 15): a developer can reproduce the data and understand each variable without a verbal explanation.

---

## 2. Pilot location [PPTX slide 3]

| Item | Value |
|---|---|
| Area | Dakahlia governorate, Nile Delta, Egypt |
| Test point | Near Mansoura, **31.04° N, 31.38° E** |
| Status | **Illustrative only** — for API testing. Not a real field. Replace with the actual farm/field point before interpreting any result. |
| CRS | WGS 84, EPSG:4326 (decimal degrees) |
| Rules | Store lat, lon, CRS, selection date. Prefer a field boundary or several soil samples when available. Mark source spatial type per dataset. |

The engine must tag every result that uses this point with flag `coordinates_illustrative` and print "illustrative — not field-specific" on the report.

Egypt sanity bounding box for input validation [RECALLED, approximate]: latitude 22.0 – 31.7, longitude 24.7 – 36.9. Outside it: warn and ask to confirm (the engine's crop table is Egypt-oriented).

---

## 3. Folder structure and file conventions [PPTX slide 15 + engine additions]

```
FieldShift_Data/
  raw/
    power/        power_<locid>_<start>_<end>_<retrieved-YYYYMMDD>.csv
                  power_<locid>_<start>_<end>_<retrieved-YYYYMMDD>.request.json   # URL, params, HTTP status, timestamp
    soil/         original HWSD extracts, QGIS exports, lab-test scans/notes
    crops/        saved source pages/PDFs or notes used for the crop table
    smap/  modis/ (optional, later)
  cleaned/
    climate_daily_<locid>.csv          # validated daily table (§5.5)
    climate_seasonal_<locid>.csv       # per-season summaries (§5.6)
    soil_<locid>.json                  # one soil record with provenance (§6.4)
    crop_reference.yaml                # the crop table (§7)
  metadata/
    data_dictionary.csv                # §14
    sources.csv                        # one row per source (§4)
    retrieval_log.jsonl                # append-only: every download/parse event
  references/
    rotation_templates.yaml            # §8.1
    rotation_rules.yaml                # §8.2
    links.md                           # the PPTX source list + retrieval dates
  README.md                            # what is here, how to regenerate it, known limits
```

* `<locid>` = `<lat>_<lon>` with 2 decimals, e.g. `31.04_31.38`. For a real field, use a short slug + the same suffix.
* Never edit files in `raw/`. Cleaned files are always regenerated from raw by code.
* Every cleaned file has a matching entry in `metadata/sources.csv` and `data_dictionary.csv`.
* `retrieval_log.jsonl` line example:
  `{"ts":"2026-10-30T09:12:44+03:00","source_id":"NASA_POWER_DAILY","action":"download","url":"https://power.larc.nasa.gov/api/temporal/daily/point?...","http_status":200,"bytes":412345,"file":"raw/power/power_31.04_31.38_20200101_20251231_20261030.csv","sha256":"..."}`

---

## 4. Source registry

`Verified?` refers to the session that wrote this file (see §0.1).

| ID | Source | URL | Spatial type | Resolution | Time | Priority | Role in engine | Verified? |
|---|---|---|---|---|---|---|---|---|
| `NASA_POWER_DAILY` | NASA POWER daily API (AG community) | https://power.larc.nasa.gov/docs/services/api/temporal/daily/ · portal https://power.larc.nasa.gov/ | gridded (point query returns the covering grid cell) | 0.5° × 0.625° meteorology (MERRA-2) **[VERIFIED from header]**; solar CERES SYN1deg — record grid in the dictionary | daily (LST **[VERIFIED from header]**); data from 1981-01-01 **[VERIFIED via API]** | **1** | temperature, rainfall, solar radiation → climate summary, ET0, crop-window indicators | **[VERIFIED]** live CSV fetched 2026-10-30, 15 complete years stored |
| `FAO_CROP_CAL` | FAO crop calendar for Egypt (two mirrors of the same 2021-02-26 dataset) | DHLG API `https://api-cropcalendar.apps.fao.org/api/v1/countries/EG/cropCalendar?language=en` · FAO data-catalog export via BigQuery API (parameterized CSV) · GIEWS country page https://cb.apps.fao.org/country.jsp?code=EGY&lang=en | non-spatial reference | national + AEZ (Delta region / Middle Egypt / Upper Egypt / others) | seasonal | **2** | sowing windows, growing periods | **[VERIFIED]** both calendars fetched 2026-10-30 (artifacts in `raw/crops/`); Delta windows extracted; NO Egypt rows for cotton, grain maize, berseem |
| `FAO_CROP_WATER` | FAO irrigation water management training manual | Ch.2 https://www.fao.org/4/S2022E/s2022e02.htm (Table 5 seasonal needs) · Ch.3 https://www.fao.org/4/S2022E/s2022e07.htm (Table 14 water need + sensitivity to drought; Tables 6/7 durations) · Ch.4 https://www.fao.org/4/S2022E/s2022e08.htm (paddy rice losses) | non-spatial reference | – | per season | **2** | reference seasonal water need (mm), drought sensitivity class | **[VERIFIED]** chapters fetched 2026-10-30 (artifacts `raw/crops/fao_water_manual/`); berseem absent from Tables 5 & 14 |
| `FAO56` | FAO Irrigation & Drainage Paper 56 — crop evapotranspiration, Ch. 6 | https://www.fao.org/4/x0490e/x0490e0b.htm | non-spatial reference | – | per stage | 2 (engine addition) | stage lengths (Table 11), Kc (Table 12) → ETc | **[VERIFIED]** by fetch; footnote digits garbled in extraction; confirm |
| `FAO_ECOCROP` | FAO EcoCrop crop requirements database | portal https://gaez.fao.org/pages/ecocrop · mirror with `EcoCrop_DB.csv` and `Ecocrop_variable_lookup.csv`: https://github.com/OpenCLIM/ecocrop | non-spatial reference | – | – | 2 (engine addition) | temperature ranges (TOPMN, TOPMX, TMIN, TMAX, KTMP), optimal/absolute pH, cycle length (GMIN, GMAX) | **[VERIFIED]** 2026-10-30: DB (2568 rows, latin-1) + variable lookup fetched; units confirmed (°C, pH); motif licence = OGL-UK-3.0 software (DOI 10.5281/zenodo.10843625); underlying FAO data licence still [TODO] (human) |
| `FAO29` | FAO Irrigation & Drainage Paper 29 Rev.1 — water quality for agriculture (salt tolerance) | Table 4 + sec.5: https://www.fao.org/4/T0234e/T0234E03.htm | non-spatial reference | – | – | 3 (engine addition) | crop salinity thresholds (ECe at 100% yield) | **[VERIFIED]** 2026-10-30 (artifact `raw/crops/fao29_rev1_salt_tolerance_20261030.htm`); faba corrected to 1.5; berseem listed only qualitatively (moderately sensitive) |
| `FAO33` | FAO Irrigation & Drainage Paper 33 — yield response to water (Ky) | seasonal Ky reproduced in FAO-66 Ch.2 Table 1: https://www.fao.org/4/i2800e/i2800e02.pdf | non-spatial reference | – | – | 3 (engine addition) | drought-sensitivity numeric evidence (Ky) | **[VERIFIED]** 2026-10-30 via FAO-66 Table 1 (cotton 0.85, sorghum 0.9, sugarbeet 1.0, maize 1.25, beans 1.15, winter wheat 1.05; NO rice row; no berseem). Classes in §7 come from `FAO_CROP_WATER` Table 14 |
| `FAO_I3500E` | FAO 'Egyptian Clover — King of Forage Crops' (Dost et al. 2014) | https://openknowledge.fao.org/server/api/core/bitstreams/947fa627-c9f2-4f67-b725-e0ef30d220c7/content | non-spatial reference | Egypt-focused monograph | – | 2 (engine addition) | berseem Egypt sowing window + practice | **[VERIFIED]** 2026-10-30 (artifact `raw/crops/fao_i3500e_berseem_20261030.pdf`): p.66 mid-Sep–late-Nov; p.32 Oct–May span; p.26 late-Sep–end-Oct |
| `GIEWS_EGY_BRIEF` | FAO GIEWS Egypt Country Brief (30-06-2026) | https://cb.apps.fao.org/country/EGY/pdf/EGY.pdf | non-spatial reference | national | seasonal observation | 3 | corroboration of maize/rice sowing onset, wheat harvest timing | **[VERIFIED]** 2026-10-30 (artifact `giews_egy_country_brief_20261030.pdf`) |
| `MAIZE_SOWING_STUDY` | Hegab et al. 2019 — maize sowing-date trial, El-Bosaily, North Delta | DOI 10.21608/ajs.2019.43523 (Arab Universities Journal of Agricultural Sciences) | non-spatial reference | North Delta field trial | – | 3 (engine addition) | Egypt maize sowing window (1 May / 1 June / 1 July tested) | **[VERIFIED via abstract]** 2026-10-30; PDF unreachable (HTTP 429) — see metadata/retrieval_log.jsonl |
| `HWSD2` | FAO/IIASA Harmonized World Soil Database v2.0 | https://www.fao.org/soils-portal/data-hub/soil-maps-and-databases/harmonized-world-soil-database-v20/en/ · PPTX links https://www.fao.org/land-water/resources/tools/databases/hwsd/en · https://www.fao.org/soils-portal/soil-survey/soil-maps-and-databases/harmonized-world-soil-database-v12/en/ | gridded | 1 km (30 arc-sec) | static | **3** | regional soil context | page **[VERIFIED]** (see §6.1) |
| `FARMER_SOIL_TEST` | Farmer's own lab/field soil test | – | field-measured | field | dated | preferred over HWSD | pH, organic carbon, EC, texture | n/a |
| `NSIDC_SMAP` | NASA SMAP soil moisture (NSIDC) | https://nsidc.org/data/smap · https://earth.gsfc.nasa.gov/hydro/data/nasa-usda-global-soil-moisture-data | gridded | some enhanced products ~9 km | 2015– | **4** (optional) | soil-moisture context | **[PPTX]** only |
| `MODIS_MOD13Q1` | NASA MODIS MOD13Q1 NDVI/EVI | https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD13Q1 · https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD13Q1 | gridded | 250 m, 16-day composite | 2000– | **5** (optional) | seasonal greenness context | **[PPTX]** only |
| `REF_CLIMATE_RISK` | Climate-risk references (Arabic section, slide 24) | OECD *Policies for the Future of Farming and Food in Egypt* (2026) https://www.oecd.org/en/publications/policies-for-the-future-of-farming-and-food-in-egypt_cab0cefd-en.html · FAO Near East https://www.fao.org/neareast/main-topics/action-areas/addressing-climate-change-in-agrifood-systems/addressing-climate-change-in-agrifood-systems/en · Knowledge4Policy/IFPRI https://knowledge4policy.ec.europa.eu/publication/climate-change-egypt%E2%80%99s-agriculture_en · World Bank CCKP profile https://climateknowledgeportal.worldbank.org/sites/default/files/2021-01/15723-WB_Egypt%20Country%20Profile-WEB.pdf | documents | national | – | background for UI text | **[PPTX]** |

---

## 5. Dataset 1 — NASA POWER (priority 1)

### 5.1 Parameters [PPTX slide 5]
| API field | Meaning | Unit | Use |
|---|---|---|---|
| `T2M` | Daily mean air temperature at 2 m | °C | seasonal climate fit |
| `T2M_MAX` | Daily maximum temperature | °C | heat context |
| `T2M_MIN` | Daily minimum temperature | °C | cold/frost context |
| `PRECTOTCORR` | Corrected precipitation | mm/day | rainfall totals and variability |
| `ALLSKY_SFC_SW_DWN` | All-sky surface shortwave radiation (downward) | MJ/m²/day | solar-energy context |

### 5.2 Request [PPTX slide 5]
```
GET https://power.larc.nasa.gov/api/temporal/daily/point
    ?parameters=T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,ALLSKY_SFC_SW_DWN
    &community=AG
    &longitude=31.38&latitude=31.04
    &start=20200101&end=20251231
    &format=CSV
```
* Dates are `YYYYMMDD`. Build the URL from a template; never hard-code the pilot point (use the profile's lat/lon).
* Save the **exact request URL** and the HTTP status next to the raw file (`.request.json`).
* No API key is needed. Be polite: one request per location/period, cache on disk, retry with back-off (max 3 tries), timeout ≥ 60 s.
* If JSON is easier later, `format=JSON` returns `properties.parameter.<PARAM>.<YYYYMMDD>`; the team plan uses CSV, so **CSV is the primary path**.

### 5.3 Facts confirmed on the first successful download (2026-10-30, pilot point, raw record `power_31.04_31.38_20110101_20251231_20261030.csv`)
All assumptions below were checked against the saved raw file and the API itself. Re-confirm only if the API version changes.
| Item | Confirmed value |
|---|---|
| Missing values | Header states: *"The value for missing source data that cannot be computed or is outside of the sources availability range: -999"*. Code `-999`, which becomes NaN on parse. (In the 2011–2025 pilot record: **0 missing values in all 5 columns**.) |
| Header block | File starts with `-BEGIN HEADER-` … `-END HEADER-`, followed by **one column-name row** `YEAR,DOY,T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,ALLSKY_SFC_SW_DWN`. |
| Time columns | `YEAR` + `DOY` layout in this record. The parser must still accept `YEAR` + `MO` + `DY` (older/other layouts exist), per §5.4 rule 2. |
| Grid | Header: *"elevation from MERRA-2: Average for 0.5 x 0.625 degree lat/lon region = 4.96 meters"*. Meteorology grid 0.5° × 0.625° confirmed. Sources named in the header: T2M/T2M_MAX/T2M_MIN/PRECTOTCORR = **MERRA-2**, ALLSKY_SFC_SW_DWN = **CERES SYN1deg** (CERES SYN1deg is 1°-scale solar; record grid per source in the data dictionary). |
| Data start | API returns a definitive error for pre-1981 requests: *"Your start date out of range. The data starts at 1981/01/01"* (tested 1979–1982 period on 2026-10-30). |
| Precipitation | `PRECTOTCORR` = "MERRA-2 Precipitation Corrected (mm/day)" per the header parameter list — model-reanalysis corrected, **not a rain-gauge record**. |
| Time basis | Header: *"Dates (month/day/year): 01/01/2011 through 12/31/2025 in LST"* — **Local Solar Time**. |
| Parameters per request | The 5-parameter request used by the engine works; only 5 parameters are needed (no limit test performed — keep to the documented 3 values: try ≤ 5, as the engine requests exactly 5). |
| Header location | `Location: latitude 31.04 longitude 31.38` — exact match to the requested point (V-POWER-010 passes with 0° deviation). |

### 5.4 Parsing rules
1. Read the file as text; find the line equal to `-END HEADER-`. Everything above is metadata → store verbatim in `metadata/` as `power_<locid>_header.txt` and parse out any lat/lon/elevation lines. If no marker exists, treat the first row that contains `YEAR` as the header.
2. Parse the table with pandas. Build `date` from `YEAR`+`DOY` or `YEAR`+`MO`+`DY`.
3. Replace the missing-value code with `NaN` (only the code documented in the header; default `-999`). Count them per column.
4. Rename columns to snake case with units (see §5.5). Do **not** convert units unless documented; every conversion is logged.
5. Run all `V-POWER-*` checks (§12). Failed checks produce flags/errors; **never** interpolate or fill.

### 5.5 Cleaned table: `climate_daily_<locid>.csv`
| Column | Type | Unit | Source column | Notes |
|---|---|---|---|---|
| `date` | date | ISO `YYYY-MM-DD` | YEAR+DOY / MO+DY | unique, sorted, no gaps expected |
| `year`, `month`, `doy` | int | – | derived | |
| `t_mean_c` | float | °C | `T2M` | NaN if missing |
| `t_max_c` | float | °C | `T2M_MAX` | |
| `t_min_c` | float | °C | `T2M_MIN` | |
| `rain_mm` | float | mm/day | `PRECTOTCORR` | ≥ 0 |
| `solar_mj_m2` | float | MJ/m²/day | `ALLSKY_SFC_SW_DWN` | |
| `qc` | string | – | engine | `ok`, `missing_value`, `out_of_range`, `inconsistent` (semicolon-joined) |

### 5.6 Seasonal summary: `climate_seasonal_<locid>.csv`
One row per (`slot`, `year_start`): `slot` ∈ {winter, summer}, window = slot months (winter Nov–Apr crossing the year end, summer May–Oct). Columns: `n_days`, `n_missing`, `t_mean_c`, `t_max_mean_c`, `t_min_mean_c`, `t_max_abs_c`, `t_min_abs_c`, `rain_total_mm`, `rain_days_ge_1mm`, `hot_days_tmax_ge_35`, `cold_days_tmin_le_5`, `frost_days_tmin_le_0`, `solar_mean_mj_m2`, `complete` (bool: window fully inside the data period). Only `complete` windows feed indicators.
Thresholds (35 °C, 5 °C, 0 °C) are **generic context thresholds** set in `config/thresholds.yaml`; they are not crop-specific and must be labelled as such.

### 5.7 Limits to state in the UI
* Satellite/model-based grid values are **not** field measurements. A point query returns the covering grid cell.
* Rainfall in the Delta is low and unevenly distributed; rainfall totals are context, **not irrigation availability** (slide 11).
* The default period (2020–2025) is short; the engine must offer a longer period and report how many complete windows were used.
* Strong winds, dust storms, heavy-rain/flash-flood events and local frost need local meteorological sources or official short-term forecasts (slide 22). The MVP does **not** score them.

---

## 6. Dataset 2 — Soil (priority 3)

### 6.1 HWSD v2.0 facts
**[VERIFIED]** from the FAO soils portal page:
* Resolution **1 km (30 arc-second)**; **seven depth layers**: 0–20, 20–40, 40–60, 60–80, 80–100, 100–150, 150–200 cm (v1.2 had two).
* Downloads named on the page: `HWSD2_RASTER.zip` (raster), `HWSD2_DB.zip` (database, `.mdb`), a Windows viewer setup, and the technical report/instructions PDF `cc3823en.pdf`.
* Attributes named on the page: effective CEC, total nitrogen, C/N ratio, aluminium saturation, **available water capacity (AWC), recalculated**, **USDA textural class**, **reference bulk density**, **rootable soil depth** (replaces reference soil depth), WRB reference groups/units.
* Licence: the page links FAO's general terms and does not state a data licence. A community mirror lists CC BY-NC-SA 3.0 (the linked URL points to 4.0). **[TODO]** read the terms before redistributing any HWSD-derived file.

**[VERIFIED]** from the Google Earth Engine community catalogue (bands exposed there): `HWSD2_ID, WISE30s_ID, COVERAGE, SHARE, WRB4, WRB_PHASES, WRB2_CODE, FAO90, KOPPEN, TEXTURE_USDA, REF_BULK_DENSITY (g/cm³), BULK_DENSITY (g/cm³), DRAINAGE, ROOT_DEPTH, AWC (mm/m), PHASE1, PHASE2, ROOTS, IL, ADD_PROP`.

**[RECALLED — verify in the technical report `cc3823en.pdf`]** the layers table also carries per-layer columns along the lines of `LAYER, TOPDEP, BOTDEP, COARSE, SAND, SILT, CLAY, TEXTURE_USDA, BULK, ORG_CARBON, PH_WATER, TOTAL_N, CEC_SOIL, ESP, ELEC_COND, GYPSUM`, linked to the raster through an ID such as `HWSD2_SMU_ID`. Confirm exact names, units and the join key before writing code that depends on them.

### 6.2 What the engine needs from soil [PPTX slide 6]
| Field | Meaning | Unit | Needed for |
|---|---|---|---|
| `soil_texture` | USDA texture class | category (12 classes) | soil-constraint indicator |
| `soil_depth_cm` | rootable depth or sampled depth | cm | context |
| `soil_ph` | soil pH | unitless | pH suitability |
| `organic_carbon` | organic carbon | **source-defined unit** (store the unit string) | soil-health context |
| `available_water_capacity` | AWC | **source-defined unit** (HWSD GEE band: mm/m) | water context |
| `soil_ec_dsm` | electrical conductivity (ECe) | dS/m | **salinity** — only meaningful from a field/lab test (slide 22) |
| `salinity_class` | derived from EC | category | UI |

USDA texture classes (12): `clay, silty clay, sandy clay, clay loam, silty clay loam, sandy clay loam, loam, silt loam, sandy loam, silt, loamy sand, sand` [RECALLED, standard].

Salinity bands (ECe, dS/m): breakpoints at **2, 4, 8, 16** [RECALLED]. Class **names differ between sources**, so the engine reports the numeric band ("4–8 dS/m") plus the source it used, not a vendor-specific label.

### 6.3 How to obtain the HWSD value for a point (manual, per slide 6)
1. Download `HWSD2_RASTER.zip` and `HWSD2_DB.zip` from the FAO page. Keep originals in `raw/soil/`.
2. In QGIS: load the raster, add the point (EPSG:4326), use *Sample raster values* (or Identify) to read the cell value (the soil-mapping-unit ID).
3. Open the database table(s), filter on that ID, read the seven layers. Record the rows used and the share (a mapping unit can contain several soil types — record which one you picked and why, or keep the dominant share).
4. Write `cleaned/soil_<locid>.json` (§6.4). Set `status: extracted`, `spatial_representation: gridded`, and note "1 km regional context — not a substitute for a farm soil test".
5. *Optional later:* `scripts/extract_hwsd.py` using `rasterio` + a `.mdb`→sqlite export, only after the engine works.

### 6.4 Soil record: `soil_<locid>.json`
```json
{
  "schema_version": 1,
  "location_id": "31.04_31.38",
  "source_type": "hwsd2",
  "source_name": "FAO/IIASA HWSD v2.0",
  "source_url": "https://www.fao.org/soils-portal/data-hub/soil-maps-and-databases/harmonized-world-soil-database-v20/en/",
  "dataset_version": "2.0",
  "retrieval_date": "YYYY-MM-DD",
  "spatial_representation": "gridded",
  "spatial_resolution": "1 km",
  "selection_note": "dominant soil unit in the cell; layers 0-20 and 20-40 cm used",
  "fields": {
    "soil_texture":  {"v": null, "unit": "USDA class", "status": "missing"},
    "soil_depth_cm": {"v": null, "unit": "cm", "status": "missing"},
    "soil_ph":       {"v": null, "unit": "pH", "status": "missing"},
    "organic_carbon":{"v": null, "unit": "<as in source>", "status": "missing"},
    "available_water_capacity": {"v": null, "unit": "<as in source>", "status": "missing"},
    "soil_ec_dsm":   {"v": null, "unit": "dS/m", "status": "missing"}
  },
  "limitations": "Regional estimate. Salinity needs field EC measurement."
}
```
The shipped file contains **no invented values**. Until a human fills it, the engine reports soil as `unknown` for the pilot.

### 6.5 Precedence and unknown handling
1. Farmer soil test (`status: farmer`, `field-measured`) overrides everything for the fields it contains.
2. HWSD record (`extracted`/`verified`) fills the rest as regional context.
3. Otherwise `missing`. The engine prints "Soil: unknown — add a soil test" and flags `soil_unknown`. If EC is missing, always add `salinity_unassessed` with the text "Measure EC in the field" (slide 22).

---

## 7. Dataset 3 — Crop reference and calendar (priority 2)

### 7.1 Schema [PPTX slide 8 + engine additions]
| Field | What to store | Unit / format | From |
|---|---|---|---|
| `crop_id`, `names` | stable id; English/Arabic/scientific names | text | PPTX |
| `sowing_window` | recommended local sowing window | `MM-DD` start/end | PPTX (`sowing_window_start/end`) |
| `growth_duration_days` | typical duration for region/variety | days | PPTX |
| `water_requirement_mm_ref` | reference seasonal water need | mm/season (min/max) | PPTX (`water_requirement_mm`) |
| `temperature_c` | documented suitable range | °C: `topmn, topmx, tmin, tmax, ktmp` + source | PPTX (`temperature_suitability`) |
| `drought_sensitivity` | qualitative class with evidence | low / medium / high + source | PPTX |
| `soil_constraints` | known limitations by soil conditions | structured: `salinity_threshold_ece_dsm`, `soil_ph_range`, note | PPTX (text/categories) |
| `category`, `family`, `n_fixer` | crop group, botanical family, nitrogen-fixing | enum/text/bool | engine addition |
| `stage_days` | FAO-56 stage lengths ini/dev/mid/late | days | engine addition |
| `kc` | FAO-56 single crop coefficients ini/mid/end | unitless | engine addition |
| `usual_slot` | winter or summer | enum | engine addition |

Every field is an object `{v, unit, src, status, note}` so that **each value has its source and status** ("Crop reference table with evidence", slide 15).

### 7.2 Season slots (Egypt)
| Slot | Nominal months | Typical crops [RECALLED] |
|---|---|---|
| `winter` | Nov – Apr | wheat, berseem, faba bean, sugar beet |
| `summer` | May – Oct | rice, maize, cotton, sorghum |
Egypt also has a short `nili` season (late summer–autumn). It is **not** in the MVP; add as a third slot later. A crop's actual growth window comes from its own `sowing_window` + `growth_duration_days` and may overlap a neighbouring slot (e.g. cotton sown in March, sugar beet harvested in June). Overlaps produce a `season_overlap` note, not an error.

### 7.3 Reference file: `FieldShift_Data/cleaned/crop_reference.yaml` (schema_version 2)
Created during the data sprint of 2026-10-30 and validated by `scripts/pre_engine_crop_validate.py` (V-CROP).
The original seed (schema_version 1) is superseded; the full quoting of every source row is in
`raw/crops/crop_table_verification_extract_20261030.md`, and raw fetch artifacts + `metadata/retrieval_log.jsonl` hold the provenance.

Upgrades vs the seed:
| Field state | Seed (v1) | Now (v2) |
|---|---|---|
| Sowing windows | all `placeholder` (GENERAL) | **extracted** for all 7 crops: wheat/faba/sugar beet (FAO calendar Delta region), rice & sorghum (FAO calendar Middle Egypt — no Delta row), maize (North-Delta peer-reviewed sowing-date trial + GIEWS corroboration), cotton (FAO-56 Egypt row month band Mar–May), berseem (FAO i3500e p.66 mid-Sep–late-Nov) |
| growth_duration_days | wheat/maize/rice/cotton/sugar beet/sorghum FAO-56 rows; faba & berseem `placeholder` | faba now **extracted** (FAO calendar Delta growing_period 180–190, midpoint 185; replaces 160). Berseem stays `placeholder` 200 (book prints a span "October to May", not a day count). FAO-56 values kept so stage_days keep summing (§7.4); Egypt FAO-calendar ranges quoted in notes |
| water_requirement_mm_ref | `missing` | **extracted** from manual Ch.2 Table 5 for 7 crops (wheat 450–650 'Barley/Oats/Wheat' row; maize 500–800; rice 450–700 paddy; cotton 700–1300; sugar beet 550–750; faba 300–500 'Bean' row — not faba-specific; sorghum 450–650). **berseem stays `missing`** (no row in the table, and i3500e prints no mm/season) |
| drought_sensitivity | `missing` | **extracted** for 7 crops from manual Ch.3 Table 14 qualitative classes (cotton low, sorghum low, rice high, wheat low-medium→medium, sugar beet low-medium→medium, maize medium-high→high, faba 'Bean' medium-high→high), collapsed by the documented more-sensitive-bound rule in the file's `drought_class_mapping`; numeric Ky quoted from FAO-66 Table 1. **berseem stays `missing`** (absent from Table 14 and FAO-66) |
| temperature_c / soil_ph_range | `missing` | **extracted** from the EcoCrop mirror for all 8 crops (units confirmed via variable lookup; variety-level rows: cotton = G. barbadense, berseem = T. alexandrinum); ktmp null where the mirror row lacks it |
| salinity_threshold_ece_dsm | 7 `placeholder` [RECALLED] | **extracted (table-verified)** for 7 crops: wheat 6.0, maize 1.7, rice 3.0, cotton 7.7 (row is G. hirsutum), sugar beet 7.0, sorghum 6.8, **faba corrected 1.6 → 1.5**. **berseem stays `missing`** (FAO-29 lists it only as a qualitative 'moderately sensitive' group, no ECe row) |

Remaining `placeholder`/`missing` values in the table (darkest for the engine, all berseem-related except engine-default stage splits):
berseem growth_duration_days (placeholder 200), water need, drought sensitivity, salinity; stage_days `missing` for faba & berseem (engine default split + `stage_split_assumed` flag).

### 7.4 Crop-table validation (see §12): stage days must sum to `growth_duration_days`; sowing windows must be valid dates; Kc values 0–2; salinity threshold ≥ 0; at least one crop per slot; every non-null value must have `src` and `status`.

### 7.5 Status of the fill-in list after the data sprint (2026-10-30)
Done by the sprint (source + status recorded in `crop_reference.yaml`):
1. ✅ Sowing windows (FAO calendars ×2 + FAO i3500e + North-Delta maize trial; citation in each crop).
2. ✅ Temperature ranges & pH (EcoCrop mirror; units verified).
3. ✅ Reference water needs (manual Table 5; berseem absent → `missing`).
4. ✅ Drought sensitivity (manual Table 14 classes + FAO-66 Table 1 Ky; collapse rule documented; berseem absent → `missing`).
5. ✅ Salinity thresholds (FAO-29 Table 4 verified; faba corrected to 1.5; berseem qualitative-only → `missing`).
6. ✅ FAO-56 re-verification (Tables 11/12 against the fetched page; footnote-digit artifacts documented; sorghum 140-vs-130 inconsistency confirmed as source-side).

Still open (human tasks, in this order):
1. **Berseem**: replace the placeholder 200-day duration with a locally confirmed value; a citable mm/season figure; a drought class; an ECe threshold if any Egyptian study gives one.
2. **Local Delta confirmation** of: maize window end (trial dates only), rice Delta sowing dates (FAO calendar has Middle Egypt only), sorghum Delta dates (Middle Egypt only), cotton day-level window (FAO-56 prints months only).
3. **Cotton ECe for G. barbadense** (FAO-29 row is G. hirsutum) — Egyptian long-staple tolerance is unverified.
4. **EcoCrop data licence** (the mirror's software licence is OGL-UK-3.0; the underlying FAO EcoCrop data licence needs a human check).
5. **Arabic crop names** — have a native speaker confirm قمح/ذرة شامية/أرز/قطن/بنجر السكر/فول بلدي/برسيم/ذرة رفيعة.
6. HWSD soil extraction for the pilot point (§6.3) — unchanged human/QGIS task.

## 8. Rotation strategies and rules

### 8.1 Illustrative templates: `references/rotation_templates.yaml`
Status: **`illustrative_for_review`** — the PPTX (Day 3) asks the team to *propose two rotation scenarios for review*. These are hypotheses to test with data, not recommendations. The existing rotation always comes from the user.

```yaml
schema_version: 1
status: illustrative_for_review
slots_per_year: [winter, summer]
templates:
- id: wheat_maize
  name: {en: "Wheat → Maize"}
  sequence: [{slot: winter, crop: wheat}, {slot: summer, crop: maize}]
  hypothesis: "Two cereals per year (same botanical family in both seasons)."
- id: faba_maize
  name: {en: "Faba bean → Maize"}
  sequence: [{slot: winter, crop: faba_bean}, {slot: summer, crop: maize}]
  hypothesis: "A winter legume before a summer cereal; test for water use and soil-related indicators."
- id: berseem_cotton
  name: {en: "Berseem → Cotton"}
  sequence: [{slot: winter, crop: berseem}, {slot: summer, crop: cotton}]
  hypothesis: "Winter forage legume then a fibre crop; cotton sowing overlaps late winter."
- id: wheat_rice
  name: {en: "Wheat → Rice"}
  sequence: [{slot: winter, crop: wheat}, {slot: summer, crop: rice}]
  hypothesis: "Winter cereal then flooded rice; expected to show the highest summer water demand."
- id: wheat_sorghum
  name: {en: "Wheat → Sorghum"}
  sequence: [{slot: winter, crop: wheat}, {slot: summer, crop: sorghum}]
  hypothesis: "Tests whether a summer sorghum lowers water demand versus maize/rice."
```
Each template is repeated for the chosen horizon (1–3 years). Slots may also be `fallow`.

### 8.2 Rotation rules: `references/rotation_rules.yaml`
**Rule from the PPTX (slide 11): apply rotation rules only where supported.** Each rule has `supported: false` until someone adds a citation. Unsupported rules are shown as *notes* and **do not change any score**.

```yaml
schema_version: 1
rules:
- id: R_FAMILY_REPEAT
  trigger: "same botanical family in consecutive seasons"
  effect_if_supported: {score: -0.10, applies_to: soil_health}
  note_key: "rule.family_repeat"     # "Same family in consecutive seasons: check pest/disease carry-over locally"
  supported: false
  evidence_needed: "extension or FAO source on pest/disease carry-over in same-family sequences"
- id: R_LEGUME_PRESENT
  trigger: "sequence includes a nitrogen-fixing crop (n_fixer = true)"
  effect_if_supported: {score: +0.10, applies_to: soil_health}
  note_key: "rule.legume_present"    # "Includes a nitrogen-fixing crop: possible nitrogen benefit, not quantified"
  supported: false
  evidence_needed: "FAO/extension source on nitrogen contribution of faba bean / berseem in Egyptian systems"
- id: R_BARE_PERIOD
  trigger: "a season slot is fallow or the crop window leaves months uncovered"
  effect_if_supported: {score: -0.05, applies_to: soil_health}
  note_key: "rule.bare_period"
  supported: false
  evidence_needed: "source linking bare periods to erosion/organic-matter loss under Delta conditions"
- id: R_HIGH_WATER_SUMMER
  trigger: "summer crop's estimated ETc is in the top tier of the compared strategies"
  effect: "data-driven; handled by the water indicators, not a separate score"
  supported: true
- id: R_SEASON_OVERLAP
  trigger: "crop window starts before the previous crop's window ends"
  effect: "note only"
  note_key: "rule.season_overlap"
  supported: true
```

### 8.3 Existing rotation
A **one-year cycle** (winter slot + summer slot) repeated over the horizon. Built from the last crop and its season (slide 10); the other slot is asked explicitly (a crop, `fallow`, or "not grown") and is never guessed. Earlier crops (`previous_2_crops`) are history context for rotation-rule notes only. Flags: `baseline_from_history` when the user confirms both slots; `baseline_assumed` if they were unsure and chose a default they accepted. A user with a genuine 2-year pattern may enter four slots.

---

## 9. Farmer inputs [PPTX slide 10]

### 9.1 Fields
**Farm profile**
| Field | Type | Allowed values | Unknown? | If unknown |
|---|---|---|---|---|
| `farm_location` | lat/lon (or boundary later) | WGS84 decimals | no | required |
| `previous_crop` | crop_id / `fallow` / `other:<text>` | crop table ids | yes | flag `history_unknown` |
| `previous_crop_season` | enum | winter, summer | yes | flag `season_unknown`; next slot assumed = winter |
| `previous_2_crops` | list of ≤2 crop ids (seasons before) | crop ids / fallow | yes (skip) | shorter history |
| `irrigation_source` | enum | `canal`, `well`, `mixed`, `rainfed_only`, `other`, `unknown` | yes | flag `irrigation_unknown` |
| `water_availability` | enum | `limited`, `moderate`, `high`, `unknown` | yes | water-access comparison skipped |
| `soil_test_available` | bool | yes/no | – | no → HWSD record or unknown |
| `soil_test` | object | texture class, pH, organic carbon (+unit), EC dS/m, depth cm | each field skippable | field stays `missing` |
| `farm_area_ha` | float ≥ 0 (optional) | – | skip | not used in scoring |

**Priorities** — ranked by the user, not assumed (slide 10): `reduce_water_use`, `support_soil_health`, `improve_climate_resilience`, `maintain_productivity`, optional `budget_market` (only if the user has a constraint; **not scored**, no data source).
Converted to weights with rank-order centroid weights: n=3 → 0.611/0.278/0.111; n=4 → 0.521/0.271/0.146/0.063; n=5 → 0.457/0.257/0.157/0.090/0.040 (`w_i = (1/n)·Σ_{k=i..n} 1/k`).

**Analysis choices** (engine, not PPTX): data mode (`offline`/`fetch`/`auto`), climate period (default 2020–2025; options 2011–2025 and custom), horizon in years (1–3, default 2), strategy selection (existing + templates/custom).

### 9.2 Example profile (`runs/<id>/profile.json`)
```json
{
  "schema_version": 1,
  "created_at": "2026-10-30T10:05:00+03:00",
  "location": {"latitude": 31.04, "longitude": 31.38, "crs": "EPSG:4326", "selected_on": "2026-10-30",
               "name": "Pilot point near Mansoura", "spatial_type": "point", "coordinates_illustrative": true},
  "farm": {"previous_crop": "wheat", "previous_crop_season": "winter", "previous_2_crops": ["maize", "berseem"],
           "irrigation_source": "canal", "water_availability": "limited", "soil_test_available": false, "farm_area_ha": null},
  "soil_test": null,
  "priorities": {"ranking": ["reduce_water_use", "support_soil_health", "improve_climate_resilience", "maintain_productivity"],
                 "budget_market_note": null},
  "analysis": {"data_mode": "offline", "period": {"start": 2020, "end": 2025}, "horizon_years": 2},
  "strategies": {"existing": {"source": "from_history"}, "candidates": ["faba_maize", "wheat_sorghum"]},
  "consent": {"stores_personal_data": false}
}
```
No names, phone numbers, or exact addresses are collected. If the project later stores profiles for real users, add explicit consent (slide 10).

---

## 10. Optional datasets (only after everything else works)

### 10.1 NASA SMAP (priority 4) [PPTX slide 7]
* Chosen product: NASA/NSIDC `SPL3SMP_E`, Version 6, enhanced L3 radiometer, daily 9 km grid. Product page: https://nsidc.org/data/spl3smp_e/versions/6 .
* Local standardized CSV fields: `observation_date`, `soil_moisture` (m³/m³), product `quality_flag`, `quality_status`, `product_id`, actual `spatial_resolution_km`, `product_version`, `retrieved`.
* Access requires a NASA Earthdata Login. Phase 9 reads a quality-interpreted local extract; it does not authenticate, download, or decode product HDF5/bit flags.
* Limits (slide 7): some enhanced products are around 9 km; a pixel may cover several fields and land uses; **surface moisture is not root-zone water available to crops**; use trends and context, **not irrigation prescriptions**.
* Engine use: context panel and an optional "soil-moisture context" indicator; never a core score term. Keep `quality_flag` and version. Choose the exact product in the build and record it in `sources.csv` **[TODO]**.

### 10.2 MODIS MOD13Q1 NDVI/EVI (priority 5) [PPTX slide 9]
* Chosen product: Terra `MOD13Q1.061`, 250 m, 16-day composites, scale factor 0.0001 for NDVI/EVI; raw fill value -3000 and valid raw range -2000..10000. Product DOI: https://doi.org/10.5067/MODIS/MOD13Q1.061 .
* Local standardized CSV fields: `observation_date`, raw integer `ndvi`/`evi`, `pixel_quality` (0 good, 1 marginal, 2 snow/ice, 3 cloudy), `product_id`, `product_version`, `scale_factor`, `retrieved`.
* Access: LAADS DAAC product page or Google Earth Engine collection `MODIS/061/MOD13Q1` (from the PPTX link).
* Limits (slide 9): greenness is **not** a direct measure of soil health; mixed pixels and small fields complicate interpretation; supporting context, not the core rotation score.
* Engine use: seasonal greenness curve beside the crop calendar; possibly an "typically low-greenness months" note for the bare-field idea. Never a score term in the MVP.

---

## 11. Climate-risk linkage (condensed from the Arabic section, slides 18–25)

### 11.1 Agricultural problems the app should track (slide 19)
Salinity · drought and water stress · soil degradation (not attributable to climate alone) · shortage or irregularity of irrigation water.

### 11.2 Sudden weather swings (slide 20) — vary by region and season; check per location and crop
Heat/cold-wave changes (timing, duration, intensity) · strong winds and dust storms · heavy rain and local flash floods · frost only in exposed areas/periods (**not assumed for all of Egypt**).

### 11.3 Impact chain (slide 21): climate hazard → plant/soil/water response → farm decision
| Outcome | Trigger | Proposed app response |
|---|---|---|
| Plant damage | extreme heat, frost, strong wind/rain | early warning, track growth stage, suitable protection |
| Lower productivity | heat or water stress, high salinity | suggest a more suitable crop/variety, more efficient irrigation management |
| Shifted sowing/harvest dates | changed temperatures and timing of weather events | use forecasts + crop calendar, update the suggestion |
| Harder irrigation planning | higher evaporation, shortage or irregular supply | schedule by crop, soil, weather and water availability |

### 11.4 Hazard → data → engine status (slide 22, with MVP decision)
| Hazard / topic | Data named in the plan | Limit stated in the plan | MVP status |
|---|---|---|---|
| Heat and cold waves | POWER daily Tmax/Tmin (°C), compared with crop-suitable limits and growth stage | — | **In** (hot-day/cold-day counts; crop-range fit when ranges exist) |
| Drought and water stress | rainfall + temperature; SMAP when available | satellite soil moisture ≠ direct measure for a small field | **In** (ETc vs rainfall); SMAP **later** |
| Salinity and soil degradation | HWSD regional + recent soil sample | soil database ≠ field EC | **In** only as soil-constraint indicator if EC given; else `salinity_unassessed` |
| Rain and wind | local meteorological source or official short-term forecast | local extremes need a suitable source | **Out** (listed as limitation) |
| Sowing and harvest timing | crop calendar + weather + growth stage | differs by crop, variety, location | **In** as window-based context (not a forecast) |
| Irrigation water shortage | farmer-reported availability | no satellite source in the plan | **In** as an input only |

### 11.5 Prototype alert chain (slide 23)
1 Identify the field (exact coordinates + crop + sowing date) → 2 Collect data (weather, soil, water, crop calendar) → 3 Quality check (units, period, missing values) → 4 Compute indicators (extreme heat, water stress, salinity risk) → 5 Show the recommendation (**risk level, reason, action, source**). The app never gives a definitive verdict from a single indicator; it shows a preliminary risk, states uncertainty and asks for local data when needed.

### 11.6 Methodological notes (slide 25) — reproduce in the UI "About" screen
* Climate change raises or shifts some risks, but salinity, soil degradation and irrigation shortage also depend on management, water quality and infrastructure.
* Do not generalise frost or heavy rain to all of Egypt; specify area and season.
* The Mansoura coordinates in the plan are illustrative, not a real field.
* No field-specific advice before data are downloaded and verified.
* Every recommendation shows its source, update date and accuracy limits.

---

## 12. Validation checks catalogue

Severity: `error` = stop that dataset, `warn` = continue with a flag, `info` = log only. Thresholds marked † are engine heuristics, tunable in `config/thresholds.yaml`.

| ID | Applies to | Rule | Severity | Flag |
|---|---|---|---|---|
| V-POWER-001 | download | HTTP status 200 and non-empty body | error | `download_failed` |
| V-POWER-002 | CSV | header contains all five requested parameter names | error | `header_mismatch` |
| V-POWER-003 | CSV | date column builds without errors; dates unique and sorted | error | `bad_dates` |
| V-POWER-004 | dates | no gaps: row count = days between start and end (inclusive) | warn | `date_gaps` |
| V-POWER-005 | values | count of missing-code cells per column; ≥ 5 %† → warn, ≥ 20 %† → error | warn/error | `climate_missing_values` |
| V-POWER-006 | values | `t_min ≤ t_mean ≤ t_max` | warn | `inconsistent_temperature` |
| V-POWER-007 | values | plausible ranges†: temperature −10…55 °C; rain 0…200 mm/day; solar 0…40 MJ/m²/day | warn | `out_of_range` |
| V-POWER-008 | period | at least 5 complete years requested, ≥ 3 complete season windows per crop | warn | `climate_short_record` / `few_windows` |
| V-POWER-009 | units | assert unit strings match §5.1; no silent conversions | error | `unit_mismatch` |
| V-POWER-010 | header | lat/lon in header within 1° of requested point | warn | `grid_cell_far` |
| V-CROP-001 | crop table | every non-null value has `src` and `status` from the enum | error | – |
| V-CROP-002 | crop table | `stage_days` sum = `growth_duration_days` | warn | `stage_sum_mismatch` |
| V-CROP-003 | crop table | sowing window dates valid; `start`/`end` parse as MM-DD | error | – |
| V-CROP-004 | crop table | Kc values between 0 and 2; kc.end present with kc.ini and kc.mid | error | – |
| V-CROP-005 | crop table | each slot has ≥ 2 crops; each crop's `usual_slot` exists | error | – |
| V-CROP-006 | crop table | count of `placeholder` / `missing` values reported in the "data readiness" screen | info | – |
| V-SOIL-001 | soil | pH 3–10†; EC ≥ 0; texture in the 12 USDA classes; depth 0–300 cm† | error | `soil_invalid` |
| V-SOIL-002 | soil | unit string present for organic carbon and AWC | warn | `unit_missing` |
| V-PROFILE-001 | profile | lat/lon inside Egypt box (warn) | warn | `outside_egypt` |
| V-PROFILE-002 | profile | every priority appears once in the ranking | error | – |
| V-PROFILE-003 | profile | horizon 1–3 years; period start < end ≤ current year | error | – |
| V-META-001 | all | each used source has name, URL, version, retrieval date, coverage, resolution, units, missing-value rule | error | `metadata_incomplete` |

---

## 13. Quality-flag catalogue (shown in "Data quality" and per strategy)

| Flag | Meaning | Confidence effect |
|---|---|---|
| `coordinates_illustrative` | pilot point, not a real field | results labelled illustrative |
| `soil_unknown` / `soil_partial` / `soil_regional_only` | no soil data / some fields / HWSD only | −1 level for soil indicators |
| `salinity_unassessed` | no EC measured | note: "Measure EC in the field" |
| `climate_short_record` / `few_windows` | short period / < 3 complete windows | −1 level |
| `climate_missing_values` / `date_gaps` | data holes (never filled) | −1 level if ≥ 5 % |
| `crop_value_placeholder` / `crop_value_missing` | crop table values need replacing | −1 level per strategy |
| `stage_split_assumed` | stage lengths missing; default split used | indicator marked `estimated` |
| `et0_estimated` | ET0 from Hargreaves–Samani, not measured | indicator marked `estimated` |
| `rice_gross_water_underestimated` | flooded-rice losses not in ETc | note on rice strategies |
| `baseline_assumed` / `baseline_from_history` | how the existing rotation was built | −1 level if assumed |
| `history_unknown` / `season_unknown` | farmer did not know | note |
| `irrigation_unknown` | source unknown | water-access comparison skipped |
| `season_overlap` | crop windows overlap | note |
| `rule_unsupported` | rotation rule shown as a note only | note |
| `priority_unscored` | `budget_market` has no data | note |
| `outside_egypt` | location outside the Egypt box | warning |

Confidence levels: `high`, `medium`, `low`. Start at `high` per strategy, apply the effects above, floor at `low`. Always print the flags that caused the level.

---

## 14. Data dictionary seed: `metadata/data_dictionary.csv`

Columns (PPTX slide 12): `field_name, definition, unit, source_url, dataset_version, spatial_resolution, time_resolution, coverage_start, coverage_end, missing_value_rule, limitations`.
Create the file with these rows; the code fills `coverage_*` and `dataset_version` after each retrieval.

```csv
field_name,definition,unit,source_url,dataset_version,spatial_resolution,time_resolution,coverage_start,coverage_end,missing_value_rule,limitations
date,Calendar date of the daily record,YYYY-MM-DD,https://power.larc.nasa.gov/docs/services/api/temporal/daily/,<from header>,gridded cell,daily,<set at retrieval>,<set at retrieval>,rows must exist for every day,Time basis (local solar vs UTC) to confirm
t_mean_c,Daily mean air temperature at 2 m (T2M),degC,https://power.larc.nasa.gov/docs/services/api/temporal/daily/,<from header>,gridded cell (see header),daily,<set>,<set>,-999 -> NaN (confirm code in header),Grid value not a station measurement
t_max_c,Daily maximum air temperature at 2 m (T2M_MAX),degC,https://power.larc.nasa.gov/docs/services/api/temporal/daily/,<from header>,gridded cell,daily,<set>,<set>,-999 -> NaN,Heat-stress context; not leaf or canopy temperature
t_min_c,Daily minimum air temperature at 2 m (T2M_MIN),degC,https://power.larc.nasa.gov/docs/services/api/temporal/daily/,<from header>,gridded cell,daily,<set>,<set>,-999 -> NaN,Frost needs local confirmation
rain_mm,Corrected precipitation (PRECTOTCORR),mm/day,https://power.larc.nasa.gov/docs/services/api/temporal/daily/,<from header>,gridded cell,daily,<set>,<set>,-999 -> NaN,Not a rain-gauge record; rainfall is not irrigation availability
solar_mj_m2,All-sky surface shortwave downward radiation (ALLSKY_SFC_SW_DWN),MJ/m2/day,https://power.larc.nasa.gov/docs/services/api/temporal/daily/,<from header>,gridded cell (coarser),daily,<set>,<set>,-999 -> NaN,Solar-energy context only
qc,Engine quality flags for the row,text,n/a,engine,n/a,daily,<set>,<set>,empty = ok,Never used to fill values
hot_days_tmax_ge_35,Days with Tmax at or above the generic hot-day threshold,days,derived from t_max_c,engine,n/a,per season window,<set>,<set>,windows with missing data excluded,Generic threshold not crop-specific
frost_days_tmin_le_0,Days with Tmin at or below 0 degC,days,derived from t_min_c,engine,n/a,per season window,<set>,<set>,windows with missing data excluded,Often zero in the Delta; do not generalise to all Egypt
rain_total_mm,Sum of rain_mm over a crop or season window,mm,derived from rain_mm,engine,n/a,per window,<set>,<set>,windows with missing data excluded,Context only
et0_mm_day,Reference evapotranspiration (Hargreaves-Samani) from Tmax/Tmin and latitude,mm/day,derived (FAO-56 Eq. 52 / Eq. 21),engine,n/a,daily,<set>,<set>,NaN if Tmax/Tmin missing,Estimate; flag et0_estimated
etc_mm,Crop evapotranspiration over a window = sum of Kc x ET0,mm/window,derived (FAO-56 Ch.6),engine,n/a,per window,<set>,<set>,NaN if Kc/stage/ET0 missing,Reference crop water need not an irrigation schedule
soil_texture,USDA textural class,category,https://www.fao.org/soils-portal/data-hub/soil-maps-and-databases/harmonized-world-soil-database-v20/en/,2.0,1 km,static,n/a,n/a,missing stays missing,Regional estimate; farm test preferred
soil_depth_cm,Rootable or sampled soil depth,cm,same as soil_texture,2.0,1 km,static,n/a,n/a,missing stays missing,Definition differs between HWSD and a farm sample
soil_ph,Soil pH,unitless,same as soil_texture,2.0,1 km,static,n/a,n/a,missing stays missing,Confirm HWSD column name and pH method
organic_carbon,Soil organic carbon,<source-defined unit>,same as soil_texture,2.0,1 km,static,n/a,n/a,missing stays missing,Store the unit string from the source
available_water_capacity,Soil available water capacity,<source-defined unit> (GEE band AWC is mm/m),same as soil_texture,2.0,1 km,static,n/a,n/a,missing stays missing,Context for water indicators
soil_ec_dsm,Electrical conductivity of saturated paste extract,dS/m,farmer soil test,farmer,field-measured,dated sample,<sample date>,<sample date>,missing stays missing,Needed to assess salinity; HWSD is not a substitute
crop_id,Stable crop identifier,text,FieldShift_Data/cleaned/crop_reference.yaml,seed v1,n/a,n/a,n/a,n/a,required,n/a
sowing_window,Recommended local sowing window,MM-DD start/end,https://cb.apps.fao.org/country.jsp?code=EGY&lang=en,<to fill>,national,seasonal,n/a,n/a,missing stays missing,Varies by variety and location
growth_duration_days,Typical crop cycle length,days,https://www.fao.org/4/x0490e/x0490e0b.htm,FAO-56,regional analogue,per crop,n/a,n/a,missing stays missing,FAO-56 Table 11 is a general guide
stage_days,Initial/development/mid/late stage lengths,days,https://www.fao.org/4/x0490e/x0490e0b.htm,FAO-56,regional analogue,per crop,n/a,n/a,missing -> default split + flag,Not Egypt-specific except the cotton row
kc,Single crop coefficients ini/mid/end,unitless,https://www.fao.org/4/x0490e/x0490e0b.htm,FAO-56,n/a,per stage,n/a,n/a,missing stays missing,End values printed as ranges; first printed value used
water_requirement_mm_ref,Reference seasonal crop water need (min/max),mm/season,https://www.fao.org/4/S2022E/s2022e07.htm,<to fill>,n/a,per season,n/a,n/a,missing stays missing,Reference not prescription
temperature_c,Suitable temperature range topmn/topmx/tmin/tmax/ktmp,degC,https://gaez.fao.org/pages/ecocrop,<to fill>,n/a,n/a,n/a,n/a,missing stays missing,Confirm units and licence
drought_sensitivity,Qualitative sensitivity to water deficit,low|medium|high,<to fill FAO-33>,<to fill>,n/a,n/a,n/a,n/a,missing stays missing,Needs cited evidence
salinity_threshold_ece_dsm,Crop salinity tolerance threshold (ECe),dS/m,FAO Irrigation and Drainage Paper 29 Rev.1,recalled,n/a,n/a,n/a,n/a,missing stays missing,Placeholder until verified
previous_crop,Crop grown in the last season (farmer),crop_id,farmer,n/a,field,per season,n/a,n/a,unknown allowed -> flag,Self-reported
irrigation_source,Main irrigation source (farmer),enum,farmer,n/a,field,n/a,n/a,n/a,unknown allowed -> flag,Self-reported
water_availability,Farmer-reported water availability,enum limited|moderate|high,farmer,n/a,field,seasonal,n/a,n/a,unknown allowed -> flag,Not satellite-derived
priorities,Farmer ranking of goals,ordered list,farmer,n/a,n/a,n/a,n/a,n/a,required,Ranking converted to weights; not a measure of importance in agronomic terms
```

---

## 15. Collection runbook (the PPTX 3-day sprint, mapped to the engine)

Priority order: **POWER → FAO crop calendar & water → HWSD soil → SMAP → MODIS.**

**Day 1 — Climate**
1. Open the API link (§5.2). Save the CSV into `raw/power/` and write the `.request.json` sidecar. (Engine command: `fieldshift fetch power --pilot`.)
2. Check headers, dates, units, gaps with `fieldshift validate --climate`; read §5.3 and write down what was confirmed.
3. Produce the climate summary (`fieldshift climate --pilot`).

**Day 2 — Soil and crops**
1. Get HWSD properties for the pilot point (§6.3); write `soil_<locid>.json` (or leave `missing`).
2. Fill the crop table (§7.5): GIEWS calendar → EcoCrop temperature → FAO water needs → drought sensitivity → soil ranges. Cite every value; flag unavailable ones.
3. `fieldshift validate --crops` must show no `error`; list remaining placeholders.

**Day 3 — Hand-over**
1. Clean/standardise tables; regenerate `cleaned/` from `raw/` by code.
2. Complete `data_dictionary.csv`, `sources.csv`, `retrieval_log.jsonl`, and `README.md` (limits, missing fields).
3. Share raw + cleaned files; review the two or more candidate rotation templates (§8.1) and keep or change them.

**Definition of done:** a developer can reproduce the data and understand each variable without a verbal explanation.

---

## 16. Source directory

From the PPTX (slides 13–14, 24):
* NASA POWER daily API documentation — https://power.larc.nasa.gov/docs/services/api/temporal/daily/
* NASA POWER portal — https://power.larc.nasa.gov/
* FAO/IIASA HWSD (land-water page) — https://www.fao.org/land-water/resources/tools/databases/hwsd/en
* FAO Soil Portal, HWSD reference — https://www.fao.org/soils-portal/soil-survey/soil-maps-and-databases/harmonized-world-soil-database-v12/en/
* NSIDC SMAP — https://nsidc.org/data/smap
* NASA-USDA global soil moisture data — https://earth.gsfc.nasa.gov/hydro/data/nasa-usda-global-soil-moisture-data
* FAO GIEWS Egypt country brief — https://cb.apps.fao.org/country.jsp?code=EGY&lang=en
* FAO crop water information — https://www.fao.org/4/S2022E/s2022e07.htm
* FAO crop water requirements overview — https://www.fao.org/4/s2022e/s2022e02.htm
* NASA LAADS MOD13Q1 — https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD13Q1
* Google Earth Engine MODIS catalog — https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD13Q1
* FAO country brief PDF (Egypt) — https://cb.apps.fao.org/country/EGY/pdf/EGY.pdf
* Reference list on climate risk — see `REF_CLIMATE_RISK` in §4.

Added in the hand-over session:
* FAO-56 Chapter 6 (Tables 11 and 12) — https://www.fao.org/4/x0490e/x0490e0b.htm
* FAO HWSD v2.0 page — https://www.fao.org/soils-portal/data-hub/soil-maps-and-databases/harmonized-world-soil-database-v20/en/
* GEE community catalogue entry for HWSD — https://gee-community-catalog.org/projects/hwsd/
* FAO EcoCrop (GAEZ page) — https://gaez.fao.org/pages/ecocrop
* EcoCrop GitHub mirror — https://github.com/OpenCLIM/ecocrop

Record the retrieval date for each in `references/links.md` the first time it is opened.

---

## 17. Known gaps and open questions

1. NASA POWER: live response format, `-999` code, grid size, time basis, parameter-per-request limit — **unverified** (§5.3).
2. HWSD v2.0: exact column names/units for pH, organic carbon, EC, texture percentages and the raster-to-table join key — **unverified** (§6.1). The pilot soil record is empty by design.
3. Crop table: sowing windows, faba/berseem durations, Arabic names, salinity thresholds — `placeholder`; temperature, drought, water-need and pH ranges — `missing`.
4. FAO-56 extraction: stray footnote digits, a sorghum total mismatch, and ranges for Kc end — confirm in the original tables.
5. The generic hot/cold thresholds (35 °C, 5 °C, 0 °C) and the indicator bands in `CLAUDE.md` are engine heuristics, not literature values.
6. Rotation rules are all unsupported (notes only) until someone adds citations.
7. SMAP product choice and Earthdata access — **[TODO]**.
8. Licence terms of HWSD and EcoCrop mirrors — **[TODO]**.
9. Real field coordinates and (ideally) a real soil test for one field — **needed from the team** before any result is presented as a finding.
10. Future-climate projections, additional NASA datasets (SRTM, GPM, GRACE, ECOSTRESS) and field-level maps are **out of the MVP** and belong to a later phase of the web application.
