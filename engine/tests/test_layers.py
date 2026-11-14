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
    smap = fl.process_smap_l4(csvs)["smap"]                    # inactive L4 processor stays tested
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
    monkeypatch.setattr(fl.db, "get_field_layers", lambda fid: store.get(fid))
    monkeypatch.setattr(fl.db, "upsert_field_layers", lambda row: store.__setitem__(row["field_id"], {**store.get(row["field_id"], {}), **row}))
    monkeypatch.setattr(fl.appeears, "configured", lambda: True)
    return store


def test_prefetch_submits_only_smap_once_per_field(fake_db, monkeypatch):
    calls = []
    monkeypatch.setattr(fl.appeears, "submit_point_task",
                        lambda name, lat, lng, start, end, layers, dates=None: calls.append((name, start, end, layers, dates)) or f"t-{name}")
    row = fl.prefetch("f1", "u1", 31.04, 31.38, today=date(2026, 11, 14))
    assert row["status"] == "submitted" and set(row["tasks"]) == {"smap"}
    assert row["field_id"] == "f1" and row["user_id"] == "u1"
    name, start, _, layers, dates = calls[0]
    assert name == "fieldshift-smap"
    assert {p for p, _ in layers} == {fl.SMAP_L3}               # daily SMAP only; every other dataset is off
    # last 90 days (ending 3 days ago for data latency), repeated every year since 2015
    assert dates == [{"startDate": "08-14", "endDate": "11-11", "recurring": True, "yearRange": [2015, 2026]}]
    fl.prefetch("f1", "u1", 31.04, 31.38)                       # same field and pin: no new request
    assert len(calls) == 1
    fl.prefetch("f2", "u1", 30.5, 31.0)                         # a second field gets its own request
    assert len(calls) == 2 and set(fake_db) == {"f1", "f2"}


def test_collect_processes_finished_tasks_and_keeps_waiting_on_others(fake_db, monkeypatch):
    fake_db["f1"] = {"field_id": "f1", "user_id": "u1", "lat": 31.04, "lng": 31.38, "status": "submitted", "features": {},
                     "tasks": {"smap": {"task_id": "s", "status": "submitted"},
                               "static": {"task_id": "x", "status": "submitted"}}}
    dates = _days("2024-01-01", 120, 1)
    smap_csv = synthetic_csv("SPL3SMP_E.006", {"Soil_Moisture_Retrieval_Data_AM_soil_moisture": [0.3] * 120,
                                               "Soil_Moisture_Retrieval_Data_AM_retrieval_qual_flag": [0] * 120}, dates)
    monkeypatch.setattr(fl.appeears, "task_status", lambda tid: "done" if tid == "s" else "processing")
    monkeypatch.setattr(fl.appeears, "download_csvs", lambda tid: {"smap.csv": smap_csv})
    feats, state, sources = fl.for_analysis("f1", "u1", 31.04, 31.38)
    assert feats["smap"]["sm_mean_m3m3"] == 0.3 and feats["smap"]["n_obs"] == 120 and state == "partial"
    assert [s["id"] for s in sources] == ["smap"]
    assert fake_db["f1"]["tasks"]["static"]["status"] == "processing"


def test_for_analysis_without_login_is_unavailable(monkeypatch):
    monkeypatch.setattr(fl.appeears, "configured", lambda: False)
    assert fl.for_analysis("f1", "u1", 31.0, 31.0) == (None, "unavailable", [])


def test_new_pin_requests_layers(fake_db, monkeypatch):
    fake_db["f1"] = {"field_id": "f1", "user_id": "u1", "lat": 30.0, "lng": 30.0, "status": "done", "features": {"smap": {}}}
    monkeypatch.setattr(fl.appeears, "submit_point_task", lambda *a, **k: "t")
    feats, state, _ = fl.for_analysis("f1", "u1", 31.04, 31.38)
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
    # Includes switched-off layers on purpose: the analysis must ignore everything but SMAP.
    return {"smap": {"rootzone_pctl_last90": 12, "rootzone_mean_m3m3": 0.31},
            "et_modis": {"annual_mm": {2023: 900}, "years": [2016, 2024], "mean_annual_mm": 900},
            "elevation_m": 7}


def test_analysis_uses_only_power_and_smap():
    from tests.test_engine import ANSWERS
    from app.pipeline import analyze_answers
    pack, _ = analyze_answers(ANSWERS, "en", layers=(_layers_features(), "ready", [{"id": "smap"}]))
    assert pack.data_quality.layers_used == ["nasa_power", "smap"]
    assert pack.data_quality.layers_unavailable == []
    codes = [n.code for n in pack.data_quality.notes]
    assert "smap_dry" in codes
    cur = next(s for s in pack.strategies if s.kind == "current")
    assert all(g.code != "ndvi_unavailable" for g in cur.gaps)


def test_analysis_without_smap_lists_it_unavailable():
    from tests.test_engine import ANSWERS
    from app.pipeline import analyze_answers
    pack, _ = analyze_answers(ANSWERS, "en", layers=(None, "unavailable", []))
    assert pack.data_quality.layers_used == ["nasa_power"]
    assert pack.data_quality.layers_unavailable == ["smap"]


def test_analysis_notes_pending_layers():
    from tests.test_engine import ANSWERS
    from app.pipeline import analyze_answers
    pack, _ = analyze_answers(ANSWERS, "en", layers=(None, "requested", []))
    cur = next(s for s in pack.strategies if s.kind == "current")
    assert any(g.code == "layers_pending" for g in cur.gaps)


