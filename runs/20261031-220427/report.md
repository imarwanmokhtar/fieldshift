# Field Shift — Rotation comparison

Supports, does not replace, farmer judgment and local expertise.

## Inputs

| Input | Value |
|---|---|
| start | new |
| loc_mode | pilot |
| coords_real | True |
| prev_crop | wheat |
| prev_season | winter |
| has_earlier | True |
| prev2_a | rice |
| prev2_b | cotton |
| irrigation | canal |
| water_avail | high |
| soil_test | True |
| soil_texture | clay |
| soil_ph | 7.0 |
| soil_oc | 2.0 |
| soil_ec | 7.0 |
| soil_depth | 30.0 |
| soil_date | 2026-01-01 |
| area | 10.0 |
| prio_rank | improve_climate_resilience |
| prio_rank_list | ['maintain_productivity', 'support_soil_health', 'reduce_water_use', 'improve_climate_resilience'] |
| budget_market | none |
| data_mode | offline |
| period | 2020-2025 |
| horizon | 3 |
| strat_source | proposed |
| existing_edit | True |
| existing_other_crop | wheat |
| review | run |
| latitude | 31.04 |
| longitude | 31.38 |
| raw_sha256 | 465e89e32f276647e840ab4f4e86bf3735dbd48a4e17cec2021a1fabd6a23390 |

## Data sources

| Source | Version | Retrieved | Period | Resolution | Type | Units | Missing values | Status | URL |
|---|---|---|---|---|---|---|---|---|---|
| NASA POWER daily API (AG community) | MERRA-2 temperatures+precip / CERES SYN1deg solar | 2026-10-30 | 2020-2025 | 0.5 x 0.625 deg (met; CERES SYN1deg solar) | gridded (point query returns covering cell) | {'temperature': '°C', 'rain': 'mm/day', 'solar': 'MJ/m²/day'} | -999 -> NaN (confirmed in header) | extracted | https://power.larc.nasa.gov/api/temporal/daily/point |
| EcoCrop crop requirements database mirror (OpenCLIM/ecocrop) | mirror of FAO EcoCrop | 2026-10-30 | n/a | global (species/variety level) | non-spatial reference | degC; pH; days | NaN stays missing | extracted | https://raw.githubusercontent.com/OpenCLIM/ecocrop/main/EcoCrop_DB.csv |
| FAO29_T4 | — | — | reference | — | non-spatial reference | — | — | extracted |  |
| FAO56_T11 | — | — | reference | — | non-spatial reference | — | — | extracted |  |
| FAO56_T12 | — | — | reference | — | non-spatial reference | — | — | extracted |  |
| FAO crop calendar for Egypt (DHLG API + data-catalog export, lastUpdated 2021-02-26) | lastUpdated 26/02/2021 | 2026-10-30 | n/a | national + agro-ecological zones | non-spatial reference | MM-DD windows; days | absent crop = no row | extracted | https://api-cropcalendar.apps.fao.org/api/v1/countries/EG/cropCalendar?language=en |
| FAO i3500e 'Egyptian Clover - King of Forage Crops' (Dost et al. 2014) | 2014 | 2026-10-30 | n/a | Egypt-focused monograph | non-spatial reference | text (dates, spans) | no mm/season figure printed | extracted | https://openknowledge.fao.org/server/api/core/bitstreams/947fa627-c9f2-4f67-b725-e0ef30d220c7/content |
| FAO_WATER_T14 | — | — | reference | — | non-spatial reference | — | — | extracted |  |
| FAO_WATER_T5 | — | — | reference | — | non-spatial reference | — | — | extracted |  |
| FARMER_SOIL_TEST | — | — | reference | — | non-spatial reference | — | — | extracted |  |
| GENERAL | — | — | reference | — | non-spatial reference | — | — | extracted |  |
| MAIZE_STUDY | — | — | reference | — | non-spatial reference | — | — | extracted |  |
| NASA SMAP Enhanced L3 Radiometer (SPL3SMP_E) | Version 6 · 9 km | — | — | 9 km | gridded context | m³/m³; soil moisture is surface context, not root-zone water | Quality-screened; missing observations are not filled. | missing | https://nsidc.org/data/spl3smp_e/versions/6 |
| MODIS MOD13Q1.061 Terra Vegetation Indices | Version 061 · 250 m · 16-day composites | — | — | 250 m | gridded context | unitless NDVI/EVI; 0.0001 scale factor applied | Quality-screened; missing observations are not filled. | missing | https://doi.org/10.5067/MODIS/MOD13Q1.061 |

## Data quality

- The selected climate record is shorter than the recommended period. Use more complete years if available.
- A crop reference value needed for some indicators is missing. Add a cited value to unlock those indicators.
- One or more crop reference values are placeholders. Replace them with locally checked, cited values.
- ET0 estimated from temperatures (Hargreaves–Samani), not measured.
- A triggered rotation rule is shown as a note only because its effect is not supported by a cited source.
- Crop growth windows overlap. Confirm sowing and harvest timing for these varieties locally.
- Soil values are regional grid context, not a field measurement. Add a field soil test.
- Growth stages assumed by a default split (no source row): timing estimates are rough.

## Climate summary

| Season | Mean T °C | Min T °C | Max T °C | Rain mm | Complete windows |
|---|---:|---:|---:|---:|---:|
| Winter | 17.5 | 5.5 | 41.6 | 91.8 | 5 |
| Summer | 27.9 | 13.5 | 45.0 | 2.2 | 6 |

## Optional satellite context

These products are regional pixel context and are not used in strategy scores.

### NASA SMAP Enhanced L3 Radiometer (SPL3SMP_E)

