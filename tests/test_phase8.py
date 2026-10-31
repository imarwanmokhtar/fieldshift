"""Unit and integration tests for Phase 8 extensions."""

import json
import shutil
from pathlib import Path

import pandas as pd
from typer.testing import CliRunner

from fieldshift.analysis.proposed import (
    enumerate_candidate_sequences,
    propose_candidate_strategies,
)
from fieldshift.analysis.sensitivity import (
    priority_sensitivity,
    sowing_date_sensitivity,
)
from fieldshift.cli import app
from fieldshift.data.crops import load_crop_table

runner = CliRunner()
BANNED = (
    "will increase yield",
    "guaranteed",
    "best rotation",
    "optimal rotation",
    "optimal strategy",
    "you should irrigate",
    "proven",
)


def _load_data_fixtures():
    crop_path = Path("FieldShift_Data/cleaned/crop_reference.yaml")
    crop_table = load_crop_table(crop_path)
    climate_path = Path("FieldShift_Data/cleaned/climate_daily_31.04_31.38.csv")
    climate = pd.read_csv(climate_path)
    soil = {"schema_version": 1, "location_id": "31.04_31.38", "fields": {}}
    return crop_table, climate, soil


def test_enumerate_candidate_sequences_enforces_no_consecutive_same_type():
    crop_table, _, _ = _load_data_fixtures()
    existing = [
        {"slot": "winter", "year": 1, "crop_id": "wheat"},
        {"slot": "summer", "year": 1, "crop_id": "maize"},
        {"slot": "winter", "year": 2, "crop_id": "wheat"},
        {"slot": "summer", "year": 2, "crop_id": "maize"},
    ]
    candidates = enumerate_candidate_sequences(
        crop_table, horizon=2, first_slot="winter", existing_sequence=existing
    )
    assert len(candidates) > 0
    for seq in candidates:
        assert len(seq) == 4
        # check consecutive winter slots have different crops
        assert seq[0]["crop_id"] != seq[2]["crop_id"]
        # check consecutive summer slots have different crops
        assert seq[1]["crop_id"] != seq[3]["crop_id"]
        # check not identical to existing
        crop_tuple = tuple(s["crop_id"] for s in seq)
        assert crop_tuple != ("wheat", "maize", "wheat", "maize")


def test_propose_candidate_strategies_returns_top_candidates():
    crop_table, climate, soil = _load_data_fixtures()
    existing = [
        {"slot": "winter", "year": 1, "crop_id": "wheat"},
        {"slot": "summer", "year": 1, "crop_id": "maize"},
    ]
    alternatives = propose_candidate_strategies(
        crop_table=crop_table,
        existing_sequence=existing,
        horizon=1,
        daily_climate=climate,
        soil_record=soil,
        latitude=31.04,
        ranked_priorities=["reduce_water_use", "support_soil_health"],
        max_candidates=3,
    )
    assert 2 <= len(alternatives) <= 3
    for alt in alternatives:
        assert alt["kind"] == "proposed"
        assert alt["id"].startswith("proposed-")
        assert "Candidate" in alt["name"]
        # Make sure no candidate is "best" or "optimal"
        assert "best" not in alt["name"].lower()
        assert "optimal" not in alt["name"].lower()


def test_sowing_date_sensitivity_computes_spread():
    crop_table, climate, _ = _load_data_fixtures()
    crops = {c["crop_id"]: c for c in crop_table.doc.get("crops", [])}
    wheat = crops["wheat"]
    thresholds = {"hot_day_tmax_c": 35, "cold_day_tmin_c": 5, "frost_day_tmin_c": 0}
    stage_splits = {"ini": 0.15, "dev": 0.25, "mid": 0.40, "late": 0.20}

    sens = sowing_date_sensitivity(climate, wheat, 31.04, thresholds, stage_splits)
    assert sens is not None
    assert sens["crop_id"] == "wheat"
    assert "indicators" in sens
    etc_data = sens["indicators"]["etc_window_mm"]
    assert etc_data["mid"] is not None
    assert etc_data["spread"] is not None
    assert etc_data["spread"] >= 0
    assert "dataset" in sens and "period" in sens
    assert set(sens["windows"]) == {"start", "mid", "end"}


