"""Phase 6 tests — analysis test vectors from Part 10."""
import copy
import math
from datetime import date

import pandas as pd
import pytest

from fieldshift.analysis.compare import overall_number, priority_score, too_close
from fieldshift.analysis.et0 import et0_hs, ra_mj
from fieldshift.analysis.evaluate import evaluate_rotation_set
from fieldshift.analysis.priorities import build_weights, roc_weights
from fieldshift.analysis.rotation import load_rules
from fieldshift.analysis.seasons import (
    build_existing_sequence,
    crop_window_dates,
    window_has_no_missing,
    windows_for_crop,
)
from fieldshift.analysis.water import kc_series
from fieldshift.config import load_bands, load_thresholds
from fieldshift.data.crops import load_crop_table


def test_ra_vectors():
    expected = {15: 20.463, 105: 36.663, 196: 40.605, 288: 27.005}
    for j, val in expected.items():
        assert abs(ra_mj(31.04, j) - val) < 0.01, (j, ra_mj(31.04, j))


def test_et0_vectors():
    cases = [(15, 19, 8, 1.993), (105, 28, 14, 4.995),
             (196, 36, 22, 6.672), (288, 29, 16, 3.682)]
    for j, tmax, tmin, exp in cases:
        got = et0_hs(tmax, tmin, 31.04, j)
        assert abs(got - exp) < 0.01, (j, got, exp)


def test_et0_invalid():
    assert et0_hs(10, 15, 31.04, 15) != et0_hs(10, 15, 31.04, 15) or True  # NaN
    assert math.isnan(et0_hs(10, 15, 31.04, 15))
    assert math.isnan(et0_hs(19, None, 31.04, 15))


def test_kc_sum_wheat():
    kc = {"ini": 0.30, "mid": 1.15, "end": 0.25}
    stages = {"ini": 20, "dev": 50, "mid": 60, "late": 30}
    series = kc_series(stages, kc, 160)
    assert series is not None
    assert abs(sum(series) - 132.25) < 1e-9
    # ETc at constant ET0 = 3
    etc = sum(k * 3.0 for k in series)
    assert abs(etc - 396.75) < 1e-6


def test_kc_sum_cotton():
    kc = {"ini": 0.35, "mid": 1.15, "end": 0.70}
    stages = {"ini": 30, "dev": 50, "mid": 60, "late": 55}
    series = kc_series(stages, kc, 195)
    assert series is not None
    assert abs(sum(series) - 167.875) < 1e-9
    etc = sum(k * 3.0 for k in series)
    assert abs(etc - 503.625) < 1e-6


def test_kc_missing_returns_none():
    assert kc_series(None, None, 160) is None
    assert kc_series({"ini": 20, "dev": 50, "mid": 60, "late": 30}, None, 160) is None
    assert kc_series(
        {"ini": 20, "dev": 50, "mid": 60, "late": 30},
        {"ini": 0.3, "mid": 1.15, "end": 0.25},
        None,
    ) is None


def test_stage_split_fallback():
    # missing stage_days but duration present -> split by defaults
    series = kc_series(None, {"ini": 0.3, "mid": 1.15, "end": 0.25}, 100,
                       split={"ini": 0.15, "dev": 0.25, "mid": 0.40, "late": 0.20})
    assert series is not None
    assert len(series) == 100


def test_roc_weights():
    assert [round(x, 4) for x in roc_weights(3)] == [0.6111, 0.2778, 0.1111]
    assert [round(x, 4) for x in roc_weights(4)] == [0.5208, 0.2708, 0.1458, 0.0625]
    assert [round(x, 4) for x in roc_weights(5)] == [0.4567, 0.2567, 0.1567, 0.0900, 0.0400]
    for n in (3, 4, 5):
        assert abs(sum(roc_weights(n)) - 1.0) < 1e-9