- Status: not_provided
- Period: —
- Spatial resolution: — km
- Valid observations: 0; excluded: 0
- Quality flags: []
- Limit: Optional context file not supplied; core analysis is unchanged.

| Month | Median soil moisture (m³/m³) | Observations |
|---|---:|---:|

### MODIS MOD13Q1.061 Terra Vegetation Indices

- Status: not_provided
- Period: —
- Spatial resolution: — m
- Valid observations: 0; excluded: 0
- Quality flags: []
- Limit: Optional context file not supplied; core analysis is unchanged.

| Month | Median NDVI | Median EVI | Observations |
|---|---:|---:|---:|

## Crop reference rows used

| Crop | Field | Value | Unit | Status | Source |
|---|---|---|---|---|---|
| Wheat | family | Poaceae | — | general_fact | GENERAL |
| Wheat | n_fixer | False | — | general_fact | GENERAL |
| Wheat | sowing_window | {'start': '11-15', 'end': '11-30'} | MM-DD | extracted | FAO_CROP_CAL |
| Wheat | growth_duration_days | 160 | days | extracted | FAO56_T11 |
| Wheat | stage_days | {'ini': 20, 'dev': 50, 'mid': 60, 'late': 30} | days | extracted | FAO56_T11 |
| Wheat | kc | {'ini': 0.3, 'mid': 1.15, 'end': 0.25} | - | extracted | FAO56_T12 |
| Wheat | water_requirement_mm_ref | {'min': 450, 'max': 650} | mm/season | extracted | FAO_WATER_T5 |
| Wheat | temperature_c | {'topmn': 15.0, 'topmx': 23.0, 'tmin': 5.0, 'tmax': 27.0, 'ktmp': 0.0} | °C | extracted | ECOCROP_MIRROR |
| Wheat | drought_sensitivity | medium | low\|medium\|high | extracted | FAO_WATER_T14 |
| Wheat | salinity_threshold_ece_dsm | 6.0 | dS/m | extracted | FAO29_T4 |
| Wheat | soil_ph_range | {'ph_min': 5.5, 'ph_max': 8.5, 'ph_opt_min': 6.0, 'ph_opt_max': 7.0} | pH | extracted | ECOCROP_MIRROR |
| Maize | family | Poaceae | — | general_fact | GENERAL |
| Maize | n_fixer | False | — | general_fact | GENERAL |
| Maize | sowing_window | {'start': '05-01', 'end': '07-01'} | MM-DD | extracted | MAIZE_STUDY |
| Maize | growth_duration_days | 150 | days | extracted | FAO56_T11 |
| Maize | stage_days | {'ini': 30, 'dev': 40, 'mid': 50, 'late': 30} | days | extracted | FAO56_T11 |
| Maize | kc | {'ini': 0.3, 'mid': 1.2, 'end': 0.6} | - | extracted | FAO56_T12 |
| Maize | water_requirement_mm_ref | {'min': 500, 'max': 800} | mm/season | extracted | FAO_WATER_T5 |
| Maize | temperature_c | {'topmn': 18.0, 'topmx': 33.0, 'tmin': 10.0, 'tmax': 47.0, 'ktmp': None} | °C | extracted | ECOCROP_MIRROR |
| Maize | drought_sensitivity | high | low\|medium\|high | extracted | FAO_WATER_T14 |
| Maize | salinity_threshold_ece_dsm | 1.7 | dS/m | extracted | FAO29_T4 |
| Maize | soil_ph_range | {'ph_min': 4.5, 'ph_max': 8.5, 'ph_opt_min': 5.0, 'ph_opt_max': 7.0} | pH | extracted | ECOCROP_MIRROR |
| Cotton | family | Malvaceae | — | general_fact | GENERAL |
| Cotton | n_fixer | False | — | general_fact | GENERAL |
| Cotton | sowing_window | {'start': '03-01', 'end': '05-31'} | MM-DD | extracted | FAO56_T11 |
| Cotton | growth_duration_days | 195 | days | extracted | FAO56_T11 |
| Cotton | stage_days | {'ini': 30, 'dev': 50, 'mid': 60, 'late': 55} | days | extracted | FAO56_T11 |
| Cotton | kc | {'ini': 0.35, 'mid': 1.15, 'end': 0.7} | - | extracted | FAO56_T12 |
| Cotton | water_requirement_mm_ref | {'min': 700, 'max': 1300} | mm/season | extracted | FAO_WATER_T5 |
| Cotton | temperature_c | {'topmn': 22.0, 'topmx': 32.0, 'tmin': 15.0, 'tmax': 38.0, 'ktmp': None} | °C | extracted | ECOCROP_MIRROR |
| Cotton | drought_sensitivity | low | low\|medium\|high | extracted | FAO_WATER_T14 |
| Cotton | salinity_threshold_ece_dsm | 7.7 | dS/m | extracted | FAO29_T4 |
| Cotton | soil_ph_range | {'ph_min': 5.0, 'ph_max': 8.5, 'ph_opt_min': 5.2, 'ph_opt_max': 7.2} | pH | extracted | ECOCROP_MIRROR |
| Sugar beet | family | Amaranthaceae | — | general_fact | GENERAL |
| Sugar beet | n_fixer | False | — | general_fact | GENERAL |
| Sugar beet | sowing_window | {'start': '10-01', 'end': '10-20'} | MM-DD | extracted | FAO_CROP_CAL |
| Sugar beet | growth_duration_days | 205 | days | extracted | FAO56_T11 |
| Sugar beet | stage_days | {'ini': 35, 'dev': 60, 'mid': 70, 'late': 40} | days | extracted | FAO56_T11 |
| Sugar beet | kc | {'ini': 0.35, 'mid': 1.2, 'end': 0.7} | - | extracted | FAO56_T12 |
| Sugar beet | water_requirement_mm_ref | {'min': 550, 'max': 750} | mm/season | extracted | FAO_WATER_T5 |
| Sugar beet | temperature_c | {'topmn': 15.0, 'topmx': 25.0, 'tmin': 4.0, 'tmax': 35.0, 'ktmp': 0.0} | °C | extracted | ECOCROP_MIRROR |
| Sugar beet | drought_sensitivity | medium | low\|medium\|high | extracted | FAO_WATER_T14 |
| Sugar beet | salinity_threshold_ece_dsm | 7.0 | dS/m | extracted | FAO29_T4 |
| Sugar beet | soil_ph_range | {'ph_min': 5.5, 'ph_max': 7.5, 'ph_opt_min': 6.0, 'ph_opt_max': 7.0} | pH | extracted | ECOCROP_MIRROR |
| Berseem clover | family | Fabaceae | — | general_fact | GENERAL |
| Berseem clover | n_fixer | True | — | general_fact | GENERAL |
| Berseem clover | sowing_window | {'start': '09-15', 'end': '11-30'} | MM-DD | extracted | FAO_I3500E |
| Berseem clover | growth_duration_days | 200 | days | placeholder | FAO_I3500E |
| Berseem clover | stage_days | — | days | missing | FAO_I3500E |
| Berseem clover | kc | {'ini': 0.4, 'mid': 0.9, 'end': 0.85} | - | extracted | FAO56_T12 |
| Berseem clover | water_requirement_mm_ref | — | mm/season | missing | FAO_WATER_T5 |
| Berseem clover | temperature_c | {'topmn': 16.0, 'topmx': 27.0, 'tmin': 3.0, 'tmax': 35.0, 'ktmp': -2.0} | °C | extracted | ECOCROP_MIRROR |
| Berseem clover | drought_sensitivity | — | low\|medium\|high | missing | FAO_WATER_T14 |
| Berseem clover | salinity_threshold_ece_dsm | — | dS/m | missing | FAO29_T4 |
| Berseem clover | soil_ph_range | {'ph_min': 4.9, 'ph_max': 7.5, 'ph_opt_min': 6.5, 'ph_opt_max': 7.0} | pH | extracted | ECOCROP_MIRROR |
| Sorghum | family | Poaceae | — | general_fact | GENERAL |
| Sorghum | n_fixer | False | — | general_fact | GENERAL |
| Sorghum | sowing_window | {'start': '05-10', 'end': '06-01'} | MM-DD | extracted | FAO_CROP_CAL |
| Sorghum | growth_duration_days | 130 | days | extracted | FAO56_T11 |
| Sorghum | stage_days | {'ini': 20, 'dev': 35, 'mid': 45, 'late': 30} | days | extracted | FAO56_T11 |
| Sorghum | kc | {'ini': 0.3, 'mid': 1.0, 'end': 0.55} | - | extracted | FAO56_T12 |
| Sorghum | water_requirement_mm_ref | {'min': 450, 'max': 650} | mm/season | extracted | FAO_WATER_T5 |
| Sorghum | temperature_c | {'topmn': 22.0, 'topmx': 35.0, 'tmin': 8.0, 'tmax': 40.0, 'ktmp': None} | °C | extracted | ECOCROP_MIRROR |
| Sorghum | drought_sensitivity | low | low\|medium\|high | extracted | FAO_WATER_T14 |
| Sorghum | salinity_threshold_ece_dsm | 6.8 | dS/m | extracted | FAO29_T4 |
| Sorghum | soil_ph_range | {'ph_min': 5.0, 'ph_max': 8.0, 'ph_opt_min': 5.5, 'ph_opt_max': 7.5} | pH | extracted | ECOCROP_MIRROR |

