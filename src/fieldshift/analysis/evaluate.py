"""Deterministic Phase 6 evaluator for comparing existing and candidate rotations.

The module joins cleaned daily climate, the sourced crop table, a soil record,
and user supplied sequences. It returns score-bearing Strategy models; wording
and exports belong to Phase 7.
"""

from __future__ import annotations

from datetime import date
from itertools import pairwise
from typing import Any

import pandas as pd

from ..data.soil import field_value, soil_flags, soil_status
from ..models import Indicator, PriorityResult, SequenceStep, Strategy, StrategyKind
from .climate import aggregate_windows, exposure_indicators
from .compare import (
    equal_weights_order,
    overall_band,
    overall_number,
    priority_score,
    rank_strategies,
    too_close,
)
from .confidence import confidence_level
from .priorities import PRIORITY_INDICATORS, build_weights
from .rotation import evaluate_rules
from .seasons import crop_window_dates, window_has_no_missing
from .sensitivity import priority_sensitivity, sowing_date_sensitivity
from .soilfit import ph_fit, salinity_fit
from .water import (
    etc_window,
    irrigation_dependence_band,
    kc_series,
    rain_coverage_pct,
    water_vs_access,
)

_LABELS = {
    "heat_days": ("Heat exposure", "days/window"),
    "cold_days": ("Cold exposure", "days/window"),
    "frost_days": ("Frost exposure", "days/window"),
    "rain_window_mm": ("Rainfall", "mm/window"),
    "temp_in_range_pct": ("Temperature suitability", "% of days"),
    "days_above_tmax": ("Days above crop maximum", "days/window"),
    "days_below_tmin": ("Days below crop minimum", "days/window"),
    "etc_window_mm": ("Estimated crop water need (ETc)", "mm/season"),
    "rain_coverage_pct": ("Rain coverage of ETc", "%"),
    "irrigation_dependence": ("Irrigation dependence", "band"),
    "water_vs_access": ("Water demand vs reported access", "band"),
    "ph_fit": ("Soil pH fit", "band"),
    "salinity_fit": ("Salinity fit", "band"),
    "drought_sensitivity": ("Crop drought sensitivity", "class"),
    "water_demand_rel": ("Relative annual ETc", "relative band"),
}
_DEFAULT_BANDS = {
    "heat_days": {"good_max": 2, "moderate_max": 10},
    "cold_days": {"good_max": 5, "moderate_max": 20},
    "frost_days": {"good_max": 0, "moderate_max": 3},
    "temp_in_range_pct": {"good_min": 70, "moderate_min": 40},
    "days_above_tmax": {"good_max": 2, "moderate_max": 10},
    "days_below_tmin": {"good_max": 0, "moderate_max": 3},
    "water_demand_rel": {"good_max": 0.75, "moderate_max": 0.90},
    "overall_too_close": 0.05,
}
_DEFAULT_THRESHOLDS = {
    "hot_day_tmax_c": 35,
    "cold_day_tmin_c": 5,
    "frost_day_tmin_c": 0,
    "min_windows": 3,
    "stage_split_if_missing": {"ini": 0.15, "dev": 0.25, "mid": 0.40, "late": 0.20},
}


def _v(crop: dict, field: str) -> Any:
    value = crop.get(field)
    return value.get("v") if isinstance(value, dict) else value


def _status(crop: dict, field: str) -> str:
    value = crop.get(field)
    return str(value.get("status", "missing")) if isinstance(value, dict) else "missing"


def _band(value: float | None, rules: dict, *, higher_is_better: bool = False) -> str:
    if value is None or not rules:
        return "Unknown"
    if higher_is_better:
        if value >= rules["good_min"]:
            return "Good"
        if value >= rules["moderate_min"]:
            return "Moderate"
        return "Poor"
    if value <= rules["good_max"]:
        return "Good"
    if value <= rules["moderate_max"]:
        return "Moderate"
    return "Poor"