def test_soilfit():
    from fieldshift.analysis.soilfit import ph_fit, salinity_fit
    assert ph_fit(7.0, {"ph_min": 6.0, "ph_max": 8.0}) == "Good"
    assert ph_fit(5.7, {"ph_min": 6.0, "ph_max": 8.0}) == "Moderate"
    assert ph_fit(4.0, {"ph_min": 6.0, "ph_max": 8.0}) == "Poor"
    assert ph_fit(7.0, None) == "Unknown"
    assert salinity_fit(1.0, 1.5) == "Good"
    assert salinity_fit(2.0, 1.5) == "Moderate"
    assert salinity_fit(4.0, 1.5) == "Poor"
    assert salinity_fit(None, 1.5) == "Unknown"


def test_window_with_missing_required_column_or_day_is_rejected():
    start, end = date(2020, 1, 1), date(2020, 1, 3)
    base = {"date": ["2020-01-01", "2020-01-02", "2020-01-03"]}
    for col in ("t_mean_c", "t_max_c", "t_min_c", "rain_mm", "solar_mj_m2"):
        base[col] = [1.0, 1.0, 1.0]
    frame = pd.DataFrame(base)
    assert window_has_no_missing(frame, start, end)
    assert not window_has_no_missing(frame.drop(columns="solar_mj_m2"), start, end)
    frame.loc[1, "rain_mm"] = float("nan")
    assert not window_has_no_missing(frame, start, end)


def test_winter_window_crosses_year_and_incomplete_windows_are_dropped():
    crop = {
        "crop_id": "synthetic_winter_crop",
        "sowing_window": {"v": {"start": "11-15", "end": "11-15"}},
        "growth_duration_days": {"v": 160},
    }
    first, last = crop_window_dates(crop, 2011)
    assert first == date(2011, 11, 15)
    assert last.year == 2012
    dates = pd.date_range("2011-01-01", "2015-12-31", freq="D")
    frame = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"), "t_mean_c": 20.0, "t_max_c": 25.0,
        "t_min_c": 15.0, "rain_mm": 0.0, "solar_mj_m2": 15.0,
    })
    start, end = date(2011, 1, 1), date(2015, 12, 31)
    windows = windows_for_crop(crop, [2011, 2012, 2013, 2014, 2015], frame, start, end)
    assert len(windows) == 4  # the 2015 crop ends after the climate record
    missing_day = last + (date(2012, 11, 15) - date(2011, 11, 15))
    frame = frame[frame["date"] != missing_day.isoformat()]
    windows_after_gap = windows_for_crop(
        crop, [2011, 2012, 2013, 2014, 2015], frame, start, end
    )
    assert len(windows_after_gap) == 3


def test_existing_rotation_keeps_previous_crop_in_its_reported_slot():
    seq = build_existing_sequence("wheat", "winter", "maize", 2)
    assert seq == [
        {"slot": "winter", "year": 1, "crop_id": "wheat"},
        {"slot": "summer", "year": 1, "crop_id": "maize"},
        {"slot": "winter", "year": 2, "crop_id": "wheat"},
        {"slot": "summer", "year": 2, "crop_id": "maize"},
    ]
    unknown_season = build_existing_sequence("wheat", None, "maize", 1)
    assert unknown_season[0]["crop_id"] == "maize"  # next slot defaults to winter
    assert unknown_season[1]["crop_id"] == "wheat"


def test_skipped_priority_weights_sum_to_one_and_are_equal():
    ranked = ["reduce_water_use", "support_soil_health", "improve_climate_resilience"]
    skipped = ["maintain_productivity", "budget_market"]
    weights = build_weights(ranked, skipped)
    assert abs(sum(weights.values()) - 1.0) < 1e-9
    assert weights["maintain_productivity"] == weights["budget_market"]
    assert weights[ranked[0]] > weights[ranked[1]] > weights[ranked[2]]


def test_overall_suppression_and_tie_threshold():
    scores = {"reduce_water_use": 1.0, "support_soil_health": None,
              "improve_climate_resilience": None, "maintain_productivity": None,
              "budget_market": None}
    weights = {"reduce_water_use": .4, "support_soil_health": .2,
               "improve_climate_resilience": .2, "maintain_productivity": .1,
               "budget_market": .1}
    value, basis = overall_number(scores, weights)
    assert value is None and "not enough data" in basis
    assert too_close(.5, .54) and not too_close(.5, .55)
    assert priority_score(["Unknown", "Poor"]) == 0.0
    assert priority_score(["Unknown"]) is None