## Strategy comparison

| Strategy | Overall | Water demand | Confidence |
|---|---|---|---|
| Existing rotation | Moderate | Good | low |
| Candidate 1 (Sugar beet / Cotton / Berseem clover / Sorghum / Sugar beet / Cotton) | Good | Poor | low |
| Candidate 2 (Sugar beet / Cotton / Berseem clover / Maize / Sugar beet / Cotton) | Good | Poor | low |
| Candidate 3 (Berseem clover / Cotton / Sugar beet / Sorghum / Berseem clover / Cotton) | Good | Poor | low |

### Priority sensitivity

- Ranking order preserved in 100.0% of 100 priority weight perturbations (±20%); top-ranked candidate unchanged in 100.0%.

## Existing rotation

### Sequence

Y1 winter: wheat; Y1 summer: wheat; Y2 winter: wheat; Y2 summer: wheat; Y3 winter: wheat; Y3 summer: wheat

### Why it was listed

- Your current practice, as entered, is included as the comparison baseline.
- heat_days was Moderate using NASA POWER data for 2020-2025 [heat_days].
- cold_days was Good using NASA POWER data for 2020-2025 [cold_days].
- frost_days was Good using NASA POWER data for 2020-2025 [frost_days].

### Evidence

| Indicator | Value | Unit | Dataset | Period | Windows | Status |
|---|---|---|---|---|---:|---|
| heat_days | 5.0 | days/window | NASA POWER | 2020-2025 | 5 | observed |
| cold_days | 0.0 | days/window | NASA POWER | 2020-2025 | 5 | observed |
| frost_days | 0.0 | days/window | NASA POWER | 2020-2025 | 5 | observed |
| temp_in_range_pct | 68.8 | % of days | NASA POWER | 2020-2025 | 5 | observed |
| days_above_tmax | 39.0 | days/window | NASA POWER | 2020-2025 | 5 | observed |
| days_below_tmin | 0.0 | days/window | NASA POWER | 2020-2025 | 5 | observed |
| irrigation_dependence | Poor | band | NASA POWER | 2020-2025 | 5 | observed |
| water_vs_access | Good | band | NASA POWER | 2020-2025 | 5 | observed |
| ph_fit | Good | band | FAO crop reference + soil record | 2020-2025 | 5 | observed |
| salinity_fit | Moderate | band | FAO crop reference + soil record | 2020-2025 | 5 | observed |
| drought_sensitivity | Moderate | class | FAO crop reference + soil record | 2020-2025 | 5 | observed |
| etc_year_mm | 884.2 | band | NASA POWER + FAO-56 | 2020-2025 | 5 | estimated |
| water_demand_rel | — | relative | NASA POWER + FAO-56 | 2020-2025 | 5 | estimated |