def _complete_windows(
    daily: pd.DataFrame, crop: dict, latitude: float
) -> list[tuple[date, date, pd.DataFrame]]:
    if daily.empty or "date" not in daily:
        return []
    frame = daily.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.date
    frame = frame.dropna(subset=["date"]).sort_values("date")
    if frame.empty:
        return []
    start, end = frame["date"].iloc[0], frame["date"].iloc[-1]
    if not isinstance(start, date) or not isinstance(end, date):
        return []
    out = []
    for year in range(start.year, end.year + 1):
        dates = crop_window_dates(crop, year)
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


def _metric_values(
    daily: pd.DataFrame,
    crop: dict,
    latitude: float,
    soil_record: dict,
    water_availability: str,
    thresholds: dict,
    bands: dict,
    stage_split_defaults: dict,
) -> tuple[dict[str, dict], set[str], int, float | None]:
    """Return per-crop indicators, quality flags, window count, and median ETc."""
    flags: set[str] = set()
    windows = _complete_windows(daily, crop, latitude)
    crop_id = crop.get("crop_id")
    if not windows:
        flags.add("few_windows")

    window_dicts = []
    etc_values: list[float] = []
    coverages: list[float] = []
    for _, _, frame in windows:
        window_dicts.append(
            {
                "tmax": frame["t_max_c"].tolist(),
                "tmin": frame["t_min_c"].tolist(),
                "tmean": frame["t_mean_c"].tolist(),
                "rain": frame["rain_mm"].tolist(),
            }
        )
        duration = _v(crop, "growth_duration_days")
        kc_data = _v(crop, "kc")
        stage_data = _v(crop, "stage_days")
        if stage_data is None and duration is not None and kc_data is not None:
            split = stage_split_defaults
            flags.add("stage_split_assumed")
        else:
            split = None
        kc = kc_series(stage_data, kc_data, duration, split)
        etc = etc_window(frame.to_dict("records"), kc)
        if etc is not None:
            etc_values.append(etc)
            coverage = rain_coverage_pct(float(frame["rain_mm"].sum()), etc)
            if coverage is not None:
                coverages.append(coverage)
    if etc_values:
        flags.add("et0_estimated")

    reference = _v(crop, "water_requirement_mm_ref")
    if isinstance(reference, dict) and etc_values:
        ref_min, ref_max = reference.get("min"), reference.get("max")
        if ref_min is not None and ref_max is not None:
            median_etc = aggregate_windows(etc_values)["median"]
            if median_etc < ref_min * 0.7 or median_etc > ref_max * 1.3:
                flags.add("etc_vs_reference_gap")

    climate = exposure_indicators(window_dicts, crop, thresholds)
    metrics: dict[str, dict] = {}
    for key in (
        "heat_days",
        "cold_days",
        "frost_days",
        "temp_in_range_pct",
        "days_above_tmax",
        "days_below_tmin",
        "rain_window_mm",
    ):
        stats = climate.get(key)
        metrics[key] = stats or aggregate_windows([])
    metrics["etc_window_mm"] = aggregate_windows(etc_values)
    metrics["rain_coverage_pct"] = aggregate_windows(coverages)

    thresholds_by_id = {
        "heat_days": "heat_days",
        "cold_days": "cold_days",
        "frost_days": "frost_days",
        "days_above_tmax": "days_above_tmax",
        "days_below_tmin": "days_below_tmin",
    }
    for indicator, rule_id in thresholds_by_id.items():
        stats = metrics.get(indicator, {})
        stats["band"] = _band(stats.get("median"), bands.get(rule_id, {}))
    for indicator in ("temp_in_range_pct",):
        stats = metrics.get(indicator, {})
        stats["band"] = _band(stats.get("median"), bands.get(indicator, {}), higher_is_better=True)

    et_stats = metrics["etc_window_mm"]
    et_stats["band"] = "Unknown" if et_stats["median"] is None else "Moderate"
    coverage_stats = metrics["rain_coverage_pct"]
    dependence_values = [irrigation_dependence_band(c) for c in coverages]
    dependence_stats = aggregate_windows(coverages)
    dep_median = (
        "low"
        if dependence_values and coverage_stats["median"] >= 75
        else "moderate"
        if dependence_values and coverage_stats["median"] >= 25
        else "high"
        if dependence_values
        else "Unknown"
    )
    dependence_stats["category"] = dep_median
    dependence_stats["band"] = {"low": "Good", "moderate": "Moderate", "high": "Poor"}.get(
        dep_median, "Unknown"
    )
    metrics["irrigation_dependence"] = dependence_stats
    metrics["water_vs_access"] = {
        "median": None,
        "band": water_vs_access(dep_median, water_availability),
    }

    soil_ph = field_value(soil_record, "soil_ph")
    ec = field_value(soil_record, "soil_ec_dsm")
    ph_range = _v(crop, "soil_ph_range")
    ph_band = ph_fit(soil_ph, ph_range)
    sal_band = salinity_fit(ec, _v(crop, "salinity_threshold_ece_dsm"))
    metrics["ph_fit"] = {"median": None, "band": ph_band}
    metrics["salinity_fit"] = {"median": None, "band": sal_band}
    drought = _v(crop, "drought_sensitivity")
    drought_band = {"low": "Good", "medium": "Moderate", "high": "Poor"}.get(drought, "Unknown")
    metrics["drought_sensitivity"] = {"median": None, "category": drought, "band": drought_band}

    if not windows:
        for key, value in metrics.items():
            if key not in ("ph_fit", "salinity_fit", "drought_sensitivity"):
                value.update(median=None, min=None, max=None, n=0, band="Unknown")
    if soil_status(soil_record) == "unknown":
        flags.add("soil_unknown")
    if ec is None:
        flags.add("salinity_unassessed")
    for field in (
        "growth_duration_days",
        "stage_days",
        "kc",
        "temperature_c",
        "drought_sensitivity",
        "salinity_threshold_ece_dsm",
        "soil_ph_range",
    ):
        status = _status(crop, field)
        if status == "placeholder":
            flags.add("crop_value_placeholder")
        elif status == "missing" or _v(crop, field) is None:
            flags.add("crop_value_missing")
    temp_values = _v(crop, "temperature_c") or {}
    if any(temp_values.get(key) is None for key in ("topmn", "topmx", "tmin", "tmax")):
        flags.add("crop_value_missing")
    if crop_id == "rice":
        flags.add("rice_gross_water_underestimated")
    if windows and len(windows) < int(thresholds.get("min_windows", 3)):
        flags.add("few_windows")
    return metrics, flags, len(windows), aggregate_windows(etc_values)["median"]


