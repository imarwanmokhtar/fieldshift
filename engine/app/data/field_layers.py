"""Satellite layers for one field, fetched through NASA AppEEARS and stored in Supabase.

Serverless-friendly: AppEEARS requests take minutes, so they are SUBMITTED when the
farmer drops the pin (prefetch) and COLLECTED later (on the next call, or at the
start of an analysis). Only small processed summaries are stored (`field_layers`
table); the analysis never waits on NASA for more than a short time budget.

ACTIVE dataset (product id as listed by AppEEARS):
  smap: SMAP L3 enhanced daily surface soil moisture SPL3SMP_E (9 km, top ~5 cm, AM + PM passes),
  for the last 90 days AND the same 90 days of every year since 2015 (recurring windows), so the
  recent soil moisture can be compared with earlier years at the same time of year.
  Why not SMAP L4 (SPL4SMGP, root zone, 3-hourly)? Its full record is tens of thousands of files
  per point; AppEEARS processes one request per account at a time and these sat for hours (first
  live test). Its percentile layer also came back empty (-9999). The L4 code is kept, inactive.
The processing code for HLS NDVI, MODIS NDVI/ET, ECOSTRESS ET and SRTM elevation is
kept below but switched off (not requested): see INACTIVE_GROUPS to turn one back on.
Missing values are dropped, never filled. One row per FIELD (a user can have several).
"""

from __future__ import annotations

import logging
import time
from datetime import date, datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from .. import db
from . import appeears

log = logging.getLogger(__name__)

HLS_L30_VI, HLS_S30_VI = "HLSL30_VI.020", "HLSS30_VI.020"
HLS_L30, HLS_S30 = "HLSL30.020", "HLSS30.020"
MOD13 = "MOD13Q1.061"
MOD16 = "MOD16A2GF.061"
ECO = "ECO_L3T_JET.002"
SMAP = "SPL4SMGP.008"          # L4 root zone, 3-hourly (inactive: too slow through AppEEARS)
SMAP_L3 = "SPL3SMP_E.006"      # L3 enhanced, daily surface soil moisture (active)
SRTM = "SRTMGL1_NC.003"

W_M2_TO_MM_DAY = 0.0864 / 2.45          # 1 W/m2 of latent heat = 0.0353 mm/day of water
FMASK_BAD_BITS = (1 << 1) | (1 << 2) | (1 << 3)   # cloud, adjacent to cloud, cloud shadow
STEP_DAYS = 10
MAX_INTERP_BINS = 2                      # interpolate gaps of up to 20 days, flag them
PIN_TOLERANCE_DEG = 1e-4                 # ~10 m: same field
REFRESH_AFTER_DAYS = 30
SMAP_START = date(2015, 4, 1)            # SMAP L4 record starts 31 March 2015
SMAP_WINDOW_DAYS = 90
SMAP_MIN_COVERAGE = 0.8                  # L4 (3-hourly, gap-free): a window counts if >= 80% of its days have data
SMAP_MIN_OBS_L3 = 15                     # L3 (satellite passes every 2-3 days): a window counts with >= 15 readings
SMAP_LATENCY_DAYS = 3                    # L3 daily files appear a couple of days after the overpass
SMAP_QUALITY_MIN_OBS = 20                # below this many "recommended quality" readings, use all valid ones (flagged)


def _md(d: date) -> str:
    # Recurring windows use MM-DD; 29 February does not exist in most years, so avoid it.
    if d.month == 2 and d.day == 29:
        d = d.replace(day=28)
    return d.strftime("%m-%d")


def smap_windows(today: date) -> list[dict]:
    """The last SMAP_WINDOW_DAYS days, repeated every year since 2015 (split at New Year if needed)."""
    from datetime import timedelta
    end = today - timedelta(days=SMAP_LATENCY_DAYS)
    start = end - timedelta(days=SMAP_WINDOW_DAYS - 1)
    first, last = SMAP_START.year, end.year
    if start.year == end.year:
        return [appeears.recurring_window(_md(start), _md(end), first, last)]
    return [appeears.recurring_window(_md(start), "12-31", first, last - 1),
            appeears.recurring_window("01-01", _md(end), first + 1, last)]