### Possible benefits

- None listed.

### Information gaps

- The selected climate record is shorter than the recommended period. Use more complete years if available.
- ET0 estimated from temperatures (Hargreaves–Samani), not measured.
- A triggered rotation rule is shown as a note only because its effect is not supported by a cited source.
- Soil values are regional grid context, not a field measurement. Add a field soil test.

### Risks needing local review

- Check local variety suitability and seed availability.
- Confirm sowing dates with local agronomy and the crop calendar.
- Review local pest and disease pressure.
- Check market prices, input costs, and household food or fodder needs.
- Confirm irrigation allocation and any current crop-area rules.
- Review equipment, labor, and harvest timing.

### Indicators

| Indicator | Value / range | Unit | Band | Dataset | Windows |
|---|---:|---|---|---|---:|
| Heat exposure | 5.0 | days/window | Moderate | NASA POWER | 5 |
| Cold exposure | 0.0 | days/window | Good | NASA POWER | 5 |
| Frost exposure | 0.0 | days/window | Good | NASA POWER | 5 |
| Temperature suitability | 68.8 | % of days | Moderate | NASA POWER | 5 |
| Days above crop maximum | 39.0 | days/window | Poor | NASA POWER | 5 |
| Days below crop minimum | 0.0 | days/window | Good | NASA POWER | 5 |
| Rainfall | — | mm/window | Unknown | NASA POWER | 5 |
| Estimated crop water need (ETc) | 442.1 | mm/season | Unknown | NASA POWER + FAO-56 | 5 |
| Rain coverage of ETc | — | % | Unknown | NASA POWER + FAO-56 | 5 |
| Irrigation dependence | — | band | Poor | NASA POWER | 5 |
| Water demand vs reported access | — | band | Good | NASA POWER | 5 |
| Soil pH fit | — | band | Good | FAO crop reference + soil record | 5 |
| Salinity fit | — | band | Moderate | FAO crop reference + soil record | 5 |
| Crop drought sensitivity | — | class | Moderate | FAO crop reference + soil record | 5 |
| etc year mm | 884.2 | band | Moderate | NASA POWER + FAO-56 | 5 |
| Relative annual ETc | 0.5 | relative | Good | NASA POWER + FAO-56 | 5 |

- Dataset: NASA POWER + FAO crop reference; period: 2020-01-01/2025-12-31.

### Sowing-date sensitivity

| Crop | Sowing window | Indicator | Unit | Sowing start | Midpoint | Sowing end | Spread | Windows (start/mid/end) |
|---|---|---|---|---:|---:|---:|---:|---|
| wheat | 11-15 .. 11-30 | etc window mm | mm/season | 416.6 | 442.1 | 474.8 | 58.2 | 5/5/5 |
| wheat | 11-15 .. 11-30 | heat days | days/window | 4 | 5 | 5 | 1 | 5/5/5 |
| wheat | 11-15 .. 11-30 | cold days | days/window | 0 | 0 | 0 | 0 | 5/5/5 |
| wheat | 11-15 .. 11-30 | frost days | days/window | 0 | 0 | 0 | 0 | 5/5/5 |
| wheat | 11-15 .. 11-30 | temp in range pct | % of days | 70.0 | 68.8 | 67.5 | 2.5 | 5/5/5 |
| wheat | 11-15 .. 11-30 | rain window mm | mm/window | 90.1 | 89.1 | 89.4 | 1.0 | 5/5/5 |

## Candidate 1 (Sugar beet / Cotton / Berseem clover / Sorghum / Sugar beet / Cotton)

### Sequence

Y1 winter: sugar_beet; Y1 summer: cotton; Y2 winter: berseem; Y2 summer: sorghum; Y3 winter: sugar_beet; Y3 summer: cotton

### Why it was listed

- Proposed by the engine as a candidate to explore based on your ranked priorities and rotation rules.
- heat_days was Poor using NASA POWER data for 2020-2025 [heat_days].
- cold_days was Good using NASA POWER data for 2020-2025 [cold_days].
- frost_days was Good using NASA POWER data for 2020-2025 [frost_days].

### Evidence

| Indicator | Value | Unit | Dataset | Period | Windows | Status |
|---|---|---|---|---|---:|---|
| heat_days | 9.0–133.0 | days/window | NASA POWER | 2020-2025 | 22 | observed |
| cold_days | 0.0 | days/window | NASA POWER | 2020-2025 | 22 | observed |
| frost_days | 0.0 | days/window | NASA POWER | 2020-2025 | 22 | observed |
| temp_in_range_pct | 61.5–100.0 | % of days | NASA POWER | 2020-2025 | 22 | observed |
| days_above_tmax | 9.0–83.5 | days/window | NASA POWER | 2020-2025 | 22 | observed |
| days_below_tmin | 0.0–15.0 | days/window | NASA POWER | 2020-2025 | 22 | observed |
| irrigation_dependence | Poor | band | NASA POWER | 2020-2025 | 22 | observed |
| water_vs_access | Good | band | NASA POWER | 2020-2025 | 22 | observed |
| ph_fit | Good | band | FAO crop reference + soil record | 2020-2025 | 22 | observed |
| etc_year_mm | 1702.6 | band | NASA POWER + FAO-56 | 2020-2025 | 22 | estimated |
| water_demand_rel | — | relative | NASA POWER + FAO-56 | 2020-2025 | 22 | estimated |

