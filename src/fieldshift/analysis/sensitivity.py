"""analysis/sensitivity.py — Sowing-date and priority sensitivity (Phase 8)."""

from __future__ import annotations

import random
from typing import Any

import pandas as pd

from .climate import aggregate_windows, exposure_indicators
from .compare import overall_number, rank_strategies
from .seasons import crop_window_dates, window_has_no_missing
from .water import etc_window, kc_series


def _complete_windows_for_anchor(
    daily: pd.DataFrame, crop: dict, latitude: float, anchor: str = "mid"
) -> list[tuple[Any, Any, pd.DataFrame]]:
    if daily.empty or "date" not in daily:
        return []
    frame = daily.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.date
    frame = frame.dropna(subset=["date"]).sort_values("date")
    if frame.empty:
        return []
    start, end = frame["date"].iloc[0], frame["date"].iloc[-1]
    out = []
    for year in range(start.year, end.year + 1):
        dates = crop_window_dates(crop, year, anchor=anchor)
        if dates is None:
            continue
        win_start, win_end = dates
        if win_start < start or win_end > end:
            continue
        if not window_has_no_missing(frame, win_start, win_end):
            continue
        sub = frame[(frame["date"] >= win_start) & (frame["date"] <= win_end)].copy()
        sub["j"] = [d.timetuple().tm_yday for d in sub["date"]]
        sub["lat"] = latitude
        out.append((win_start, win_end, sub))
    return out


def evaluate_crop_at_anchor(
    daily: pd.DataFrame,
    crop: dict,
    latitude: float,
    thresholds: dict,
    stage_split_defaults: dict,
    anchor: str = "mid",
) -> dict[str, float | None]:
    """Compute key numeric indicators for a single crop at a specific sowing anchor."""
    windows = _complete_windows_for_anchor(daily, crop, latitude, anchor=anchor)
    if not windows:
        return {
            "etc_window_mm": None,
            "heat_days": None,
            "cold_days": None,
            "frost_days": None,
            "temp_in_range_pct": None,
            "rain_window_mm": None,
            "n_windows": 0,
        }

    window_dicts = []
    etc_values: list[float] = []
    for _, _, frame in windows:
        window_dicts.append(
            {
                "tmax": frame["t_max_c"].tolist(),
                "tmin": frame["t_min_c"].tolist(),
                "tmean": frame["t_mean_c"].tolist(),
                "rain": frame["rain_mm"].tolist(),
            }
        )
        dur_obj = crop.get("growth_duration_days")
        duration = dur_obj.get("v") if isinstance(dur_obj, dict) else dur_obj
        kc_obj = crop.get("kc")
        kc_data = kc_obj.get("v") if isinstance(kc_obj, dict) else kc_obj
        stg_obj = crop.get("stage_days")
        stage_data = stg_obj.get("v") if isinstance(stg_obj, dict) else stg_obj
        split = (
            stage_split_defaults
            if (stage_data is None and duration is not None and kc_data is not None)
            else None
        )
        kc = kc_series(stage_data, kc_data, duration, split)
        etc = etc_window(frame.to_dict("records"), kc)
        if etc is not None:
            etc_values.append(etc)

    climate = exposure_indicators(window_dicts, crop, thresholds)
    etc_stats = aggregate_windows(etc_values)

    return {
        "etc_window_mm": etc_stats.get("median"),
        "heat_days": (climate.get("heat_days") or {}).get("median"),
        "cold_days": (climate.get("cold_days") or {}).get("median"),
        "frost_days": (climate.get("frost_days") or {}).get("median"),
        "temp_in_range_pct": (climate.get("temp_in_range_pct") or {}).get("median"),
        "rain_window_mm": (climate.get("rain_window_mm") or {}).get("median"),
        "n_windows": len(windows),
    }


