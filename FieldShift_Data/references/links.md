# Source links and retrieval dates (DATA.md §16)

> "Record the retrieval date for each in `references/links.md` the first time it is opened."

## Opened / used during the engine data sprint

| Source | URL | First opened | Notes |
|---|---|---|---|
| NASA POWER daily API (live request) | https://power.larc.nasa.gov/api/temporal/daily/point | **2026-10-30** | HTTP 200; 2011–2025 pilot record saved to `raw/power/`; all §5.3 items confirmed |
| NASA POWER docs (daily) | https://power.larc.nasa.gov/docs/services/api/temporal/daily/ | 2026-10-30 | linked from API error message; docs page not deep-read yet |
| FAO GIEWS Egypt country brief | https://cb.apps.fao.org/country.jsp?code=EGY&lang=en | (pending — see bottom) | sowing windows to be extracted |
| FAO country brief PDF (Egypt) | https://cb.apps.fao.org/country/EGY/pdf/EGY.pdf | (pending) | crop calendar PDF |
| FAO-56 Ch. 6 (Tables 11/12) | https://www.fao.org/4/x0490e/x0490e0b.htm | **2026-10-30** | fetched; artifact `raw/crops/fao56_ch6_tables11_12_fetched_20261030.txt` (sha256 36199f…) |
| FAO crop calendar — DHLG platform API (EG) | https://api-cropcalendar.apps.fao.org/api/v1/countries/EG/cropCalendar?language=en | **2026-10-30** | 65 Egypt crops, Delta sessions + growing_period; artifact in `raw/crops/`; lastUpdated 26/02/2021 |
| FAO crop calendar — data catalog export (BigQuery) | https://api.data.apps.fao.org/api/v2/bigquery?sql_url=<catalog resource>&crop_process=all&crop=all&download=true | **2026-10-30** | 1.3 MB CSV, cross-checked with DHLG; both agree |
| FAO water-management manual ch.2 (Table 5) | https://www.fao.org/4/S2022E/s2022e02.htm | **2026-10-30** | seasonal water needs; berseem absent |
| FAO water-management manual ch.3 (Tables 6/7/14) | https://www.fao.org/4/S2022E/s2022e07.htm | **2026-10-30** | drought-sensitivity classes; growing-period/stage tables |
| FAO water-management manual ch.4 (paddy rice) | https://www.fao.org/4/S2022E/s2022e08.htm | **2026-10-30** | SAT/PERC/WL formulae for rice |
| FAO-29 Rev.1 (Ayers & Westcot) Tables | https://www.fao.org/4/T0234e/T0234E03.htm | **2026-10-30** | ECe 100%-yield thresholds verified; faba 1.5; berseem qualitative only |
| FAO-66 Ch.2 (reproduces FAO-33 seasonal Ky) | https://www.fao.org/4/i2800e/i2800e02.pdf | **2026-10-30** (search-verified, not archived) | Ky: cotton 0.85, sorghum 0.9, sugarbeet 1.0, maize 1.25, beans 1.15, winter wheat 1.05; no rice row |
| FAO i3500e Egyptian Clover (Dost et al. 2014) | https://openknowledge.fao.org/server/api/core/bitstreams/947fa627-c9f2-4f67-b725-e0ef30d220c7/content | **2026-10-30** | artifact `fao_i3500e_berseem_20261030.pdf`; p.26/32/66 facts |
| EcoCrop mirror (OpenCLIM/ecocrop) | https://raw.githubusercontent.com/OpenCLIM/ecocrop/main/EcoCrop_DB.csv | **2026-10-30** | sha256 4187e8…; 2568 rows; latin-1; units confirmed (°C, pH, KTMP definitions) |
| GIEWS Egypt country brief (PDF) | https://cb.apps.fao.org/country/EGY/pdf/EGY.pdf | **2026-10-30** | ref. 30-06-2026; "rice and maize sowing began in May" |
| USAID/USDA FAS crop-calendar PNG (Egypt) | https://www.fas.usda.gov/sites/default/files/ipad/crop-calendars/... | 2026-10-30 | **HTTP 403 blocked** (twice, incl. browser UA) — not usable |
| Hegab et al. 2019 maize sowing trial (DOI) | https://doi.org/10.21608/ajs.2019.43523 | 2026-10-30 (abstract) | North-Delta sowing dates 1 May/1 June/1 July; PDF 429 — not archived |
| FAO crop water pages | https://www.fao.org/4/S2022E/s2022e07.htm · s2022e02.htm | (pending) | reference seasonal water need |
| FAO EcoCrop | https://gaez.fao.org/pages/ecocrop · mirror https://github.com/OpenCLIM/ecocrop | (pending) | temperature ranges, pH ranges |
| FAO-29 Rev.1 (Ayers & Westcot) | see §4 | (pending) | salinity thresholds verification |
| FAO-33 (Ky) | see §4 | (pending) | drought sensitivity |
| HWSD v2.0 | https://www.fao.org/soils-portal/data-hub/soil-maps-and-databases/harmonized-world-soil-database-v20/en/ | (pending) | pilot extraction (human task) |

## From the PPTX (not yet opened by the engine, listed for completeness)

* NASA POWER portal — https://power.larc.nasa.gov/
* FAO/IIASA HWSD land-water page — https://www.fao.org/land-water/resources/tools/databases/hwsd/en
* FAO Soil Portal HWSD v1.2 reference — https://www.fao.org/soils-portal/soil-survey/soil-maps-and-databases/harmonized-world-soil-database-v12/en/
* NSIDC SMAP — https://nsidc.org/data/smap
* NASA-USDA global soil moisture — https://earth.gsfc.nasa.gov/hydro/data/nasa-usda-global-soil-moisture-data
* NASA LAADS MOD13Q1 — https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD13Q1
* GEE MODIS catalog — https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD13Q1
* GEE community HWSD — https://gee-community-catalog.org/projects/hwsd/
* OECD (2026) Egypt farming/food — https://www.oecd.org/en/publications/policies-for-the-future-of-farming-and-food-in-egypt_cab0cefd-en.html
* FAO Near East climate change — https://www.fao.org/neareast/main-topics/action-areas/addressing-climate-change-in-agrifood-systems/addressing-climate-change-in-agrifood-systems/en
* Knowledge4Policy/IFPRI Egypt climate — https://knowledge4policy.ec.europa.eu/publication/climate-change-egypt%E2%80%99s-agriculture_en
* World Bank CCKP Egypt profile — https://climateknowledgeportal.worldbank.org/sites/default/files/2021-01/15723-WB_Egypt%20Country%20Profile-WEB.pdf