### Possible benefits

- This strategy may have a more favorable temp_in_range_pct band (Good) in NASA POWER for 2020-2025 [temp_in_range_pct].

### Information gaps

- The selected climate record is shorter than the recommended period. Use more complete years if available.
- A crop reference value needed for some indicators is missing. Add a cited value to unlock those indicators.
- One or more crop reference values are placeholders. Replace them with locally checked, cited values.
- ET0 estimated from temperatures (Hargreaves–Samani), not measured.
- A triggered rotation rule is shown as a note only because its effect is not supported by a cited source.
- Crop growth windows overlap. Confirm sowing and harvest timing for these varieties locally.
- Soil values are regional grid context, not a field measurement. Add a field soil test.
- Growth stages assumed by a default split (no source row): timing estimates are rough.

### Risks needing local review

- Check local variety suitability and seed availability.
- Confirm sowing dates with local agronomy and the crop calendar.
- Review local pest and disease pressure.
- Check market prices, input costs, and household food or fodder needs.
- Confirm irrigation allocation and any current crop-area rules.
- Review equipment, labor, and harvest timing.
- Check whether overlapping crop windows are workable with local varieties and equipment.

### Indicators

| Indicator | Value / range | Unit | Band | Dataset | Windows |
|---|---:|---|---|---|---:|
| Heat exposure | 9.0–133.0 | days/window | Poor | NASA POWER | 22 |
| Cold exposure | 0.0 | days/window | Good | NASA POWER | 22 |
| Frost exposure | 0.0 | days/window | Good | NASA POWER | 22 |
| Temperature suitability | 61.5–100.0 | % of days | Good | NASA POWER | 22 |
| Days above crop maximum | 9.0–83.5 | days/window | Poor | NASA POWER | 22 |
| Days below crop minimum | 0.0–15.0 | days/window | Good | NASA POWER | 22 |
| Rainfall | — | mm/window | Unknown | NASA POWER | 22 |
| Estimated crop water need (ETc) | 536.7–1108.0 | mm/season | Unknown | NASA POWER + FAO-56 | 22 |
| Rain coverage of ETc | — | % | Unknown | NASA POWER + FAO-56 | 22 |
| Irrigation dependence | — | band | Poor | NASA POWER | 22 |
| Water demand vs reported access | — | band | Good | NASA POWER | 22 |
| Soil pH fit | — | band | Good | FAO crop reference + soil record | 22 |
| Salinity fit | — | band | Unknown | FAO crop reference + soil record | 22 |
| Crop drought sensitivity | — | class | Unknown | FAO crop reference + soil record | 22 |
| etc year mm | 1702.6 | band | Moderate | NASA POWER + FAO-56 | 22 |
| Relative annual ETc | 1.0 | relative | Poor | NASA POWER + FAO-56 | 22 |

- Dataset: NASA POWER + FAO crop reference; period: 2020-01-01/2025-12-31.

### Sowing-date sensitivity

| Crop | Sowing window | Indicator | Unit | Sowing start | Midpoint | Sowing end | Spread | Windows (start/mid/end) |
|---|---|---|---|---:|---:|---:|---:|---|
| sugar_beet | 10-01 .. 10-20 | etc window mm | mm/season | 566.9 | 594.6 | 637.6 | 70.7 | 5/5/5 |
| sugar_beet | 10-01 .. 10-20 | heat days | days/window | 8 | 9 | 11 | 3 | 5/5/5 |
| sugar_beet | 10-01 .. 10-20 | cold days | days/window | 0 | 0 | 0 | 0 | 5/5/5 |
| sugar_beet | 10-01 .. 10-20 | frost days | days/window | 0 | 0 | 0 | 0 | 5/5/5 |
| sugar_beet | 10-01 .. 10-20 | temp in range pct | % of days | 66.3 | 69.8 | 71.2 | 4.9 | 5/5/5 |
| sugar_beet | 10-01 .. 10-20 | rain window mm | mm/window | 99.5 | 99.5 | 99.3 | 0.2 | 5/5/5 |
| cotton | 03-01 .. 05-31 | etc window mm | mm/season | 1151.2 | 1108.0 | 886.8 | 264.4 | 6/6/6 |
| cotton | 03-01 .. 05-31 | heat days | days/window | 115.5 | 133.0 | 119.0 | 17.5 | 6/6/6 |
| cotton | 03-01 .. 05-31 | cold days | days/window | 0.0 | 0.0 | 0.0 | 0.0 | 6/6/6 |
| cotton | 03-01 .. 05-31 | frost days | days/window | 0.0 | 0.0 | 0.0 | 0.0 | 6/6/6 |
| cotton | 03-01 .. 05-31 | temp in range pct | % of days | 68.5 | 87.0 | 79.5 | 18.5 | 6/6/6 |
| cotton | 03-01 .. 05-31 | rain window mm | mm/window | 32.5 | 5.2 | 20.1 | 27.2 | 6/6/6 |
| sorghum | 05-10 .. 06-01 | etc window mm | mm/season | 702.9 | 682.1 | 656.9 | 46.0 | 6/6/6 |
| sorghum | 05-10 .. 06-01 | heat days | days/window | 112.0 | 114.0 | 117.0 | 5.0 | 6/6/6 |
| sorghum | 05-10 .. 06-01 | cold days | days/window | 0.0 | 0.0 | 0.0 | 0.0 | 6/6/6 |
| sorghum | 05-10 .. 06-01 | frost days | days/window | 0.0 | 0.0 | 0.0 | 0.0 | 6/6/6 |
| sorghum | 05-10 .. 06-01 | temp in range pct | % of days | 99.6 | 100.0 | 100.0 | 0.4 | 6/6/6 |
| sorghum | 05-10 .. 06-01 | rain window mm | mm/window | 0.4 | 0.4 | 0.4 | 0.0 | 6/6/6 |

