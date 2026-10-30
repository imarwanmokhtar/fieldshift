"""analysis/climate.py — exposure and fit indicators (Part 7.3)."""
from __future__ import annotations


def heat_days(tmax_series: list[float], threshold: float = 35.0) -> int:
    return sum(1 for t in tmax_series if t is not None and t >= threshold)


def cold_days(tmin_series: list[float], threshold: float = 5.0) -> int:
    return sum(1 for t in tmin_series if t is not None and t <= threshold)


def frost_days(tmin_series: list[float], threshold: float = 0.0) -> int:
    return sum(1 for t in tmin_series if t is not None and t <= threshold)


def temp_in_range_pct(tmean_series: list[float], topmn: float | None,
                      topmx: float | None) -> float | None:
    if topmn is None or topmx is None:
        return None
    vals = [t for t in tmean_series if t is not None]
    if not vals:
        return None
    in_range = sum(1 for t in vals if topmn <= t <= topmx)
    return round(100.0 * in_range / len(vals), 1)


def days_above_tmax(tmax_series: list[float], tmax: float | None) -> int | None:
    if tmax is None:
        return None
    return sum(1 for t in tmax_series if t is not None and t > tmax)


def days_below_tmin(tmin_series: list[float], tmin: float | None) -> int | None:
    if tmin is None:
        return None
    return sum(1 for t in tmin_series if t is not None and t < tmin)


def aggregate_windows(values_per_window: list[float]) -> dict:
    """Median/min/max across windows."""
    if not values_per_window:
        return {"median": None, "min": None, "max": None, "n": 0}
    s = sorted(values_per_window)
    n = len(s)
    med = s[n // 2] if n % 2 == 1 else (s[n // 2 - 1] + s[n // 2]) / 2
    return {"median": med, "min": s[0], "max": s[-1], "n": n}


def exposure_indicators(window_days: list[dict], crop: dict, thresholds: dict) -> dict:
    """Compute per-window exposure+fit indicators, then aggregate.

    window_days: list of per-window dicts with tmax/tmin/tmean/rain lists.
    Returns dict of indicator_id -> {median,min,max,n} or scalar for fit.
    """
    hot_t = thresholds.get("hot_day_tmax_c", 35)
    cold_t = thresholds.get("cold_day_tmin_c", 5)
    frost_t = thresholds.get("frost_day_tmin_c", 0)
    temp = crop.get("temperature_c", {}).get("v") or {}
    topmn = temp.get("topmn")
    topmx = temp.get("topmx")
    tmax_crop = temp.get("tmax")
    tmin_crop = temp.get("tmin")

    heat_list, cold_list, frost_list = [], [], []
    rain_list = []
    temp_range_list = []
    above_list = []
    below_list = []
    for w in window_days:
        tmaxs = w.get("tmax", [])
        tmins = w.get("tmin", [])
        tmeans = w.get("tmean", [])
        rains = w.get("rain", [])
        heat_list.append(heat_days(tmaxs, hot_t))
        cold_list.append(cold_days(tmins, cold_t))
        frost_list.append(frost_days(tmins, frost_t))
        rain_list.append(sum(r for r in rains if r is not None))
        # fit (only if crop range present)
        if topmn is not None and topmx is not None:
            temp_range_list.append(temp_in_range_pct(tmeans, topmn, topmx))
        if tmax_crop is not None:
            above_list.append(days_above_tmax(tmaxs, tmax_crop))
        if tmin_crop is not None:
            below_list.append(days_below_tmin(tmins, tmin_crop))

    out = {
        "heat_days": aggregate_windows(heat_list),
        "cold_days": aggregate_windows(cold_list),
        "frost_days": aggregate_windows(frost_list),
        "rain_window_mm": aggregate_windows(rain_list),
    }
    if temp_range_list and topmn is not None:
        out["temp_in_range_pct"] = aggregate_windows([x for x in temp_range_list if x is not None])
    else:
        out["temp_in_range_pct"] = None
    if above_list and tmax_crop is not None:
        out["days_above_tmax"] = aggregate_windows([x for x in above_list if x is not None])
    else:
        out["days_above_tmax"] = None
    if below_list and tmin_crop is not None:
        out["days_below_tmin"] = aggregate_windows([x for x in below_list if x is not None])
    else:
        out["days_below_tmin"] = None
    return out
