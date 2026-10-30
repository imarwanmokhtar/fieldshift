# ruff: noqa: E501
"""data/init.py — `fieldshift init-data` (Phase 1). Creates the FieldShift_Data skeleton
and writes seed files from DATA.md only when they are absent (never clobbers
verified data produced by the data sprint).
"""
from __future__ import annotations

import json
from pathlib import Path

DIRS = [
    "raw/power", "raw/soil", "raw/crops", "raw/smap", "raw/modis",
    "cleaned", "metadata", "references",
]

SEED_CROP_REFERENCE = """schema_version: 2
generated_by: "FieldShift init-data seed (Phase 1) — replace values via the data sprint"
generated_on: "2026-10-30"
location_note: "Sowing windows below are illustrative seed values; verify against FAO calendars before publishing."
verification_extract: "FieldShift_Data/raw/crops/crop_table_verification_extract_20261030.md"
sources:
  GENERAL: "General agronomic knowledge (placeholder seed) — must be replaced by cited sources."
slots:
  winter: {months: [11, 12, 1, 2, 3, 4], label: "Winter Nov-Apr"}
  summer: {months: [5, 6, 7, 8, 9, 10], label: "Summer May-Oct"}
defaults:
  stage_split_if_missing: {ini: 0.15, dev: 0.25, mid: 0.40, late: 0.20}
drought_class_mapping:
  rule: "Compound classes collapsed to the more-sensitive bound (see DECISIONS.md)."
  printed_to_enum: {low: low, low-medium: medium, medium: medium, medium-high: high, high: high}
crops:
- crop_id: wheat
  names: {en: Wheat, ar: قمح, scientific: Triticum aestivum}
  category: cereal
  family: {v: Poaceae, src: GENERAL, status: general_fact}
  n_fixer: {v: false, src: GENERAL, status: general_fact}
  usual_slot: winter
  sowing_window: {v: {start: "11-15", end: "11-30"}, unit: "MM-DD", src: GENERAL, status: placeholder}
  growth_duration_days: {v: 160, unit: days, src: GENERAL, status: placeholder}
  stage_days: {v: null, unit: days, src: GENERAL, status: missing, note: "No stage split; engine default split applies."}
  kc: {v: {ini: 0.30, mid: 1.15, end: 0.25}, unit: "-", src: GENERAL, status: placeholder}
  water_requirement_mm_ref: {v: null, unit: "mm/season", src: GENERAL, status: missing}
  temperature_c: {v: null, unit: "°C", src: GENERAL, status: missing}
  drought_sensitivity: {v: null, unit: "low|medium|high", src: GENERAL, status: missing}
  salinity_threshold_ece_dsm: {v: null, unit: "dS/m", src: GENERAL, status: missing}
  soil_ph_range: {v: null, unit: pH, src: GENERAL, status: missing}
- crop_id: maize
  names: {en: Maize, ar: ذرة شامية, scientific: Zea mays}
  category: cereal
  family: {v: Poaceae, src: GENERAL, status: general_fact}
  n_fixer: {v: false, src: GENERAL, status: general_fact}
  usual_slot: summer
  sowing_window: {v: {start: "05-01", end: "07-01"}, unit: "MM-DD", src: GENERAL, status: placeholder}
  growth_duration_days: {v: 150, unit: days, src: GENERAL, status: placeholder}
  stage_days: {v: null, unit: days, src: GENERAL, status: missing, note: "No stage split; engine default split applies."}
  kc: {v: {ini: 0.30, mid: 1.20, end: 0.60}, unit: "-", src: GENERAL, status: placeholder}
  water_requirement_mm_ref: {v: null, unit: "mm/season", src: GENERAL, status: missing}
  temperature_c: {v: null, unit: "°C", src: GENERAL, status: missing}
  drought_sensitivity: {v: null, unit: "low|medium|high", src: GENERAL, status: missing}
  salinity_threshold_ece_dsm: {v: null, unit: "dS/m", src: GENERAL, status: missing}
  soil_ph_range: {v: null, unit: pH, src: GENERAL, status: missing}
- crop_id: rice
  names: {en: Rice, ar: أرز, scientific: Oryza sativa}
  category: cereal
  family: {v: Poaceae, src: GENERAL, status: general_fact}
  n_fixer: {v: false, src: GENERAL, status: general_fact}
  usual_slot: summer
  sowing_window: {v: {start: "04-20", end: "05-10"}, unit: "MM-DD", src: GENERAL, status: placeholder}
  growth_duration_days: {v: 150, unit: days, src: GENERAL, status: placeholder}
  stage_days: {v: null, unit: days, src: GENERAL, status: missing, note: "No stage split; engine default split applies."}
  kc: {v: {ini: 1.05, mid: 1.20, end: 0.90}, unit: "-", src: GENERAL, status: placeholder}
  water_requirement_mm_ref: {v: null, unit: "mm/season", src: GENERAL, status: missing}
  temperature_c: {v: null, unit: "°C", src: GENERAL, status: missing}
  drought_sensitivity: {v: null, unit: "low|medium|high", src: GENERAL, status: missing}
  salinity_threshold_ece_dsm: {v: null, unit: "dS/m", src: GENERAL, status: missing}
  soil_ph_range: {v: null, unit: pH, src: GENERAL, status: missing}
- crop_id: cotton
  names: {en: Cotton, ar: قطن, scientific: Gossypium barbadense}
  category: fibre
  family: {v: Malvaceae, src: GENERAL, status: general_fact}
  n_fixer: {v: false, src: GENERAL, status: general_fact}
  usual_slot: summer
  sowing_window: {v: {start: "03-01", end: "05-31"}, unit: "MM-DD", src: GENERAL, status: placeholder}
  growth_duration_days: {v: 195, unit: days, src: GENERAL, status: placeholder}
  stage_days: {v: null, unit: days, src: GENERAL, status: missing, note: "No stage split; engine default split applies."}
  kc: {v: {ini: 0.35, mid: 1.15, end: 0.70}, unit: "-", src: GENERAL, status: placeholder}
  water_requirement_mm_ref: {v: null, unit: "mm/season", src: GENERAL, status: missing}
  temperature_c: {v: null, unit: "°C", src: GENERAL, status: missing}
  drought_sensitivity: {v: null, unit: "low|medium|high", src: GENERAL, status: missing}
  salinity_threshold_ece_dsm: {v: null, unit: "dS/m", src: GENERAL, status: missing}
  soil_ph_range: {v: null, unit: pH, src: GENERAL, status: missing}
- crop_id: sugar_beet
  names: {en: Sugar beet, ar: بنجر السكر, scientific: Beta vulgaris}
  category: root_sugar
  family: {v: Amaranthaceae, src: GENERAL, status: general_fact}
  n_fixer: {v: false, src: GENERAL, status: general_fact}
  usual_slot: winter
  sowing_window: {v: {start: "10-01", end: "10-20"}, unit: "MM-DD", src: GENERAL, status: placeholder}
  growth_duration_days: {v: 205, unit: days, src: GENERAL, status: placeholder}
  stage_days: {v: null, unit: days, src: GENERAL, status: missing, note: "No stage split; engine default split applies."}
  kc: {v: {ini: 0.35, mid: 1.20, end: 0.70}, unit: "-", src: GENERAL, status: placeholder}
  water_requirement_mm_ref: {v: null, unit: "mm/season", src: GENERAL, status: missing}
  temperature_c: {v: null, unit: "°C", src: GENERAL, status: missing}
  drought_sensitivity: {v: null, unit: "low|medium|high", src: GENERAL, status: missing}
  salinity_threshold_ece_dsm: {v: null, unit: "dS/m", src: GENERAL, status: missing}
  soil_ph_range: {v: null, unit: pH, src: GENERAL, status: missing}
- crop_id: faba_bean
  names: {en: Faba bean, ar: فول بلدي, scientific: Vicia faba}
  category: legume
  family: {v: Fabaceae, src: GENERAL, status: general_fact}
  n_fixer: {v: true, src: GENERAL, status: general_fact}
  usual_slot: winter
  sowing_window: {v: {start: "10-01", end: "11-15"}, unit: "MM-DD", src: GENERAL, status: placeholder}
  growth_duration_days: {v: 185, unit: days, src: GENERAL, status: placeholder}
  stage_days: {v: null, unit: days, src: GENERAL, status: missing, note: "No stage split; engine default split applies."}
  kc: {v: {ini: 0.50, mid: 1.15, end: 0.30}, unit: "-", src: GENERAL, status: placeholder}
  water_requirement_mm_ref: {v: null, unit: "mm/season", src: GENERAL, status: missing}
  temperature_c: {v: null, unit: "°C", src: GENERAL, status: missing}
  drought_sensitivity: {v: null, unit: "low|medium|high", src: GENERAL, status: missing}
  salinity_threshold_ece_dsm: {v: null, unit: "dS/m", src: GENERAL, status: missing}
  soil_ph_range: {v: null, unit: pH, src: GENERAL, status: missing}
- crop_id: berseem
  names: {en: Berseem clover, ar: برسيم, scientific: Trifolium alexandrinum}
  category: forage_legume
  family: {v: Fabaceae, src: GENERAL, status: general_fact}
  n_fixer: {v: true, src: GENERAL, status: general_fact}
  usual_slot: winter
  sowing_window: {v: {start: "09-15", end: "11-30"}, unit: "MM-DD", src: GENERAL, status: placeholder}
  growth_duration_days: {v: 200, unit: days, src: GENERAL, status: placeholder}
  stage_days: {v: null, unit: days, src: GENERAL, status: missing, note: "No stage split; engine default split applies."}
  kc: {v: {ini: 0.40, mid: 0.90, end: 0.85}, unit: "-", src: GENERAL, status: placeholder}
  water_requirement_mm_ref: {v: null, unit: "mm/season", src: GENERAL, status: missing}
  temperature_c: {v: null, unit: "°C", src: GENERAL, status: missing}
  drought_sensitivity: {v: null, unit: "low|medium|high", src: GENERAL, status: missing}
  salinity_threshold_ece_dsm: {v: null, unit: "dS/m", src: GENERAL, status: missing}
  soil_ph_range: {v: null, unit: pH, src: GENERAL, status: missing}
- crop_id: sorghum
  names: {en: Sorghum, ar: ذرة رفيعة, scientific: Sorghum bicolor}
  category: cereal
  family: {v: Poaceae, src: GENERAL, status: general_fact}
  n_fixer: {v: false, src: GENERAL, status: general_fact}
  usual_slot: summer
  sowing_window: {v: {start: "05-10", end: "06-01"}, unit: "MM-DD", src: GENERAL, status: placeholder}
  growth_duration_days: {v: 130, unit: days, src: GENERAL, status: placeholder}
  stage_days: {v: null, unit: days, src: GENERAL, status: missing, note: "No stage split; engine default split applies."}
  kc: {v: {ini: 0.30, mid: 1.00, end: 0.55}, unit: "-", src: GENERAL, status: placeholder}
  water_requirement_mm_ref: {v: null, unit: "mm/season", src: GENERAL, status: missing}
  temperature_c: {v: null, unit: "°C", src: GENERAL, status: missing}
  drought_sensitivity: {v: null, unit: "low|medium|high", src: GENERAL, status: missing}
  salinity_threshold_ece_dsm: {v: null, unit: "dS/m", src: GENERAL, status: missing}
  soil_ph_range: {v: null, unit: pH, src: GENERAL, status: missing}
- crop_id: fallow
  names: {en: Fallow / bare, ar: بور, scientific: null}
  category: fallow
  family: {v: null, src: GENERAL, status: general_fact}
  n_fixer: {v: false, src: GENERAL, status: general_fact}
  usual_slot: any
  note: "No crop. Zero crop water use by definition."
"""