def _groups(today: date) -> dict[str, dict[str, Any]]:
    """The AppEEARS requests submitted for a field. Only SMAP (daily L3) is active."""
    return {"smap": {"start": SMAP_START, "end": today, "dates": smap_windows(today), "layers": [
        (SMAP_L3, "Soil_Moisture_Retrieval_Data_AM_soil_moisture"),
        (SMAP_L3, "Soil_Moisture_Retrieval_Data_AM_retrieval_qual_flag"),
        (SMAP_L3, "Soil_Moisture_Retrieval_Data_PM_soil_moisture_pm"),
        (SMAP_L3, "Soil_Moisture_Retrieval_Data_PM_retrieval_qual_flag_pm"),
    ]}}


def INACTIVE_GROUPS(today: date) -> dict[str, dict[str, Any]]:
    """Switched-off requests, kept for later (HLS, ECOSTRESS, MODIS, SRTM)."""
    return {
        "recent": {"start": date(today.year - 2, 1, 1), "end": today, "layers": [
            (HLS_L30_VI, "NDVI"), (HLS_L30_VI, "NDWI"), (HLS_L30, "Fmask"),
            (HLS_S30_VI, "NDVI"), (HLS_S30_VI, "NDWI"), (HLS_S30, "Fmask"),
            (ECO, "ETdaily"), (ECO, "cloud"),
            (SMAP, "Geophysical_Data_sm_rootzone"), (SMAP, "Geophysical_Data_sm_rootzone_pctl"),
        ]},
        "history": {"start": date(2015, 1, 1), "end": today, "layers": [
            (MOD13, "_250m_16_days_NDVI"), (MOD13, "_250m_16_days_pixel_reliability"),
            (MOD16, "ET_500m"), (MOD16, "ET_QC_500m"),
        ]},
        "static": {"start": date(2000, 2, 11), "end": date(2000, 2, 21), "layers": [(SRTM, "SRTMGL1_DEM")]},
    }


SOURCES = {
    "hls_ndvi": {"dataset": "NASA HLS (Landsat 8/9 + Sentinel-2) vegetation index", "products": [HLS_L30_VI, HLS_S30_VI], "resolution": "30 m"},
    "modis_ndvi": {"dataset": "NASA MODIS Terra vegetation index", "products": [MOD13], "resolution": "250 m, 16-day"},
    "modis_et": {"dataset": "NASA MODIS Terra evapotranspiration (gap-filled)", "products": [MOD16], "resolution": "500 m, 8-day"},
    "ecostress_et": {"dataset": "NASA ECOSTRESS daily evapotranspiration", "products": [ECO], "resolution": "70 m, irregular overpasses"},
    "smap": {"dataset": "NASA SMAP L3 enhanced daily surface soil moisture (top ~5 cm)", "products": [SMAP_L3],
             "resolution": "9 km, daily (a pass every 2-3 days)"},
    "srtm": {"dataset": "NASA SRTM elevation", "products": [SRTM], "resolution": "30 m"},
}


# ---------------------------------------------------------------- processing (pure)

def _layer(csvs: dict[str, str], product: str, layer: str, **kw) -> pd.Series:
    """Find the layer in whichever CSV of the bundle contains it."""
    for text in csvs.values():
        s = appeears.read_layer(text, product, layer, **kw)
        if len(s):
            return s
    return pd.Series(dtype=float)