## Candidate 2 (Sugar beet / Cotton / Berseem clover / Maize / Sugar beet / Cotton)

### Sequence

Y1 winter: sugar_beet; Y1 summer: cotton; Y2 winter: berseem; Y2 summer: maize; Y3 winter: sugar_beet; Y3 summer: cotton

### Why it was listed

- Proposed by the engine as a candidate to explore based on your ranked priorities and rotation rules.
- heat_days was Poor using NASA POWER data for 2020-2025 [heat_days].
- cold_days was Good using NASA POWER data for 2020-2025 [cold_days].
- frost_days was Good using NASA POWER data for 2020-2025 [frost_days].

### Evidence

| Indicator | Value | Unit | Dataset | Period | Windows | Status |
|---|---|---|---|---|---:|---|
| heat_days | 9.0–133.0 | days/window | NASA POWER | 2020-2025 | 22 | observed |
| cold_days | 0.0 | days/window | NASA POWER | 2020-2025 | 22 | observed |
| frost_days | 0.0 | days/window | NASA POWER | 2020-2025 | 22 | observed |
| temp_in_range_pct | 61.5–96.7 | % of days | NASA POWER | 2020-2025 | 22 | observed |
| days_above_tmax | 0.0–83.5 | days/window | NASA POWER | 2020-2025 | 22 | observed |
| days_below_tmin | 0.0–15.0 | days/window | NASA POWER | 2020-2025 | 22 | observed |
| irrigation_dependence | Poor | band | NASA POWER | 2020-2025 | 22 | observed |
| water_vs_access | Good | band | NASA POWER | 2020-2025 | 22 | observed |
| ph_fit | Good | band | FAO crop reference + soil record | 2020-2025 | 22 | observed |
| etc_year_mm | 1702.6 | band | NASA POWER + FAO-56 | 2020-2025 | 22 | estimated |
| water_demand_rel | — | relative | NASA POWER + FAO-56 | 2020-2025 | 22 | estimated |

### Possible benefits

- This strategy may have a more favorable temp_in_range_pct band (Good) in NASA POWER for 2020-2025 [temp_in_range_pct].
- This strategy may have a more favorable days_above_tmax band (Moderate) in NASA POWER for 2020-2025 [days_above_tmax].

### Information gaps

- The selected climate record is shorter than the recommended period. Use more complete years if available.
- A crop reference value needed for some indicators is missing. Add a cited value to unlock those indicators.
- One or more crop reference values are placeholders. Replace them with locally checked, cited values.
- ET0 estimated from temperatures (Hargreaves–Samani), not measured.
- A triggered rotation rule is shown as a note only because its effect is not supported by a cited source.
- Crop growth windows overlap. Confirm sowing and harvest timing for these varieties locally.
- Soil values are regional grid context, not a field measurement. Add a field soil test.
- Growth stages assumed by a default split (no source row): timing estimates are rough.

### Risks needing local review

- Check local variety suitability and seed availability.
- Confirm sowing dates with local agronomy and the crop calendar.
- Review local pest and disease pressure.
- Check market prices, input costs, and household food or fodder needs.
- Confirm irrigation allocation and any current crop-area rules.
- Review equipment, labor, and harvest timing.
- Check whether overlapping crop windows are workable with local varieties and equipment.

### Indicators

| Indicator | Value / range | Unit | Band | Dataset | Windows |
|---|---:|---|---|---|---:|
| Heat exposure | 9.0–133.0 | days/window | Poor | NASA POWER | 22 |
| Cold exposure | 0.0 | days/window | Good | NASA POWER | 22 |
| Frost exposure | 0.0 | days/window | Good | NASA POWER | 22 |
| Temperature suitability | 61.5–96.7 | % of days | Good | NASA POWER | 22 |
| Days above crop maximum | 0.0–83.5 | days/window | Moderate | NASA POWER | 22 |
| Days below crop minimum | 0.0–15.0 | days/window | Good | NASA POWER | 22 |
| Rainfall | — | mm/window | Unknown | NASA POWER | 22 |
| Estimated crop water need (ETc) | 536.7–1108.0 | mm/season | Unknown | NASA POWER + FAO-56 | 22 |
| Rain coverage of ETc | — | % | Unknown | NASA POWER + FAO-56 | 22 |
| Irrigation dependence | — | band | Poor | NASA POWER | 22 |
| Water demand vs reported access | — | band | Good | NASA POWER | 22 |
| Soil pH fit | — | band | Good | FAO crop reference + soil record | 22 |
| Salinity fit | — | band | Unknown | FAO crop reference + soil record | 22 |
| Crop drought sensitivity | — | class | Unknown | FAO crop reference + soil record | 22 |
| etc year mm | 1702.6 | band | Moderate | NASA POWER + FAO-56 | 22 |
| Relative annual ETc | 1.0 | relative | Poor | NASA POWER + FAO-56 | 22 |

- Dataset: NASA POWER + FAO crop reference; period: 2020-01-01/2025-12-31.

### Sowing-date sensitivity