def test_sowing_sensitivity_skips_placeholder_crop_duration():
    crop_table, climate, _ = _load_data_fixtures()
    crops = {c["crop_id"]: c for c in crop_table.doc.get("crops", [])}
    berseem = crops["berseem"]
    thresholds = {"hot_day_tmax_c": 35, "cold_day_tmin_c": 5, "frost_day_tmin_c": 0}
    stage_splits = {"ini": 0.15, "dev": 0.25, "mid": 0.40, "late": 0.20}

    assert sowing_date_sensitivity(climate, berseem, 31.04, thresholds, stage_splits) is None


def test_priority_sensitivity_fixed_seed_is_deterministic():
    prepared = [
        {
            "id": "strat_a",
            "overall_value": 0.80,
            "priority_scores": {
                "reduce_water_use": 0.9,
                "support_soil_health": 0.7,
                "improve_climate_resilience": 0.8,
            },
        },
        {
            "id": "strat_b",
            "overall_value": 0.50,
            "priority_scores": {
                "reduce_water_use": 0.4,
                "support_soil_health": 0.5,
                "improve_climate_resilience": 0.6,
            },
        },
        {
            "id": "strat_c",
            "overall_value": 0.30,
            "priority_scores": {
                "reduce_water_use": 0.2,
                "support_soil_health": 0.3,
                "improve_climate_resilience": 0.4,
            },
        },
    ]
    base_weights = {
        "reduce_water_use": 0.6,
        "support_soil_health": 0.3,
        "improve_climate_resilience": 0.1,
    }

    res1 = priority_sensitivity(prepared, base_weights, seed=42, n_trials=50)
    res2 = priority_sensitivity(prepared, base_weights, seed=42, n_trials=50)
    assert res1 == res2
    assert res1["trials"] == 50
    assert res1["order_stable_pct"] == 100.0
    assert res1["top_stable_pct"] == 100.0
    assert res1["is_stable"] is True
    assert "Ranking order preserved" in res1["summary"]


def test_end_to_end_proposed_run(tmp_path):
    target = tmp_path / "FieldShift_Data"
    shutil.copytree(Path("FieldShift_Data"), target)
    profile = tmp_path / "profile.json"
    profile.write_text(
        json.dumps(
            {
                "answers": {
                    "loc_mode": "pilot",
                    "coords_real": False,
                    "prev_crop": "wheat",
                    "prev_season": "winter",
                    "existing_edit": True,
                    "existing_other_crop": "maize",
                    "irrigation": "canal",
                    "water_avail": "moderate",
                    "horizon": 1,
                    "period": "2020-2025",
                    "strat_source": "proposed",
                    "prio_rank_list": ["reduce_water_use", "support_soil_health"],
                },
                "flags": [],
                "chosen_priorities": ["reduce_water_use", "support_soil_health"],
            }
        ),
        encoding="utf-8",
    )
    result = runner.invoke(
        app, ["--data-dir", str(target), "run", "--profile", str(profile), "--offline"]
    )
    assert result.exit_code == 0, result.output
    output = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    report = (tmp_path / "report.md").read_text(encoding="utf-8").lower()

    assert output["schema_version"] == 1
    # 1 existing + 3 proposed alternatives = 4 strategies
    assert len(output["strategies"]) >= 3
    proposed_strategies = [s for s in output["strategies"] if s["kind"] == "proposed"]
    assert len(proposed_strategies) >= 2
    for s in proposed_strategies:
        assert any("candidate to explore" in item.lower() for item in s["why_suggested"])
        assert "sowing_sensitivity" in s
        assert len(s["sowing_sensitivity"]) > 0

    assert "priority_sensitivity" in output["comparison"]
    assert output["comparison"]["priority_sensitivity"] is not None

    # Verify report sections and banned words
    assert "priority sensitivity" in report
    assert "sowing-date sensitivity" in report
    assert not any(phrase in report for phrase in BANNED)