def to_10day(s: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Max-value composite per 10-day bin (suppresses leftover cloud), then fill only
    short gaps by linear interpolation. Returns (values, interpolated_flags)."""
    if s.empty:
        return pd.Series(dtype=float), pd.Series(dtype=bool)
    comp = s.resample(f"{STEP_DAYS}D").max()
    missing = comp.isna()
    filled = comp.interpolate(limit=MAX_INTERP_BINS, limit_area="inside")
    interp = missing & filled.notna()
    keep = filled.notna()
    return filled[keep].round(3), interp[keep]


def _series_json(values: pd.Series, interp: pd.Series) -> dict[str, list]:
    return {"dates": [d.strftime("%Y-%m-%d") for d in values.index],
            "values": [float(v) for v in values.to_numpy()],
            "interpolated": [bool(b) for b in interp.reindex(values.index, fill_value=False).to_numpy()]}


def process_hls(csvs: dict[str, str]) -> dict[str, Any]:
    parts = []
    for vi, base in ((HLS_L30_VI, HLS_L30), (HLS_S30_VI, HLS_S30)):
        ndvi = _layer(csvs, vi, "NDVI", fill=-19999, scale=0.0001, valid=(-1.0, 1.0))
        fmask = _layer(csvs, base, "Fmask", fill=255)
        if len(ndvi) and len(fmask):
            bad = fmask.astype(int).groupby(level=0).max().apply(lambda v: bool(v & FMASK_BAD_BITS))
            ndvi = ndvi[~ndvi.index.isin(bad[bad].index)]
        parts.append(ndvi)
    allv = pd.concat(parts).sort_index() if parts else pd.Series(dtype=float)
    if allv.empty:
        return {}
    allv = allv.groupby(level=0).max()
    values, interp = to_10day(allv)
    out: dict[str, Any] = {"ndvi_hls": {**_series_json(values, interp), "n_clear_obs": int(len(allv))}}
    # NDWI > 0 on a vegetated summer field is the classic sign of standing water (flooded rice).
    ndwi = pd.concat([_layer(csvs, p, "NDWI", fill=-19999, scale=0.0001, valid=(-1.0, 1.0))
                      for p in (HLS_L30_VI, HLS_S30_VI)])
    if len(ndwi):
        ndwi = ndwi[ndwi.index.isin(allv.index)]          # clear-sky dates only
        summer = ndwi[ndwi.index.month.isin([6, 7, 8])]
        if len(summer) >= 3:
            out["flooded_summer_share"] = round(float((summer > 0).mean()), 2)
    return out


def process_modis_ndvi(csvs: dict[str, str]) -> dict[str, Any]:
    ndvi = _layer(csvs, MOD13, "_250m_16_days_NDVI", fill=-3000, scale=0.0001, valid=(-1.0, 1.0))
    rel = _layer(csvs, MOD13, "_250m_16_days_pixel_reliability", fill=-1)
    if ndvi.empty:
        return {}
    if len(rel):
        good = rel[rel <= 1].index                        # 0 good, 1 marginal; 2 snow, 3 cloudy
        ndvi = ndvi[ndvi.index.isin(good)]
    recent = ndvi[ndvi.index >= ndvi.index.max() - pd.Timedelta(days=3 * 365)]
    values, interp = to_10day(recent)
    return {"ndvi_modis": _series_json(values, interp)} if len(values) else {}


def process_modis_et(csvs: dict[str, str]) -> dict[str, Any]:
    # kg/m2 per 8 days == mm per 8 days. Codes 32761-32767 (water, urban, barren...) are out of range.
    # Real 8-day totals stay below ~64 mm (8 mm/day), so values above 80 can only be raw
    # integers needing the 0.1 scale. TODO-verify on the first real download whether
    # AppEEARS point CSVs arrive scaled (expected) or raw.
    et = _layer(csvs, MOD16, "ET_500m", fill=32767, scale=0.1, valid=(0.0, 80.0))
    if et.empty:
        return {}
    per_year = et.groupby(et.index.year)
    annual = {int(y): round(float(v.sum()), 0) for y, v in per_year if len(v) >= 44}   # complete years only
    if not annual:
        return {}
    winter = et[et.index.month.isin([11, 12, 1, 2, 3, 4])]
    summer = et[et.index.month.isin([5, 6, 7, 8, 9, 10])]
    years = sorted(annual)
    n = len(years)
    return {"et_modis": {
        "annual_mm": annual, "years": [years[0], years[-1]],
        "mean_annual_mm": round(float(np.mean(list(annual.values()))), 0),
        "mean_winter_mm": round(float(winter[winter.index.year.isin(years)].sum() / n), 0),
        "mean_summer_mm": round(float(summer[summer.index.year.isin(years)].sum() / n), 0),
    }}


def process_ecostress(csvs: dict[str, str]) -> dict[str, Any]:
    et = _layer(csvs, ECO, "ETdaily", valid=(0.0, 1000.0))
    cloud = _layer(csvs, ECO, "cloud", fill=255)
    if et.empty:
        return {}
    if len(cloud):
        et = et[~et.index.isin(cloud[cloud == 1].index)]
    mm = (et * W_M2_TO_MM_DAY).groupby(et.index.normalize()).mean()
    if len(mm) < 5:
        return {}
    by_month = mm.groupby(mm.index.month).median()
    return {"et_ecostress": {
        "n_obs": int(len(mm)), "first": str(mm.index.min().date()), "last": str(mm.index.max().date()),
        "median_mm_day_by_month": {int(k): round(float(v), 2) for k, v in by_month.items()},
        "median_mm_day": round(float(mm.median()), 2),
    }}


def smap_vs_past_years(daily: pd.Series, window_days: int = SMAP_WINDOW_DAYS,
                       min_obs: int | None = None) -> dict[str, Any]:
    """Compare the mean of the last `window_days` with the same calendar window of every
    earlier year that has enough data. Returns counts, never an invented percentile."""
    end = daily.index.max()
    current = daily[daily.index > end - pd.Timedelta(days=window_days)]
    past = []
    for k in range(1, 30):
        e = end - pd.DateOffset(years=k)
        w = daily[(daily.index > e - pd.Timedelta(days=window_days)) & (daily.index <= e)]
        if e < daily.index.min():
            break
        needed = min_obs if min_obs is not None else SMAP_MIN_COVERAGE * window_days
        if len(w) >= needed:
            past.append(float(w.mean()))
    now = float(current.mean())
    out: dict[str, Any] = {"sm_last90_m3m3": round(now, 3), "n_years": len(past)}
    if past:
        out["years_drier_than_now"] = int(sum(v < now for v in past))
        out["anomaly_m3m3"] = round(now - float(np.mean(past)), 3)
    return out


def process_smap(csvs: dict[str, str]) -> dict[str, Any]:
    """SMAP L3 enhanced (daily, surface): AM and PM passes, recommended-quality readings only
    (bit 0 of the retrieval quality flag == 0). Missing days stay missing."""
    readings, valid_all = [], []
    for sm_layer, qf_layer in (("Soil_Moisture_Retrieval_Data_AM_soil_moisture", "Soil_Moisture_Retrieval_Data_AM_retrieval_qual_flag"),
                               ("Soil_Moisture_Retrieval_Data_PM_soil_moisture_pm", "Soil_Moisture_Retrieval_Data_PM_retrieval_qual_flag_pm")):
        sm = _layer(csvs, SMAP_L3, sm_layer, fill=-9999.0, valid=(0.02, 0.5))
        if sm.empty:
            continue
        valid_all.append(sm)
        qf = _layer(csvs, SMAP_L3, qf_layer, fill=65534)
        if len(qf):
            good = qf[(qf.astype(int) & 1) == 0].index
            sm = sm[sm.index.isin(good)]
        readings.append(sm)
    good_sm = pd.concat(readings) if readings else pd.Series(dtype=float)
    relaxed = False
    if len(good_sm) < SMAP_QUALITY_MIN_OBS and valid_all:
        good_sm, relaxed = pd.concat(valid_all), True      # too few top-quality readings: use all valid ones
    if good_sm.empty:
        return {}
    daily = good_sm.groupby(good_sm.index.normalize()).mean().sort_index()
    out: dict[str, Any] = {"product": SMAP_L3, "depth": "0-5 cm", "n_obs": int(len(daily)),
                           "sm_mean_m3m3": round(float(daily.mean()), 3),
                           "first_date": str(daily.index.min().date()), "last_date": str(daily.index.max().date()),
                           "quality_relaxed": relaxed}
    out.update(smap_vs_past_years(daily, min_obs=SMAP_MIN_OBS_L3))
    return {"smap": out}


def process_smap_l4(csvs: dict[str, str]) -> dict[str, Any]:
    """SMAP L4 root zone (3-hourly) processing. Inactive: kept for when L4 is requested again."""
    sm = _layer(csvs, SMAP, "Geophysical_Data_sm_rootzone", fill=-9999.0, valid=(0.0, 1.0))
    pct = _layer(csvs, SMAP, "Geophysical_Data_sm_rootzone_pctl", fill=-9999.0, valid=(0.0, 100.0))
    if sm.empty and pct.empty:
        return {}
    out: dict[str, Any] = {}
    if len(pct):                                   # NASA's own percentile, when AppEEARS returns it
        daily = pct.groupby(pct.index.normalize()).mean()
        last = daily[daily.index > daily.index.max() - pd.Timedelta(days=SMAP_WINDOW_DAYS)]
        out["rootzone_pctl_last90"] = round(float(last.mean()), 0)
    if len(sm):
        daily_sm = sm.groupby(sm.index.normalize()).mean()
        out["rootzone_mean_m3m3"] = round(float(daily_sm.mean()), 3)
        out["first_date"] = str(daily_sm.index.min().date())
        out["last_date"] = str(daily_sm.index.max().date())
        out.update(smap_vs_past_years(daily_sm))
    return {"smap": out}


def process_srtm(csvs: dict[str, str]) -> dict[str, Any]:
    dem = _layer(csvs, SRTM, "SRTMGL1_DEM", fill=-32768, valid=(-500.0, 9000.0))
    return {"elevation_m": round(float(dem.iloc[0]), 0)} if len(dem) else {}


PROCESSORS = {
    "smap": (process_smap,),
    "recent": (process_hls, process_ecostress, process_smap),
    "history": (process_modis_ndvi, process_modis_et),
    "static": (process_srtm,),
}


def process_group(group: str, csvs: dict[str, str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for fn in PROCESSORS[group]:
        try:
            out.update(fn(csvs))
        except Exception:                                   # one bad layer must not drop the others
            log.exception("processing %s failed", fn.__name__)
    return out


def sources_for(features: dict[str, Any], retrieved: str) -> list[dict[str, Any]]:
    present = {"hls_ndvi": "ndvi_hls" in features, "modis_ndvi": "ndvi_modis" in features,
               "modis_et": "et_modis" in features, "ecostress_et": "et_ecostress" in features,
               "smap": "smap" in features, "srtm": "elevation_m" in features}
    return [{"id": k, **SOURCES[k], "retrieved": retrieved, "via": "NASA AppEEARS"} for k, ok in present.items() if ok]


# ---------------------------------------------------------------- submit / collect (network)

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _same_pin(row: dict[str, Any], lat: float, lng: float) -> bool:
    return abs(float(row.get("lat", 999)) - lat) < PIN_TOLERANCE_DEG and abs(float(row.get("lng", 999)) - lng) < PIN_TOLERANCE_DEG


def _stale(row: dict[str, Any]) -> bool:
    try:
        updated = datetime.fromisoformat(str(row.get("updated_at")).replace("Z", "+00:00"))
    except ValueError:
        return True
    return (datetime.now(timezone.utc) - updated).days > REFRESH_AFTER_DAYS


def prefetch(field_id: str, user_id: str, lat: float, lng: float, today: date | None = None,
             force: bool = False) -> dict[str, Any]:
    """Submit the AppEEARS requests for this field's pin, unless they already exist and are fresh
    (`force` resubmits anyway, e.g. after the requested period changed)."""
    if not appeears.configured():
        return {"status": "unavailable"}
    row = db.get_field_layers(field_id)
    if not force and row and _same_pin(row, lat, lng) and row.get("status") in ("submitted", "processing", "partial", "done") \
            and not (row.get("status") == "done" and _stale(row)):
        return row
    tasks, errors = {}, []
    for name, g in _groups(today or date.today()).items():
        try:
            tid = appeears.submit_point_task(f"fieldshift-{name}", lat, lng, g["start"], g["end"], g["layers"],
                                             dates=g.get("dates"))
            tasks[name] = {"task_id": tid, "status": "submitted", "submitted": _now()}
        except Exception as exc:
            log.warning("AppEEARS submit %s failed: %s", name, exc)
            errors.append(f"{name}: {exc}"[:200])
    row = {"field_id": field_id, "user_id": user_id, "lat": lat, "lng": lng, "tasks": tasks, "features": {}, "sources": [],
           "status": "submitted" if tasks else "failed", "error": "; ".join(errors) or None}
    db.upsert_field_layers(row)
    return row


def collect(row: dict[str, Any], budget_s: float = 20.0) -> dict[str, Any]:
    """Check unfinished tasks, download and process the finished ones. Stops at the time budget."""
    started = time.monotonic()
    old_status = row.get("status")
    tasks = dict(row.get("tasks") or {})
    features = dict(row.get("features") or {})
    changed = False
    for name, t in tasks.items():
        if t.get("status") in ("done", "error"):
            continue
        if time.monotonic() - started > budget_s:
            break
        try:
            st = appeears.task_status(t["task_id"])
            if st == "done":
                features.update(process_group(name, appeears.download_csvs(t["task_id"])))
                t = {**t, "status": "done", "collected": _now()}
            elif st == "error":
                t = {**t, "status": "error"}
            else:
                t = {**t, "status": "processing"}
        except Exception as exc:
            log.warning("AppEEARS collect %s failed: %s", name, exc)
            continue
        tasks[name] = t
        changed = True
    states = {t.get("status") for t in tasks.values()}
    if not tasks:
        status = "failed"
    elif states == {"done"}:
        status = "done"
    elif states <= {"done", "error"}:
        status = "partial" if "done" in states else "failed"
    else:
        status = "processing"
    row = {**row, "tasks": tasks, "features": features, "status": status,
           "sources": sources_for(features, _now()[:10]) if features else row.get("sources", [])}
    if changed or status != old_status:
        db.upsert_field_layers({k: row[k] for k in ("field_id", "user_id", "lat", "lng", "tasks", "features", "sources", "status")})
    return row


def for_analysis(field_id: str, user_id: str, lat: float, lng: float,
                 budget_s: float = 20.0) -> tuple[dict[str, Any] | None, str, list]:
    """Features to use now, a state for the data notes, and their sources.

    state: 'ready' | 'partial' | 'processing' | 'requested' | 'unavailable' | 'failed'
    """
    if not appeears.configured():
        return None, "unavailable", []
    try:
        row = db.get_field_layers(field_id)
        if not row or not _same_pin(row, lat, lng):
            row = prefetch(field_id, user_id, lat, lng)
            return None, "requested" if row.get("status") == "submitted" else "failed", []
        if row.get("status") in ("submitted", "processing"):
            row = collect(row, budget_s)
        elif row.get("status") == "done" and _stale(row):
            prefetch(field_id, user_id, lat, lng)           # refresh for next time; use what we have now
        feats = row.get("features") or None
        state = {"done": "ready", "partial": "partial", "failed": "failed"}.get(row.get("status"), "processing")
        if state == "processing" and feats:
            state = "partial"
        return feats, state, row.get("sources") or []
    except Exception as exc:
        log.warning("field layers unavailable: %s", exc)
        return None, "failed", []