| Crop | Sowing window | Indicator | Unit | Sowing start | Midpoint | Sowing end | Spread | Windows (start/mid/end) |
|---|---|---|---|---:|---:|---:|---:|---|
| sugar_beet | 10-01 .. 10-20 | etc window mm | mm/season | 566.9 | 594.6 | 637.6 | 70.7 | 5/5/5 |
| sugar_beet | 10-01 .. 10-20 | heat days | days/window | 8 | 9 | 11 | 3 | 5/5/5 |
| sugar_beet | 10-01 .. 10-20 | cold days | days/window | 0 | 0 | 0 | 0 | 5/5/5 |
| sugar_beet | 10-01 .. 10-20 | frost days | days/window | 0 | 0 | 0 | 0 | 5/5/5 |
| sugar_beet | 10-01 .. 10-20 | temp in range pct | % of days | 66.3 | 69.8 | 71.2 | 4.9 | 5/5/5 |
| sugar_beet | 10-01 .. 10-20 | rain window mm | mm/window | 99.5 | 99.5 | 99.3 | 0.2 | 5/5/5 |
| cotton | 03-01 .. 05-31 | etc window mm | mm/season | 1151.2 | 1108.0 | 886.8 | 264.4 | 6/6/6 |
| cotton | 03-01 .. 05-31 | heat days | days/window | 115.5 | 133.0 | 119.0 | 17.5 | 6/6/6 |
| cotton | 03-01 .. 05-31 | cold days | days/window | 0.0 | 0.0 | 0.0 | 0.0 | 6/6/6 |
| cotton | 03-01 .. 05-31 | frost days | days/window | 0.0 | 0.0 | 0.0 | 0.0 | 6/6/6 |
| cotton | 03-01 .. 05-31 | temp in range pct | % of days | 68.5 | 87.0 | 79.5 | 18.5 | 6/6/6 |
| cotton | 03-01 .. 05-31 | rain window mm | mm/window | 32.5 | 5.2 | 20.1 | 27.2 | 6/6/6 |
| maize | 05-01 .. 07-01 | etc window mm | mm/season | 890.4 | 786.1 | 626.9 | 263.5 | 6/6/6 |
| maize | 05-01 .. 07-01 | heat days | days/window | 125.0 | 119.0 | 91.0 | 34.0 | 6/6/6 |
| maize | 05-01 .. 07-01 | cold days | days/window | 0.0 | 0.0 | 0.0 | 0.0 | 6/6/6 |
| maize | 05-01 .. 07-01 | frost days | days/window | 0.0 | 0.0 | 0.0 | 0.0 | 6/6/6 |
| maize | 05-01 .. 07-01 | temp in range pct | % of days | 96.7 | 96.7 | 96.0 | 0.7 | 6/6/6 |
| maize | 05-01 .. 07-01 | rain window mm | mm/window | 0.4 | 1.5 | 15.4 | 15.0 | 6/6/6 |

## Candidate 3 (Berseem clover / Cotton / Sugar beet / Sorghum / Berseem clover / Cotton)

### Sequence

Y1 winter: berseem; Y1 summer: cotton; Y2 winter: sugar_beet; Y2 summer: sorghum; Y3 winter: berseem; Y3 summer: cotton

### Why it was listed

- Proposed by the engine as a candidate to explore based on your ranked priorities and rotation rules.
- heat_days was Poor using NASA POWER data for 2020-2025 [heat_days].
- cold_days was Good using NASA POWER data for 2020-2025 [cold_days].
- frost_days was Good using NASA POWER data for 2020-2025 [frost_days].

### Evidence

| Indicator | Value | Unit | Dataset | Period | Windows | Status |
|---|---|---|---|---|---:|---|
| heat_days | 9.0–133.0 | days/window | NASA POWER | 2020-2025 | 22 | observed |
| cold_days | 0.0 | days/window | NASA POWER | 2020-2025 | 22 | observed |
| frost_days | 0.0 | days/window | NASA POWER | 2020-2025 | 22 | observed |
| temp_in_range_pct | 61.5–100.0 | % of days | NASA POWER | 2020-2025 | 22 | observed |
| days_above_tmax | 9.0–83.5 | days/window | NASA POWER | 2020-2025 | 22 | observed |
| days_below_tmin | 0.0–15.0 | days/window | NASA POWER | 2020-2025 | 22 | observed |
| irrigation_dependence | Poor | band | NASA POWER | 2020-2025 | 22 | observed |
| water_vs_access | Good | band | NASA POWER | 2020-2025 | 22 | observed |
| ph_fit | Good | band | FAO crop reference + soil record | 2020-2025 | 22 | observed |
| etc_year_mm | 1644.8 | band | NASA POWER + FAO-56 | 2020-2025 | 22 | estimated |
| water_demand_rel | — | relative | NASA POWER + FAO-56 | 2020-2025 | 22 | estimated |

### Possible benefits

- This strategy may have a more favorable temp_in_range_pct band (Good) in NASA POWER for 2020-2025 [temp_in_range_pct].

### Information gaps

- The selected climate record is shorter than the recommended period. Use more complete years if available.
- A crop reference value needed for some indicators is missing. Add a cited value to unlock those indicators.
- One or more crop reference values are placeholders. Replace them with locally checked, cited values.
- ET0 estimated from temperatures (Hargreaves–Samani), not measured.
- A triggered rotation rule is shown as a note only because its effect is not supported by a cited source.
- Crop growth windows overlap. Confirm sowing and harvest timing for these varieties locally.
- Soil values are regional grid context, not a field measurement. Add a field soil test.
- Growth stages assumed by a default split (no source row): timing estimates are rough.

### Risks needing local review

- Check local variety suitability and seed availability.
- Confirm sowing dates with local agronomy and the crop calendar.
- Review local pest and disease pressure.
- Check market prices, input costs, and household food or fodder needs.
- Confirm irrigation allocation and any current crop-area rules.
- Review equipment, labor, and harvest timing.
- Check whether overlapping crop windows are workable with local varieties and equipment.