SEED_ROTATION_TEMPLATES = """schema_version: 1
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
"""

SEED_ROTATION_RULES = """schema_version: 1
rules:
- id: R_FAMILY_REPEAT
  trigger: "same botanical family in consecutive seasons"
  effect_if_supported: {score: -0.10, applies_to: soil_health}
  note_key: "rule.family_repeat"
  supported: false
  evidence_needed: "extension or FAO source on pest/disease carry-over in same-family sequences"
- id: R_LEGUME_PRESENT
  trigger: "sequence includes a nitrogen-fixing crop (n_fixer = true)"
  effect_if_supported: {score: +0.10, applies_to: soil_health}
  note_key: "rule.legume_present"
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
"""

SEED_SOIL = {
    "schema_version": 1,
    "location_id": "31.04_31.38",
    "source_type": "hwsd2",
    "source_name": "FAO/IIASA HWSD v2.0",
    "source_url": "https://www.fao.org/soils-portal/data-hub/soil-maps-and-databases/harmonized-world-soil-database-v20/en/",
    "dataset_version": "2.0",
    "retrieval_date": None,
    "spatial_representation": "gridded",
    "spatial_resolution": "1 km",
    "selection_note": "dominant soil unit in the cell; layers 0-20 and 20-40 cm",
    "fields": {
        "soil_texture": {"v": None, "unit": "USDA class", "status": "missing"},
        "soil_depth_cm": {"v": None, "unit": "cm", "status": "missing"},
        "soil_ph": {"v": None, "unit": "pH", "status": "missing"},
        "organic_carbon": {"v": None, "unit": "<as in source>", "status": "missing"},
        "available_water_capacity": {"v": None, "unit": "<as in source>", "status": "missing"},
        "soil_ec_dsm": {"v": None, "unit": "dS/m", "status": "missing"},
    },
    "limitations": "Regional estimate. Salinity needs field EC measurement.",
}