def sowing_date_sensitivity(
    daily: pd.DataFrame,
    crop: dict,
    latitude: float,
    thresholds: dict,
    stage_split_defaults: dict,
) -> dict[str, Any] | None:
    """Compute indicators across start, mid, end of crop sowing window and return the spread."""
    window_obj = crop.get("sowing_window") or {}
    duration_obj = crop.get("growth_duration_days") or {}
    if window_obj.get("status") in ("missing", "placeholder"):
        return None
    if duration_obj.get("status") in ("missing", "placeholder"):
        return None
    win = window_obj.get("v")
    if not win or "start" not in win or "end" not in win:
        return None
    dur = duration_obj.get("v")
    if not dur:
        return None

    crop_id = crop.get("crop_id", "unknown")
    start_metrics = evaluate_crop_at_anchor(
        daily, crop, latitude, thresholds, stage_split_defaults, anchor="start"
    )
    mid_metrics = evaluate_crop_at_anchor(
        daily, crop, latitude, thresholds, stage_split_defaults, anchor="mid"
    )
    end_metrics = evaluate_crop_at_anchor(
        daily, crop, latitude, thresholds, stage_split_defaults, anchor="end"
    )

    indicator_keys = [
        "etc_window_mm",
        "heat_days",
        "cold_days",
        "frost_days",
        "temp_in_range_pct",
        "rain_window_mm",
    ]
    indicators_result = {}
    for key in indicator_keys:
        s_val = start_metrics.get(key)
        m_val = mid_metrics.get(key)
        e_val = end_metrics.get(key)
        vals = [v for v in (s_val, m_val, e_val) if v is not None]
        spread = round(max(vals) - min(vals), 1) if vals else None
        indicators_result[key] = {
            "start": round(s_val, 1) if s_val is not None else None,
            "mid": round(m_val, 1) if m_val is not None else None,
            "end": round(e_val, 1) if e_val is not None else None,
            "spread": spread,
        }

    return {
        "crop_id": crop_id,
        "sowing_window": f"{win.get('start')} .. {win.get('end')}",
        "period": (
            f"{pd.to_datetime(daily['date']).min():%Y-%m-%d}/"
            f"{pd.to_datetime(daily['date']).max():%Y-%m-%d}"
            if not daily.empty and "date" in daily
            else None
        ),
        "dataset": "NASA POWER + FAO crop reference",
        "windows": {
            "start": start_metrics.get("n_windows", 0),
            "mid": mid_metrics.get("n_windows", 0),
            "end": end_metrics.get("n_windows", 0),
        },
        "units": {
            "etc_window_mm": "mm/season",
            "heat_days": "days/window",
            "cold_days": "days/window",
            "frost_days": "days/window",
            "temp_in_range_pct": "% of days",
            "rain_window_mm": "mm/window",
        },
        "indicators": indicators_result,
    }


def priority_sensitivity(
    prepared_strategies: list[dict],
    base_weights: dict[str, float],
    seed: int = 42,
    n_trials: int = 100,
    perturbation: float = 0.20,
) -> dict[str, Any] | None:
    """Perturb priority weights with a fixed seed and measure strategy ranking stability."""
    valid_strategies = [s for s in prepared_strategies if s.get("overall_value") is not None]
    if len(valid_strategies) < 2:
        return None

    base_order = rank_strategies(prepared_strategies)
    rng = random.Random(seed)
    order_preserved_count = 0
    top_preserved_count = 0

    for _ in range(n_trials):
        perturbed_weights: dict[str, float] = {}
        for p, w in base_weights.items():
            if w > 0:
                factor = 1.0 + rng.uniform(-perturbation, perturbation)
                perturbed_weights[p] = max(0.0001, w * factor)
            else:
                perturbed_weights[p] = 0.0

        total = sum(perturbed_weights.values())
        if total > 0:
            perturbed_weights = {p: w / total for p, w in perturbed_weights.items()}

        trial_strategies = []
        for s in prepared_strategies:
            val, _ = overall_number(s.get("priority_scores", {}), perturbed_weights)
            trial_strategies.append({"id": s["id"], "overall_value": val})

        trial_order = rank_strategies(trial_strategies)
        if trial_order == base_order:
            order_preserved_count += 1
        if trial_order and base_order and trial_order[0] == base_order[0]:
            top_preserved_count += 1

    order_pct = round((order_preserved_count / n_trials) * 100, 1)
    top_pct = round((top_preserved_count / n_trials) * 100, 1)
    is_stable = order_pct >= 60.0

    summary = (
        f"Ranking order preserved in {order_pct}% of {n_trials} priority weight "
        f"perturbations (±{int(perturbation * 100)}%); "
        f"top-ranked candidate unchanged in {top_pct}%."
    )

    return {
        "trials": n_trials,
        "seed": seed,
        "perturbation_range": f"±{int(perturbation * 100)}%",
        "order_stable_pct": order_pct,
        "top_stable_pct": top_pct,
        "is_stable": is_stable,
        "summary": summary,
    }