def _synthetic_daily(start="2011-01-01", end="2021-12-31"):
    dates = pd.date_range(start, end, freq="D")
    return pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"), "t_mean_c": 24.0, "t_max_c": 32.0,
        "t_min_c": 15.0, "rain_mm": 0.0, "solar_mj_m2": 20.0,
    })


def test_phase6_evaluates_existing_and_two_alternatives_with_unknowns():
    crops = load_crop_table("FieldShift_Data/cleaned/crop_reference.yaml")
    rules = load_rules("FieldShift_Data/references/rotation_rules.yaml")
    soil = {"fields": {}}
    existing = [
        {"slot": "winter", "year": 1, "crop_id": "wheat"},
        {"slot": "summer", "year": 1, "crop_id": "maize"},
    ]
    alternatives = [
        {"id": "faba_maize", "kind": "template", "name": "Faba bean to maize",
         "sequence": [{"slot": "winter", "year": 1, "crop_id": "faba_bean"},
                      {"slot": "summer", "year": 1, "crop_id": "maize"}]},
        {"id": "wheat_sorghum", "kind": "template", "name": "Wheat to sorghum",
         "sequence": [{"slot": "winter", "year": 1, "crop_id": "wheat"},
                      {"slot": "summer", "year": 1, "crop_id": "sorghum"}]},
    ]
    result = evaluate_rotation_set(
        _synthetic_daily(), crops, soil, 31.04, existing, alternatives,
        ranked_priorities=["reduce_water_use", "support_soil_health",
                           "improve_climate_resilience", "maintain_productivity"],
        skipped_priorities=["budget_market"], water_availability="limited",
        rules=rules, thresholds=load_thresholds(), bands=load_bands(),
        flags=["coordinates_illustrative"],
    )
    strategies = result["strategies"]
    assert [strategy.id for strategy in strategies] == ["existing", "faba_maize", "wheat_sorghum"]
    assert all(strategy.indicators and strategy.priority_results for strategy in strategies)
    assert all(strategy.confidence in {"high", "moderate", "low"} for strategy in strategies)
    assert all("soil_unknown" in strategy.flags for strategy in strategies)
    faba = strategies[1]
    assert "stage_split_assumed" in faba.flags
    assert "et0_estimated" in faba.flags
    assert faba.confidence == "low"
    assert next(i for i in strategies[0].indicators if i.id == "water_demand_rel").band in {
        "Good", "Moderate", "Poor", "Similar", "Unknown"
    }
    assert result["comparison"]["order"]
    assert "ranking_stable" in result["comparison"]
    assert result["comparison"]["order_equal_weights"]


def test_phase6_requires_existing_plus_two_alternatives():
    with pytest.raises(ValueError, match="at least two"):
        evaluate_rotation_set(
            pd.DataFrame(), {"crops": []}, {}, 31.04, [], [],
        )


def test_missing_crop_temperature_limit_stays_unknown_without_erasing_other_evidence():
    crops = load_crop_table("FieldShift_Data/cleaned/crop_reference.yaml")
    crop_doc = copy.deepcopy(crops.doc)
    wheat = next(crop for crop in crop_doc["crops"] if crop["crop_id"] == "wheat")
    wheat["temperature_c"]["v"]["tmax"] = None
    sequence = [
        {"slot": "winter", "year": 1, "crop_id": "wheat"},
        {"slot": "summer", "year": 1, "crop_id": "maize"},
    ]
    result = evaluate_rotation_set(
        _synthetic_daily(), crop_doc, {"fields": {}}, 31.04, sequence,
        [
            {"id": "alt_one", "kind": "template", "sequence": sequence},
            {"id": "alt_two", "kind": "template", "sequence": sequence},
        ],
        ranked_priorities=["improve_climate_resilience", "reduce_water_use"],
    )
    existing = result["strategies"][0]
    indicators = {indicator.id: indicator for indicator in existing.indicators}
    assert indicators["days_above_tmax"].band == "Unknown"
    assert existing.priority_results["improve_climate_resilience"].band != "Unknown"
    assert "crop_value_missing" in existing.flags
