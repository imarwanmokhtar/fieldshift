"""Tests for the NASA AppEEARS satellite layers. All offline.

The CSV fixtures are SYNTHETIC: they follow the documented AppEEARS point-CSV layout
(columns '<PRODUCT>_<VERSION>_<LAYER>' plus 'Date'), but the values are made up and
never reach the demo path.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from app.data import appeears, field_layers as fl


def synthetic_csv(product: str, layers: dict[str, list], dates: list[str]) -> str:
    prefix = product.replace(".", "_")
    df = pd.DataFrame({"ID": "field", "Category": "field", "Latitude": 31.04, "Longitude": 31.38, "Date": dates})
    for layer, values in layers.items():
        df[f"{prefix}_{layer}"] = values
    return df.to_csv(index=False)


def _days(start: str, n: int, step: int) -> list[str]:
    return [d.strftime("%Y-%m-%d") for d in pd.date_range(start, periods=n, freq=f"{step}D")]


# ---------------------------------------------------------------- CSV reading

def test_read_layer_finds_column_drops_fill_and_scales_raw_values():
    csv = synthetic_csv("MOD13Q1.061", {"_250m_16_days_NDVI": [5000, -3000, 7000]}, _days("2024-01-01", 3, 16))
    s = appeears.read_layer(csv, "MOD13Q1.061", "_250m_16_days_NDVI", fill=-3000, scale=0.0001, valid=(-1, 1))
    assert list(s.round(2)) == [0.5, 0.7]                      # raw integers scaled, fill dropped


def test_read_layer_keeps_already_scaled_values():
    csv = synthetic_csv("HLSL30_VI.020", {"NDVI": [0.42, 0.61]}, _days("2024-01-01", 2, 8))
    s = appeears.read_layer(csv, "HLSL30_VI.020", "NDVI", fill=-19999, scale=0.0001, valid=(-1, 1))
    assert list(s) == [0.42, 0.61]


def test_read_layer_missing_column_is_empty():
    csv = synthetic_csv("HLSL30_VI.020", {"NDVI": [0.4]}, ["2024-01-01"])
    assert appeears.read_layer(csv, "HLSL30.020", "Fmask").empty


# ---------------------------------------------------------------- processing

def test_hls_cloud_mask_removes_cloudy_dates_and_composites_to_10_days():
    dates = _days("2024-01-01", 40, 5)
    ndvi = [0.6] * 40
    fmask = [0] * 40
    for i in (3, 9, 15):                                      # cloudy scenes read as near-bare
        ndvi[i], fmask[i] = 0.05, 1 << 1
    csvs = {"l30_vi": synthetic_csv("HLSL30_VI.020", {"NDVI": ndvi, "NDWI": [-0.3] * 40}, dates),
            "l30": synthetic_csv("HLSL30.020", {"Fmask": fmask}, dates)}
    out = fl.process_hls(csvs)
    vals = out["ndvi_hls"]["values"]
    assert min(vals) >= 0.6                                   # no fake bare spots from clouds
    steps = np.diff(pd.to_datetime(out["ndvi_hls"]["dates"])).astype("timedelta64[D]").astype(int)
    assert set(steps) == {10}
    assert out["ndvi_hls"]["n_clear_obs"] == 37


def test_hls_flooded_summer_share_from_ndwi():
    dates = _days("2024-06-01", 12, 7)                        # June-August
    csvs = {"vi": synthetic_csv("HLSS30_VI.020", {"NDVI": [0.5] * 12, "NDWI": [0.2] * 9 + [-0.2] * 3}, dates)}
    assert fl.process_hls(csvs)["flooded_summer_share"] == 0.75


def test_modis_et_annual_totals_complete_years_only():
    dates = _days("2020-01-01", 46 + 20, 8)                   # 2020 complete (46), 2021 partial
    raw = [250] * len(dates)                                  # raw integer 250 = 25.0 mm per 8 days
    csvs = {"et": synthetic_csv("MOD16A2GF.061", {"ET_500m": raw, "ET_QC_500m": [0] * len(dates)}, dates)}
    out = fl.process_modis_et(csvs)["et_modis"]
    assert list(out["annual_mm"]) == [2020]
    assert out["mean_annual_mm"] == 1150.0                    # 46 composites * 25 mm
    scaled = [25.0] * len(dates)                              # same data, already scaled by AppEEARS
    csvs = {"et": synthetic_csv("MOD16A2GF.061", {"ET_500m": scaled, "ET_QC_500m": [0] * len(dates)}, dates)}
    assert fl.process_modis_et(csvs)["et_modis"]["mean_annual_mm"] == 1150.0


def test_ecostress_watts_to_mm_and_cloud_removed():
    dates = _days("2024-03-01", 8, 4)
    csvs = {"eco": synthetic_csv("ECO_L3T_JET.002", {"ETdaily": [100.0] * 7 + [900.0], "cloud": [0] * 7 + [1]}, dates)}
    out = fl.process_ecostress(csvs)["et_ecostress"]
    assert out["n_obs"] == 7
    assert out["median_mm_day"] == pytest.approx(3.53, abs=0.01)   # 100 W/m2 = 3.53 mm/day


def test_smap_recent_percentile_and_srtm_elevation():
    dates = _days("2024-01-01", 200, 1)
    pctl = [50.0] * 100 + [10.0] * 100
    csvs = {"smap": synthetic_csv("SPL4SMGP.008", {"Geophysical_Data_sm_rootzone": [0.3] * 200,
                                                   "Geophysical_Data_sm_rootzone_pctl": pctl}, dates),
            "dem": synthetic_csv("SRTMGL1_NC.003", {"SRTMGL1_DEM": [6]}, ["2000-02-11"])}
    smap = fl.process_smap(csvs)["smap"]
    assert smap["rootzone_pctl_last90"] == 10.0
    assert smap["rootzone_mean_m3m3"] == 0.3
    assert fl.process_srtm(csvs) == {"elevation_m": 6.0}


def test_one_bad_layer_does_not_drop_the_others():
    csvs = {"dem": synthetic_csv("SRTMGL1_NC.003", {"SRTMGL1_DEM": [6]}, ["2000-02-11"]), "junk": "not,a\ncsv"}
    assert fl.process_group("static", csvs) == {"elevation_m": 6.0}


# ---------------------------------------------------------------- submit / collect

@pytest.fixture
def fake_db(monkeypatch):
    store: dict = {}
    monkeypatch.setattr(fl.db, "get_field_layers", lambda uid: store.get(uid))
    monkeypatch.setattr(fl.db, "upsert_field_layers", lambda row: store.__setitem__(row["user_id"], {**store.get(row["user_id"], {}), **row}))
    monkeypatch.setattr(fl.appeears, "configured", lambda: True)
    return store


def test_prefetch_submits_three_groups_once(fake_db, monkeypatch):
    calls = []
    monkeypatch.setattr(fl.appeears, "submit_point_task",
                        lambda name, lat, lng, start, end, layers: calls.append((name, start, end, layers)) or f"t-{name}")
    row = fl.prefetch("u1", 31.04, 31.38, today=date(2026, 11, 14))
    assert row["status"] == "submitted" and set(row["tasks"]) == {"recent", "history", "static"}
    by = {c[0]: c for c in calls}
    assert by["fieldshift-recent"][1] == date(2024, 1, 1)
    assert ("HLSL30.020", "Fmask") in by["fieldshift-recent"][3]
    assert by["fieldshift-history"][1] == date(2015, 1, 1)
    fl.prefetch("u1", 31.04, 31.38)                          # same pin: no new requests
    assert len(calls) == 3


def test_collect_processes_finished_tasks_and_keeps_waiting_on_others(fake_db, monkeypatch):
    fake_db["u1"] = {"user_id": "u1", "lat": 31.04, "lng": 31.38, "status": "submitted", "features": {},
                     "tasks": {"static": {"task_id": "s", "status": "submitted"},
                               "recent": {"task_id": "r", "status": "submitted"}}}
    monkeypatch.setattr(fl.appeears, "task_status", lambda tid: "done" if tid == "s" else "processing")
    monkeypatch.setattr(fl.appeears, "download_csvs",
                        lambda tid: {"dem.csv": synthetic_csv("SRTMGL1_NC.003", {"SRTMGL1_DEM": [6]}, ["2000-02-11"])})
    feats, state, sources = fl.for_analysis("u1", 31.04, 31.38)
    assert feats == {"elevation_m": 6.0} and state == "partial"
    assert [s["id"] for s in sources] == ["srtm"]
    assert fake_db["u1"]["tasks"]["recent"]["status"] == "processing"


def test_for_analysis_without_login_is_unavailable(monkeypatch):
    monkeypatch.setattr(fl.appeears, "configured", lambda: False)
    assert fl.for_analysis("u1", 31.0, 31.0) == (None, "unavailable", [])


def test_new_pin_requests_layers(fake_db, monkeypatch):
    fake_db["u1"] = {"user_id": "u1", "lat": 30.0, "lng": 30.0, "status": "done", "features": {"elevation_m": 1}}
    monkeypatch.setattr(fl.appeears, "submit_point_task", lambda *a: "t")
    feats, state, _ = fl.for_analysis("u1", 31.04, 31.38)
    assert feats is None and state == "requested"


def test_expired_token_logs_in_again(monkeypatch):
    import httpx
    logins = []
    monkeypatch.setattr(appeears, "_login", lambda: logins.append(1) or f"tok{len(logins)}")
    monkeypatch.setattr(appeears.cache, "get", lambda *a, **k: None)
    monkeypatch.setattr(appeears.cache, "put", lambda *a, **k: None)
    appeears._token.clear()
    seen = []

    def fake_request(method, url, headers, timeout, **kw):
        seen.append(headers["Authorization"])
        code = 403 if len(seen) == 1 else 200
        return httpx.Response(code, json={"status": "done"}, request=httpx.Request(method, url))
    monkeypatch.setattr(httpx, "request", fake_request)
    assert appeears.task_status("x") == "done"
    assert seen == ["Bearer tok1", "Bearer tok2"]


# ---------------------------------------------------------------- full analysis

def _layers_features():
    dates = pd.date_range("2023-11-01", periods=100, freq="10D")
    ndvi = (0.45 + 0.3 * np.sin(np.arange(100) / 6)).round(3)
    return {"ndvi_hls": {"dates": [d.strftime("%Y-%m-%d") for d in dates], "values": [float(v) for v in ndvi],
                         "interpolated": [False] * 100},
            "et_modis": {"annual_mm": {2023: 900}, "years": [2016, 2024], "mean_annual_mm": 900,
                         "mean_winter_mm": 400, "mean_summer_mm": 500},
            "smap": {"rootzone_pctl_last90": 12, "rootzone_mean_m3m3": 0.31},
            "elevation_m": 7}


def test_analysis_uses_satellite_layers():
    from tests.test_engine import ANSWERS
    from app.pipeline import analyze_answers
    pack, _ = analyze_answers(ANSWERS, "en", layers=(_layers_features(), "ready", [{"id": "hls_ndvi"}]))
    used = pack.data_quality.layers_used
    assert {"hls_ndvi", "modis_et", "smap", "srtm"} <= set(used)
    codes = [n.code for n in pack.data_quality.notes]
    assert "smap_dry" in codes and "elevation" in codes
    cur = next(s for s in pack.strategies if s.kind == "current")
    assert any(f.code == "et_check_modis" for f in cur.evidence)
    assert pack.observations["satellite"]["et_check"]["modis_mm_per_year"] == 900
    assert pack.observations["satellite"]["elevation_m"] == 7


def test_analysis_notes_pending_layers():
    from tests.test_engine import ANSWERS
    from app.pipeline import analyze_answers
    pack, _ = analyze_answers(ANSWERS, "en", layers=(None, "requested", []))
    cur = next(s for s in pack.strategies if s.kind == "current")
    assert any(g.code == "layers_pending" for g in cur.gaps)
