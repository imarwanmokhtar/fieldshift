"""Phase 9 optional satellite context remains quality-screened and outside scoring."""

import pandas as pd

from fieldshift.data.modis import load_modis, summarize_modis, validate_modis
from fieldshift.data.smap import load_smap, summarize_smap, validate_smap
from fieldshift.run_service import _optional_context


def test_smap_quality_filter_and_monthly_summary(tmp_path):
    frame = pd.DataFrame(
        {
            "observation_date": ["2020-01-01", "2020-01-02", "2020-02-01"],
            "soil_moisture": [0.21, 0.8, 0.31],
            "quality_flag": [0, 3, 0],
            "quality_status": ["recommended", "bad", "good"],
            "spatial_resolution_km": [9, 9, 9],
            "product_id": ["SPL3SMP_E"] * 3,
            "product_version": ["6", "6", "6"],
            "retrieved": ["2026-10-31"] * 3,
        }
    )
    path = tmp_path / "smap.csv"
    frame.to_csv(path, index=False)

    assert validate_smap(frame) == (
        [],
        ["some retrievals are not recommended quality and will be excluded"],
    )
    summary = summarize_smap(load_smap(path), "2020-2020")
    assert summary["valid_observations"] == 2
    assert summary["excluded_observations"] == 1
    assert summary["monthly"][0]["median"] == 0.21
    assert summary["spatial_resolution_km"] == 9


def test_modis_applies_scale_factor_and_masks_quality(tmp_path):
    frame = pd.DataFrame(
        {
            "observation_date": ["2020-01-01", "2020-01-17", "2020-02-02"],
            "ndvi": [5000, 6000, -3000],
            "evi": [3000, 4000, -3000],
            "pixel_quality": [0, 1, 0],
            "product_id": ["MOD13Q1.061"] * 3,
            "product_version": ["061"] * 3,
            "scale_factor": [0.0001] * 3,
            "retrieved": ["2026-10-31"] * 3,
        }
    )
    path = tmp_path / "modis.csv"
    frame.to_csv(path, index=False)

    errors, warnings = validate_modis(frame)
    assert errors == []
    assert "marginal, snow/ice, or cloudy pixels will be excluded" in warnings
    summary = summarize_modis(load_modis(path), "2020-2020")
    assert summary["valid_observations"] == 1
    assert summary["excluded_observations"] == 2
    assert summary["monthly"][0]["ndvi_median"] == 0.5
    assert summary["monthly"][0]["evi_median"] == 0.3
    assert summary["scale_factor"] == 0.0001


def test_run_context_panels_load_optional_files_without_scoring(tmp_path):
    cleaned = tmp_path / "cleaned"
    cleaned.mkdir()
    smap = pd.DataFrame(
        {
            "observation_date": ["2020-01-01"],
            "soil_moisture": [0.24],
            "quality_flag": [0],
            "quality_status": ["recommended"],
            "product_id": ["SPL3SMP_E"],
            "spatial_resolution_km": [9],
            "product_version": ["6"],
            "retrieved": ["2026-10-31"],
        }
    )
    modis = pd.DataFrame(
        {
            "observation_date": ["2020-01-01"],
            "ndvi": [5300],
            "evi": [3200],
            "pixel_quality": [0],
            "product_id": ["MOD13Q1.061"],
            "product_version": ["061"],
            "scale_factor": [0.0001],
            "retrieved": ["2026-10-31"],
        }
    )
    smap.to_csv(cleaned / "smap_daily_31.04_31.38.csv", index=False)
    modis.to_csv(cleaned / "modis_mod13q1_31.04_31.38.csv", index=False)

    panels, sources, flags = _optional_context(tmp_path, "31.04_31.38", "2020-2025")
    assert panels["smap"]["status"] == "available"
    assert panels["modis"]["status"] == "available"
    assert panels["modis"]["monthly"][0]["ndvi_median"] == 0.53
    assert {source["status"] for source in sources} == {"extracted"}
    assert flags == []


def test_missing_optional_files_are_reported_without_blocking_core(tmp_path):
    panels, sources, flags = _optional_context(tmp_path, "31.04_31.38", "2020-2025")
    assert panels["smap"]["status"] == "not_provided"
    assert panels["modis"]["status"] == "not_provided"
    assert {source["status"] for source in sources} == {"missing"}
    assert flags == []
