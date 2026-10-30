"""analysis/water.py — Kc curve, ETc, rain coverage, access match (Part 7.2, 7.4)."""
from __future__ import annotations

from .et0 import et0_hs


def stage_split(duration: int, split: dict) -> tuple[int, int, int, int]:
    """Split duration into (ini, dev, mid, late) by fractions, remainder to mid."""
    ini = round(duration * split.get("ini", 0.15))
    dev = round(duration * split.get("dev", 0.25))
    mid = round(duration * split.get("mid", 0.40))
    late = round(duration * split.get("late", 0.20))
    # fix rounding to sum to duration
    while ini + dev + mid + late < duration:
        mid += 1
    while ini + dev + mid + late > duration:
        if mid > 1:
            mid -= 1
        else:
            break
    return ini, dev, mid, late


def kc_series(stage_days: dict, kc: dict, duration: int,
              split: dict | None = None) -> list[float] | None:
    """Return per-day Kc list of length `duration`, or None if impossible."""
    if not kc or duration is None:
        return None
    ini_d, dev_d, mid_d, late_d = None, None, None, None
    if isinstance(stage_days, dict) and all(k in stage_days for k in ("ini", "dev", "mid", "late")):
        ini_d = stage_days["ini"]
        dev_d = stage_days["dev"]
        mid_d = stage_days["mid"]
        late_d = stage_days["late"]
    else:
        if split is None:
            split = {"ini": 0.15, "dev": 0.25, "mid": 0.40, "late": 0.20}
        ini_d, dev_d, mid_d, late_d = stage_split(duration, split)
    if ini_d + dev_d + mid_d + late_d != duration:
        # adjust mid
        mid_d += duration - (ini_d + dev_d + mid_d + late_d)
    kc_ini = kc.get("ini")
    kc_mid = kc.get("mid")
    kc_end = kc.get("end")
    if kc_ini is None or kc_mid is None or kc_end is None:
        return None
    series = []
    # initial
    for _ in range(ini_d):
        series.append(float(kc_ini))
    # develop
    for i in range(1, dev_d + 1):
        kc = kc_ini + (kc_mid - kc_ini) * (i - 0.5) / max(dev_d, 1)
        series.append(kc)
    # mid
    for _ in range(mid_d):
        series.append(float(kc_mid))
    # late
    for i in range(1, late_d + 1):
        kc = kc_mid + (kc_end - kc_mid) * (i - 0.5) / max(late_d, 1)
        series.append(kc)
    # pad/truncate to duration
    if len(series) < duration:
        series += [float(kc_end)] * (duration - len(series))
    if len(series) > duration:
        series = series[:duration]
    return series


def etc_window(daily_slice: list[dict], kc_list: list[float] | None) -> float | None:
    """ETc = sum Kc_d * ET0_d (mm per window). Returns None if kc missing or no valid ET0."""
    if kc_list is None:
        return None
    total = 0.0
    valid = 0
    for i, row in enumerate(daily_slice):
        if i >= len(kc_list):
            break
        et0 = et0_hs(row["t_max_c"], row["t_min_c"], row["lat"], row["j"])
        if et0 != et0:  # NaN check
            continue
        total += kc_list[i] * et0
        valid += 1
    if valid == 0:
        return None
    return round(total, 2)


def rain_coverage_pct(rain_mm: float, etc_mm: float) -> float | None:
    if etc_mm is None or etc_mm == 0 or rain_mm is None:
        return None
    return min(100.0, 100.0 * rain_mm / etc_mm)


def irrigation_dependence_band(coverage_pct: float | None) -> str:
    if coverage_pct is None:
        return "Unknown"
    if coverage_pct >= 75:
        return "low"
    if coverage_pct >= 25:
        return "moderate"
    return "high"


def water_vs_access(irrigation_dependence: str, water_availability: str | None) -> str:
    dep = irrigation_dependence
    avail = (water_availability or "unknown").lower()
    if dep == "Unknown" or avail == "unknown":
        return "Unknown"
    if dep == "low":
        return "Good"
    if dep == "high":
        if avail == "limited":
            return "Poor"
        if avail == "moderate":
            return "Moderate"
        return "Good"
    # moderate dependence
    if avail == "limited":
        return "Moderate"
    return "Good"
