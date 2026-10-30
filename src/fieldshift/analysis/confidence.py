"""analysis/confidence.py — confidence level per strategy (Part 7.8)."""
from __future__ import annotations


def confidence_level(flags: list[str], soil_status: str = "unknown",
                     n_windows: int = 0, has_placeholder_crop: bool = False) -> str:
    """Lower confidence once for each distinct documented source of uncertainty."""
    level = "high"
    def drop() -> None:
        nonlocal level
        level = "moderate" if level == "high" else "low"

    flag_set = set(flags)
    if soil_status in ("unknown", "regional", "partial") or flag_set & {
        "soil_unknown", "soil_partial", "soil_regional_only"
    }:
        drop()
    if n_windows < 3 or flag_set & {"few_windows", "climate_short_record", "short_record"}:
        drop()
    if has_placeholder_crop or flag_set & {"crop_value_placeholder", "crop_value_missing"}:
        drop()
    if flag_set & {"baseline_assumed", "coordinates_illustrative", "stage_split_assumed"}:
        drop()
    if flag_set & {"climate_missing_values", "date_gaps"}:
        drop()
    return level