def evaluate_rotation_set(
    daily_climate: pd.DataFrame,
    crop_table: dict | Any,
    soil_record: dict,
    latitude: float,
    existing_sequence: list[dict],
    alternatives: list[dict],
    *,
    ranked_priorities: list[str] | None = None,
    skipped_priorities: list[str] | None = None,
    water_availability: str = "unknown",
    rules: list[dict] | None = None,
    thresholds: dict | None = None,
    bands: dict | None = None,
    flags: list[str] | None = None,
    horizon: int = 1,
    baseline_assumed: bool = False,
) -> dict:
    """Compare an existing rotation and candidate sequences using Phase 6 rules.

    Each alternative is ``{"id", "name", "kind", "sequence"}``; sequences
    use the format consumed by :class:`SequenceStep`. The return value contains
    Strategy models plus comparison metadata for Phase 7 to explain/export.
    """
    doc = crop_table.doc if hasattr(crop_table, "doc") else crop_table
    if len(alternatives) < 2:
        raise ValueError("Phase 6 comparison requires at least two alternative strategies")
    crops = {c["crop_id"]: c for c in doc.get("crops", [])}
    thresholds = {**_DEFAULT_THRESHOLDS, **(thresholds or {})}
    bands = {**_DEFAULT_BANDS, **(bands or {})}
    rules = rules or []
    stage_split_defaults = (
        doc.get("defaults", {}).get("stage_split_if_missing")
        or _DEFAULT_THRESHOLDS["stage_split_if_missing"]
    )
    priorities = ranked_priorities or []
    skipped = skipped_priorities or []
    global_flags = set(flags or []) | set(soil_flags(soil_record))
    if baseline_assumed:
        global_flags.add("baseline_assumed")
    required_climate = ["t_mean_c", "t_max_c", "t_min_c", "rain_mm", "solar_mj_m2"]
    present_climate = [col for col in required_climate if col in daily_climate]
    if present_climate and any(daily_climate[col].isna().mean() >= 0.05 for col in present_climate):
        global_flags.add("climate_missing_values")
    if "date" in daily_climate:
        dates = pd.to_datetime(daily_climate["date"], errors="coerce").dropna().sort_values()
        if not dates.empty:
            span_days = (dates.iloc[-1] - dates.iloc[0]).days + 1
            missing_day_share = 1 - dates.nunique() / span_days
        else:
            missing_day_share = 0.0
        if missing_day_share >= 0.05:
            global_flags.add("date_gaps")

    prepared: list[dict] = []
    specs = [
        {
            "id": "existing",
            "name": "Existing rotation",
            "kind": "existing",
            "sequence": existing_sequence,
        },
        *alternatives,
    ]
    for spec in specs:
        sequence = spec.get("sequence", [])
        seq_flags = set(global_flags)
        per_crop: dict[str, dict] = {}
        n_windows_total = 0
        windows_per_crop: list[int] = []
        for step in sequence:
            cid = step.get("crop_id", step.get("crop"))
            if cid == "fallow":
                continue
            if cid not in crops:
                seq_flags.update({"crop_not_in_reference", "crop_value_missing"})
                per_crop[cid] = {
                    key: {"median": None, "min": None, "max": None, "n": 0, "band": "Unknown"}
                    for key in (*_LABELS, "rain_window_mm")
                }
                windows_per_crop.append(0)
                continue
            if cid not in per_crop:
                values, crop_flags, count, _ = _metric_values(
                    daily_climate,
                    crops[cid],
                    latitude,
                    soil_record,
                    water_availability,
                    thresholds,
                    bands,
                    stage_split_defaults,
                )
                per_crop[cid] = values
                seq_flags.update(crop_flags)
                n_windows_total += count
                windows_per_crop.append(count)
        confidence_windows = min(windows_per_crop, default=0)
        rule_info = evaluate_rules(rules, sequence, crops)
        windows_by_crop = {
            cid: [(a, b) for a, b, _ in _complete_windows(daily_climate, crops[cid], latitude)]
            for cid in per_crop
            if cid in crops
        }
        chosen_crops = [
            step.get("crop_id", step.get("crop"))
            for step in sequence
            if step.get("crop_id", step.get("crop")) in windows_by_crop
        ]
        for first, second in pairwise(chosen_crops):
            if first != second and any(
                max(a, c) <= min(b, d)
                for a, b in windows_by_crop[first]
                for c, d in windows_by_crop[second]
            ):
                seq_flags.add("season_overlap")
                break
        if rule_info["notes"]:
            seq_flags.add("rule_unsupported")

        annual_etc: list[float] = []
        for year in sorted({s.get("year", 1) for s in sequence}):
            total, known = 0.0, False
            complete = True
            for step in sequence:
                if step.get("year", 1) != year:
                    continue
                cid = step.get("crop_id", step.get("crop"))
                if cid == "fallow":
                    known = True
                    continue
                if cid in per_crop:
                    median = per_crop[cid]["etc_window_mm"].get("median")
                    if median is not None:
                        total += median
                        known = True
                    else:
                        complete = False
                else:
                    complete = False
            if known and complete:
                annual_etc.append(total)
        etc_year = aggregate_windows(annual_etc)

        indicator_data: dict[str, dict] = {}
        for values in per_crop.values():
            for key, val in values.items():
                indicator_data.setdefault(
                    key, {"median": [], "min": [], "max": [], "bands": [], "category": []}
                )
                for field in ("median", "min", "max"):
                    if val.get(field) is not None:
                        indicator_data[key][field].append(val[field])
                indicator_data[key]["bands"].append(val.get("band", "Unknown"))
                if val.get("category") is not None:
                    indicator_data[key]["category"].append(val["category"])
        indicator_data["etc_year_mm"] = {
            "median": [] if etc_year["median"] is None else [etc_year["median"]],
            "min": [] if etc_year["min"] is None else [etc_year["min"]],
            "max": [] if etc_year["max"] is None else [etc_year["max"]],
            "bands": [],
            "category": [],
        }
        indicators: list[Indicator] = []
        for key, vals in indicator_data.items():
            med = aggregate_windows(vals["median"])
            any_unknown = "Unknown" in vals["bands"]
            if key == "etc_year_mm":
                band = "Unknown" if med["median"] is None else "Moderate"
            elif key in (
                "ph_fit",
                "salinity_fit",
                "water_vs_access",
                "irrigation_dependence",
                "drought_sensitivity",
            ):
                # Preserve a categorical indicator band without introducing a numeric score.
                bands_seen = [b for b in vals["bands"] if b != "Unknown"]
                band_name = (
                    "Unknown" if not bands_seen else max(set(bands_seen), key=bands_seen.count)
                )
                band = band_name
            elif key not in bands or not bands[key]:
                band = "Unknown"
            else:
                band_name = _band(
                    med["median"], bands.get(key, {}), higher_is_better=key == "temp_in_range_pct"
                )
                band = band_name
            if key == "drought_sensitivity" and vals["category"]:
                band = {"low": "Good", "medium": "Moderate", "high": "Poor"}.get(
                    max(set(vals["category"]), key=vals["category"].count), "Unknown"
                )
            if any_unknown and key != "etc_year_mm":
                band = "Unknown"
                med = {"median": None, "min": None, "max": None, "n": 0}
            label, unit = _LABELS.get(key, (key.replace("_", " "), "band"))
            is_categorical = key in (
                "ph_fit",
                "salinity_fit",
                "water_vs_access",
                "irrigation_dependence",
                "drought_sensitivity",
            )
            indicators.append(
                Indicator(
                    id=key,
                    label=label,
                    median=None if is_categorical else med["median"],
                    min=None if is_categorical else med["min"],
                    max=None if is_categorical else med["max"],
                    unit=unit,
                    band=band,
                    status="estimated"
                    if key.startswith("etc")
                    else ("unknown" if band == "Unknown" else "observed"),
                    n_windows=n_windows_total,
                    dataset="NASA POWER + FAO-56"
                    if key.startswith(("etc", "rain_coverage"))
                    else (
                        "NASA POWER"
                        if key not in ("ph_fit", "salinity_fit", "drought_sensitivity")
                        else "FAO crop reference + soil record"
                    ),
                )
            )

        # Cross-strategy water-demand band is assigned after all annual ETc values exist.
        prepared.append(
            {
                "id": spec.get("id"),
                "name": spec.get("name", spec.get("id")),
                "kind": spec.get("kind", "template"),
                "sequence": sequence,
                "indicators": indicators,
                "indicator_data": indicator_data,
                "flags": seq_flags,
                "rule_info": rule_info,
                "n_windows": n_windows_total,
                "confidence_windows": confidence_windows,
                "overall_value": None,
                "priority_scores": {},
                "etc_year": etc_year["median"],
            }
        )

    et_values = [p["etc_year"] for p in prepared if p["etc_year"] is not None]
    max_et = max(et_values) if et_values else None
    for item in prepared:
        ratio = (item["etc_year"] / max_et) if item["etc_year"] is not None and max_et else None
        if ratio is None:
            rel_band = "Unknown"
        elif len(et_values) > 1 and (max(et_values) - min(et_values)) / max(et_values) < 0.05:
            rel_band = "Similar"
        else:
            rel_band = _band(ratio, bands.get("water_demand_rel", {}))
        item["indicators"].append(
            Indicator(
                id="water_demand_rel",
                label=_LABELS["water_demand_rel"][0],
                median=ratio,
                unit="relative",
                band=rel_band,
                status="estimated" if ratio is not None else "unknown",
                dataset="NASA POWER + FAO-56",
                n_windows=item["n_windows"],
            )
        )

    weights = build_weights(priorities, skipped)
    all_priorities = list(PRIORITY_INDICATORS)
    for item in prepared:
        by_id = {i.id: i for i in item["indicators"]}
        p_scores: dict[str, float | None] = {}
        p_results: dict[str, PriorityResult] = {}
        for priority, ids in PRIORITY_INDICATORS.items():
            bands_for_priority = [by_id[i].band for i in ids if i in by_id]
            score = priority_score(bands_for_priority)
            p_scores[priority] = score
            p_results[priority] = PriorityResult(
                band=overall_band(score),
                indicators=[i for i in ids if i in by_id],
            )
            if priority == "budget_market" and priority in (priorities + skipped):
                item["flags"].add("priority_unscored")
        value, basis = overall_number(p_scores, weights)
        item["overall_value"] = value
        item["priority_scores"] = p_scores
        item["priority_results"] = p_results
        item["overall_basis"] = basis
        item["overall_band"] = overall_band(value)

    order = rank_strategies(prepared)
    eq_order = equal_weights_order(prepared, all_priorities)
    prio_sens = priority_sensitivity(prepared, weights, seed=42, n_trials=100, perturbation=0.20)
    close_pairs = []
    ordered_known = [
        p
        for p in sorted(prepared, key=lambda x: order.index(x["id"]))
        if p["overall_value"] is not None
    ]
    for left, right in pairwise(ordered_known):
        if too_close(
            left["overall_value"],
            right["overall_value"],
            float(bands.get("overall_too_close", 0.05)),
        ):
            close_pairs.append([left["id"], right["id"]])

    # Cache sowing-date sensitivity for referenced crops
    crop_sowing_cache = {}
    for cid, crop_obj in crops.items():
        crop_sowing_cache[cid] = sowing_date_sensitivity(
            daily_climate, crop_obj, latitude, thresholds, stage_split_defaults
        )

    strategies = []
    for item in prepared:
        flags_list = sorted(item["flags"])
        has_placeholder = "crop_value_placeholder" in flags_list
        soil_state = soil_status(soil_record)
        conf = confidence_level(flags_list, soil_state, item["confidence_windows"], has_placeholder)
        sequence_models = [
            SequenceStep.model_validate(
                {
                    "slot": step.get("slot", "winter"),
                    "year": step.get("year", 1),
                    "crop_id": step.get("crop_id", step.get("crop", "unknown")),
                }
            )
            for step in item["sequence"]
        ]
        strat_sowing_sens = []
        seen_crops = set()
        for step in item["sequence"]:
            cid = step.get("crop_id", step.get("crop"))
            if cid in crop_sowing_cache and crop_sowing_cache[cid] and cid not in seen_crops:
                seen_crops.add(cid)
                strat_sowing_sens.append(crop_sowing_cache[cid])
        strategies.append(
            Strategy(
                id=item["id"],
                kind=StrategyKind(item["kind"]),
                name=item["name"],
                sequence=sequence_models,
                indicators=item["indicators"],
                priority_results=item["priority_results"],
                overall={
                    "band": item["overall_band"],
                    "value": item["overall_value"],
                    "basis": item["overall_basis"],
                    "suppressed": item["overall_value"] is None,
                },
                confidence=conf,
                flags=flags_list,
                sowing_sensitivity=strat_sowing_sens,
            )
        )
    return {
        "strategies": strategies,
        "comparison": {
            "order": order,
            "too_close": close_pairs,
            "order_equal_weights": eq_order,
            "ranking_stable": order == eq_order,
            "priority_sensitivity": prio_sens,
        },
        "weights": weights,
        "priority_indicator_mapping": PRIORITY_INDICATORS,
    }
