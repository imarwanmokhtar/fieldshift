"""analysis/soilfit.py — pH and salinity fit (Part 7.5)."""
from __future__ import annotations


def ph_fit(soil_ph: float | None, ph_range: dict | None) -> str:
    if soil_ph is None or not ph_range:
        return "Unknown"
    lo = ph_range.get("ph_min")
    hi = ph_range.get("ph_max")
    if lo is None or hi is None:
        return "Unknown"
    if lo <= soil_ph <= hi:
        return "Good"
    if soil_ph < lo and soil_ph >= lo - 0.5:
        return "Moderate"
    if soil_ph > hi and soil_ph <= hi + 0.5:
        return "Moderate"
    return "Poor"


def salinity_fit(ec: float | None, threshold: float | None) -> str:
    if ec is None or threshold is None:
        return "Unknown"
    if ec <= threshold:
        return "Good"
    if ec <= 2 * threshold:
        return "Moderate"
    return "Poor"