def test_smap_compares_last_90_days_with_past_years_when_percentile_is_empty():
    # Like the first live AppEEARS download: the percentile layer is all -9999.
    idx = pd.date_range("2015-04-01", "2025-11-10", freq="D")
    sm = np.where(idx >= pd.Timestamp("2025-08-13"), 0.10, 0.20)   # last 90 days much drier
    csv = synthetic_csv("SPL4SMGP.008", {"Geophysical_Data_sm_rootzone": sm,
                                         "Geophysical_Data_sm_rootzone_pctl": [-9999.0] * len(idx)},
                        [d.strftime("%Y-%m-%d") for d in idx])
    smap = fl.process_smap_l4({"s": csv})["smap"]
    assert "rootzone_pctl_last90" not in smap
    assert smap["n_years"] == 10 and smap["years_drier_than_now"] == 0
    assert smap["anomaly_m3m3"] == -0.1


def test_smap_years_fact_in_analysis():
    from tests.test_engine import ANSWERS
    from app.pipeline import analyze_answers
    feats = {"smap": {"rootzone_mean_m3m3": 0.2, "n_years": 10, "years_drier_than_now": 0, "anomaly_m3m3": -0.1}}
    pack, _ = analyze_answers(ANSWERS, "en", layers=(feats, "ready", []))
    note = next(n for n in pack.data_quality.notes if n.code == "smap_dry_years")
    assert "10 of the last 10 years" in note.text


def test_offline_uses_saved_real_power_copy(monkeypatch, tmp_path):
    """No internet + a saved NASA POWER file for the pin's grid cell -> real data, flagged as offline copy."""
    import gzip
    import json as _json
    from app.data import power
    days = pd.date_range("2020-01-01", "2021-12-31", freq="D")
    raw = {c: {d.strftime("%Y%m%d"): 20.0 for d in days} for c in power.COLUMNS}
    (tmp_path / "power").mkdir()
    import shutil
    shutil.copy(power.settings.DATA_DIR / "fallback_climatology_dakahlia.json", tmp_path)
    # pin 31.40, 30.96 lies in the cell centred on 31.5, 31.25 (0.5 x 0.625 deg grid)
    (tmp_path / "power" / "cell_31.500_31.250.json.gz").write_bytes(gzip.compress(_json.dumps(
        {"meta": {"retrieved": "2026-11-14"}, "parameter": raw}).encode()))
    monkeypatch.setattr(power, "settings", type("S", (), {"DATA_DIR": tmp_path, "POWER_START": "20200101",
                                                          "POWER_END": "20211231"})())

    def no_internet(*a, **k):
        raise OSError("no internet")
    monkeypatch.setattr(power, "fetch_power", no_internet)
    c = power.load_climate(31.40, 30.96)
    assert c.source == "nasa_power" and c.offline_copy == "2026-11-14" and len(c.df) == len(days)
    c2 = power.load_climate(25.0, 33.0)                          # outside the saved cells
    assert c2.source == "fallback_climatology" and c2.offline_copy is None



def _l3_csv(idx, am, am_qf, pm=None, pm_qf=None):
    layers = {"Soil_Moisture_Retrieval_Data_AM_soil_moisture": am, "Soil_Moisture_Retrieval_Data_AM_retrieval_qual_flag": am_qf}
    if pm is not None:
        layers.update({"Soil_Moisture_Retrieval_Data_PM_soil_moisture_pm": pm,
                       "Soil_Moisture_Retrieval_Data_PM_retrieval_qual_flag_pm": pm_qf})
    return synthetic_csv("SPL3SMP_E.006", layers, [d.strftime("%Y-%m-%d") for d in idx])


def test_smap_l3_keeps_recommended_quality_and_merges_am_pm():
    idx = pd.date_range("2025-01-01", periods=40, freq="D")
    am = [0.30] * 40
    am_qf = [0] * 20 + [1] * 20                      # bit 0 set = not recommended quality
    pm = [0.10] * 40
    pm_qf = [0] * 40
    smap = fl.process_smap({"s": _l3_csv(idx, am, am_qf, pm, pm_qf)})["smap"]
    assert smap["product"] == "SPL3SMP_E.006" and smap["depth"] == "0-5 cm"
    assert smap["n_obs"] == 40 and not smap["quality_relaxed"]
    # days 1-20: mean of AM 0.30 and PM 0.10; days 21-40: PM only (AM failed quality)
    assert smap["sm_mean_m3m3"] == round((20 * 0.20 + 20 * 0.10) / 40, 3)


def test_smap_l3_sparse_passes_compared_with_past_years():
    # The 90-day window of each year 2015-2025 only (like the recurring request), a pass every 3 days.
    days = []
    for y in range(2015, 2026):
        days += list(pd.date_range(f"{y}-08-14", f"{y}-11-11", freq="3D"))
    idx = pd.DatetimeIndex(days)
    sm = [0.12 if d.year == 2025 else 0.25 for d in idx]   # this year much drier
    smap = fl.process_smap({"s": _l3_csv(idx, sm, [0] * len(idx))})["smap"]
    assert smap["n_years"] == 10 and smap["years_drier_than_now"] == 0
    assert smap["anomaly_m3m3"] == -0.13


def test_smap_l3_relaxes_quality_only_when_too_few_good_readings():
    idx = pd.date_range("2025-01-01", periods=30, freq="D")
    smap = fl.process_smap({"s": _l3_csv(idx, [0.2] * 30, [1] * 30)})["smap"]   # none recommended
    assert smap["quality_relaxed"] and smap["n_obs"] == 30


def test_smap_windows_split_at_new_year():
    w = fl.smap_windows(date(2027, 1, 20))                   # window 21 Oct 2026 -> 17 Jan 2027
    assert w == [{"startDate": "10-20", "endDate": "12-31", "recurring": True, "yearRange": [2015, 2026]},
                 {"startDate": "01-01", "endDate": "01-17", "recurring": True, "yearRange": [2016, 2027]}]