SEED_SOURCES_CSV_HEADER = ["source_id", "source_name", "url", "dataset_version", "retrieved",
                           "coverage_start", "coverage_end", "spatial_resolution", "spatial_type",
                           "time_resolution", "units", "missing_value_rule", "file"]
SEED_DATA_DICTIONARY = [
    {"field_name": "crop_id", "description": "stable crop id", "unit": "text",
     "source_url": "FieldShift_Data/cleaned/crop_reference.yaml", "dataset_version": "seed"},
]


def _write_if_absent(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _write_json_if_absent(path: Path, obj) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return True


def init_data(data_dir: Path) -> dict:
    """Create the skeleton. Returns a summary of created paths."""
    data_dir = Path(data_dir)
    created: list[str] = []
    for d in DIRS:
        (data_dir / d).mkdir(parents=True, exist_ok=True)

    # references
    if _write_if_absent(data_dir / "references" / "rotation_templates.yaml", SEED_ROTATION_TEMPLATES):
        created.append("references/rotation_templates.yaml")
    if _write_if_absent(data_dir / "references" / "rotation_rules.yaml", SEED_ROTATION_RULES):
        created.append("references/rotation_rules.yaml")
    if _write_if_absent(data_dir / "references" / "links.md", "# Links\n\n(see DATA.md §4 for the full source list)\n"):
        created.append("references/links.md")

    # cleaned
    if _write_if_absent(data_dir / "cleaned" / "crop_reference.yaml", SEED_CROP_REFERENCE):
        created.append("cleaned/crop_reference.yaml")
    if _write_if_absent(data_dir / "cleaned" / "soil_31.04_31.38.json",
                        json.dumps(SEED_SOIL, indent=2, ensure_ascii=False) + "\n"):
        created.append("cleaned/soil_31.04_31.38.json")

    # metadata
    if _write_if_absent(data_dir / "metadata" / "retrieval_log.jsonl", ""):
        created.append("metadata/retrieval_log.jsonl")
    if _write_if_absent(data_dir / "metadata" / "sources.csv",
                        ",".join(SEED_SOURCES_CSV_HEADER) + "\n"):
        created.append("metadata/sources.csv")
    if _write_if_absent(data_dir / "metadata" / "data_dictionary.csv",
                        "field_name,description,unit,source_url,dataset_version\n"):
        created.append("metadata/data_dictionary.csv")

    # README
    if _write_if_absent(data_dir / "README.md", "# FieldShift_Data\n\nSeed skeleton created by `fieldshift init-data`.\n"):
        created.append("README.md")

    return {"data_dir": str(data_dir), "created": created}