### Indicators

| Indicator | Value / range | Unit | Band | Dataset | Windows |
|---|---:|---|---|---|---:|
| Heat exposure | 9.0–133.0 | days/window | Poor | NASA POWER | 22 |
| Cold exposure | 0.0 | days/window | Good | NASA POWER | 22 |
| Frost exposure | 0.0 | days/window | Good | NASA POWER | 22 |
| Temperature suitability | 61.5–100.0 | % of days | Good | NASA POWER | 22 |
| Days above crop maximum | 9.0–83.5 | days/window | Poor | NASA POWER | 22 |
| Days below crop minimum | 0.0–15.0 | days/window | Good | NASA POWER | 22 |
| Rainfall | — | mm/window | Unknown | NASA POWER | 22 |
| Estimated crop water need (ETc) | 536.7–1108.0 | mm/season | Unknown | NASA POWER + FAO-56 | 22 |
| Rain coverage of ETc | — | % | Unknown | NASA POWER + FAO-56 | 22 |
| Irrigation dependence | — | band | Poor | NASA POWER | 22 |
| Water demand vs reported access | — | band | Good | NASA POWER | 22 |
| Soil pH fit | — | band | Good | FAO crop reference + soil record | 22 |
| Salinity fit | — | band | Unknown | FAO crop reference + soil record | 22 |
| Crop drought sensitivity | — | class | Unknown | FAO crop reference + soil record | 22 |
| etc year mm | 1644.8 | band | Moderate | NASA POWER + FAO-56 | 22 |
| Relative annual ETc | 1.0 | relative | Poor | NASA POWER + FAO-56 | 22 |

- Dataset: NASA POWER + FAO crop reference; period: 2020-01-01/2025-12-31.

### Sowing-date sensitivity

| Crop | Sowing window | Indicator | Unit | Sowing start | Midpoint | Sowing end | Spread | Windows (start/mid/end) |
|---|---|---|---|---:|---:|---:|---:|---|
| cotton | 03-01 .. 05-31 | etc window mm | mm/season | 1151.2 | 1108.0 | 886.8 | 264.4 | 6/6/6 |
| cotton | 03-01 .. 05-31 | heat days | days/window | 115.5 | 133.0 | 119.0 | 17.5 | 6/6/6 |
| cotton | 03-01 .. 05-31 | cold days | days/window | 0.0 | 0.0 | 0.0 | 0.0 | 6/6/6 |
| cotton | 03-01 .. 05-31 | frost days | days/window | 0.0 | 0.0 | 0.0 | 0.0 | 6/6/6 |
| cotton | 03-01 .. 05-31 | temp in range pct | % of days | 68.5 | 87.0 | 79.5 | 18.5 | 6/6/6 |
| cotton | 03-01 .. 05-31 | rain window mm | mm/window | 32.5 | 5.2 | 20.1 | 27.2 | 6/6/6 |
| sugar_beet | 10-01 .. 10-20 | etc window mm | mm/season | 566.9 | 594.6 | 637.6 | 70.7 | 5/5/5 |
| sugar_beet | 10-01 .. 10-20 | heat days | days/window | 8 | 9 | 11 | 3 | 5/5/5 |
| sugar_beet | 10-01 .. 10-20 | cold days | days/window | 0 | 0 | 0 | 0 | 5/5/5 |
| sugar_beet | 10-01 .. 10-20 | frost days | days/window | 0 | 0 | 0 | 0 | 5/5/5 |
| sugar_beet | 10-01 .. 10-20 | temp in range pct | % of days | 66.3 | 69.8 | 71.2 | 4.9 | 5/5/5 |
| sugar_beet | 10-01 .. 10-20 | rain window mm | mm/window | 99.5 | 99.5 | 99.3 | 0.2 | 5/5/5 |
| sorghum | 05-10 .. 06-01 | etc window mm | mm/season | 702.9 | 682.1 | 656.9 | 46.0 | 6/6/6 |
| sorghum | 05-10 .. 06-01 | heat days | days/window | 112.0 | 114.0 | 117.0 | 5.0 | 6/6/6 |
| sorghum | 05-10 .. 06-01 | cold days | days/window | 0.0 | 0.0 | 0.0 | 0.0 | 6/6/6 |
| sorghum | 05-10 .. 06-01 | frost days | days/window | 0.0 | 0.0 | 0.0 | 0.0 | 6/6/6 |
| sorghum | 05-10 .. 06-01 | temp in range pct | % of days | 99.6 | 100.0 | 100.0 | 0.4 | 6/6/6 |
| sorghum | 05-10 .. 06-01 | rain window mm | mm/window | 0.4 | 0.4 | 0.4 | 0.0 | 6/6/6 |

## Limits and methodology

- Climate change can shift some risks; salinity, soil degradation, and irrigation shortage also depend on management, water quality, and infrastructure.
- Frost and heavy rain are not generalised to all of Egypt; local area and season matter.
- The Mansoura coordinates are illustrative, not a real field location.
- This comparison is not field-specific advice; verify the inputs and sources locally.
- Each indicator should be read with its source, update date, and accuracy limits.

## Check locally

- Confirm crop varieties, sowing windows, and seed availability.
- Review pests, diseases, costs, market needs, and equipment with local experts.
- Check irrigation allocation, crop-area rules, and field soil EC.

Check these locally with an agronomist or extension officer.

## Reproduction

- Engine version: 0.1.0
- Created: 2026-10-31T22:04:29
- Command: `fieldshift run --profile runs/20261031-220427/profile.json --offline`
- Raw data SHA-256: 465e89e32f276647e840ab4f4e86bf3735dbd48a4e17cec2021a1fabd6a23390
