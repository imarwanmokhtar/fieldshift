"""Climate, water and NDVI features.

All maths is deterministic and documented so every number in the evidence pack
can be traced back to a formula and an input.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from .data.ndvi import NdviSeries
from .schemas import FEDDAN_HA, CropMetrics

CROPS: dict = {k: v for k, v in json.loads((Path(__file__).parent / "crops.json").read_text(encoding="utf-8")).items() if k != "_meta"}

HOT_DAY_C = 35.0
ELEVATION_M = 10.0          # Nile Delta is close to sea level
EFFECTIVE_RAIN_FRACTION = 0.7

# Share of applied water that reaches the crop's roots (field application efficiency).
IRRIGATION_EFFICIENCY = {
    "flood": 0.65, "furrow": 0.70, "sprinkler": 0.75, "drip": 0.90, "pivot": 0.80, "other": 0.60,
}
DEFAULT_EFFICIENCY = 0.65


# ---------------------------------------------------------------- ET0

def _sat_vp(t: np.ndarray) -> np.ndarray:
    return 0.6108 * np.exp(17.27 * t / (t + 237.3))


def extraterrestrial_radiation(lat_deg: float, doy: np.ndarray) -> np.ndarray:
    """Ra in MJ/m2/day (FAO-56 eq. 21)."""
    phi = math.radians(lat_deg)
    dr = 1 + 0.033 * np.cos(2 * np.pi * doy / 365)
    delta = 0.409 * np.sin(2 * np.pi * doy / 365 - 1.39)
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(delta), -1, 1))
    return 24 * 60 / np.pi * 0.0820 * dr * (ws * np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.sin(ws))


def et0_hargreaves(tmax, tmin, ra) -> np.ndarray:
    tmean = (tmax + tmin) / 2
    return np.maximum(0.0, 0.0023 * (tmean + 17.8) * np.sqrt(np.maximum(tmax - tmin, 0)) * 0.408 * ra)


def et0_penman_monteith(df: pd.DataFrame, lat: float) -> pd.Series:
    """Daily reference evapotranspiration, mm/day (FAO-56 Penman-Monteith).

    Falls back to Hargreaves on days where radiation, humidity or wind is missing.
    """
    doy = df.index.dayofyear.to_numpy()
    tmax, tmin = df["T2M_MAX"].to_numpy(float), df["T2M_MIN"].to_numpy(float)
    tmean = df["T2M"].fillna((df["T2M_MAX"] + df["T2M_MIN"]) / 2).to_numpy(float)
    rs = df["ALLSKY_SFC_SW_DWN"].to_numpy(float)
    if np.nanmedian(rs) < 10:          # POWER sometimes reports kWh/m2/day
        rs = rs * 3.6
    rh, u2 = df["RH2M"].to_numpy(float), df["WS2M"].to_numpy(float)

    ra = extraterrestrial_radiation(lat, doy)
    pressure = 101.3 * ((293 - 0.0065 * ELEVATION_M) / 293) ** 5.26
    gamma = 0.000665 * pressure
    es = (_sat_vp(tmax) + _sat_vp(tmin)) / 2
    ea = np.clip(rh, 0, 100) / 100 * es
    slope = 4098 * _sat_vp(tmean) / (tmean + 237.3) ** 2
    rso = (0.75 + 2e-5 * ELEVATION_M) * ra
    rns = 0.77 * rs
    rnl = 4.903e-9 * (((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2) \
        * (0.34 - 0.14 * np.sqrt(np.maximum(ea, 0))) * (1.35 * np.clip(rs / rso, 0.25, 1.0) - 0.35)
    rn = rns - rnl
    et0 = (0.408 * slope * rn + gamma * 900 / (tmean + 273) * u2 * (es - ea)) / (slope + gamma * (1 + 0.34 * u2))
    hg = et0_hargreaves(tmax, tmin, ra)
    et0 = np.where(np.isfinite(et0), np.maximum(et0, 0), hg)
    return pd.Series(et0, index=df.index, name="ET0")


# ---------------------------------------------------------------- climate features

@dataclass
class ClimateFeatures:
    years: list[int]
    hot_days_per_year: dict[int, int]
    hot_days_mean: float
    hot_days_trend_per_year: float
    annual_mean_temp: float
    temp_trend_per_decade: float
    monthly_mean_temp: dict[int, float]
    et0_annual_mm: float
    rain_annual_mm: float
    rain_winter_mm: float
    rain_summer_mm: float
    daily: pd.DataFrame = field(repr=False)   # full daily frame incl. ET0


def _trend(years: list[int], values: list[float]) -> float:
    if len(years) < 3:
        return 0.0
    slope = np.polyfit(np.array(years, float), np.array(values, float), 1)[0]
    return float(slope)


def climate_features(df: pd.DataFrame, lat: float) -> ClimateFeatures:
    d = df.copy()
    d["ET0"] = et0_penman_monteith(d, lat)
    counts = d.groupby(d.index.year)["T2M_MAX"].count()
    years = [int(y) for y, n in counts.items() if n >= 330]   # complete years only
    full = d[d.index.year.isin(years)]
    hot = full.groupby(full.index.year)["T2M_MAX"].apply(lambda s: int((s > HOT_DAY_C).sum()))
    ann_t = full.groupby(full.index.year)["T2M"].mean()
    winter = full[full.index.month.isin([11, 12, 1, 2, 3, 4])]
    summer = full[full.index.month.isin([5, 6, 7, 8, 9, 10])]
    n = max(len(years), 1)
    return ClimateFeatures(
        years=years,
        hot_days_per_year={int(k): int(v) for k, v in hot.items()},
        hot_days_mean=float(hot.mean()) if len(hot) else 0.0,
        hot_days_trend_per_year=_trend(list(hot.index), list(hot.values)),
        annual_mean_temp=float(ann_t.mean()) if len(ann_t) else float("nan"),
        temp_trend_per_decade=_trend(list(ann_t.index), list(ann_t.values)) * 10,
        monthly_mean_temp={int(m): float(v) for m, v in full.groupby(full.index.month)["T2M"].mean().items()},
        et0_annual_mm=float(full["ET0"].sum() / n),
        rain_annual_mm=float(full["PRECTOTCORR"].sum() / n),
        rain_winter_mm=float(winter["PRECTOTCORR"].sum() / n),
        rain_summer_mm=float(summer["PRECTOTCORR"].sum() / n),
        daily=d,
    )


# ---------------------------------------------------------------- crop water and heat

def kc_curve(crop: dict, n_days: int) -> np.ndarray:
    """Daily crop coefficient using the FAO-56 four-stage shape."""
    f_ini, f_dev, f_mid, f_late = crop["stage_fractions"]
    b1 = int(round(n_days * f_ini))
    b2 = b1 + int(round(n_days * f_dev))
    b3 = b2 + int(round(n_days * f_mid))
    k = np.empty(n_days)
    for i in range(n_days):
        if i < b1:
            k[i] = crop["kc_ini"]
        elif i < b2:
            k[i] = crop["kc_ini"] + (crop["kc_mid"] - crop["kc_ini"]) * (i - b1) / max(b2 - b1, 1)
        elif i < b3:
            k[i] = crop["kc_mid"]
        else:
            k[i] = crop["kc_mid"] + (crop["kc_end"] - crop["kc_mid"]) * (i - b3) / max(n_days - b3, 1)
    return k


def sensitive_window(crop: dict, n_days: int) -> tuple[int, int]:
    """Mid-season (flowering / grain or fruit set) is the heat-sensitive stage."""
    f_ini, f_dev, f_mid, _ = crop["stage_fractions"]
    start = int(round(n_days * (f_ini + f_dev)))
    return start, start + int(round(n_days * f_mid))


def crop_season_dates(crop: dict, year: int) -> tuple[date, date]:
    start = date(year, crop["plant_month"], crop["plant_day"])
    return start, start + timedelta(days=crop["season_days"] - 1)


def crop_metrics(crop_id: str, clim: ClimateFeatures, irrigation_method: str | None) -> CropMetrics:
    crop = CROPS[crop_id]
    d = clim.daily
    eff = IRRIGATION_EFFICIENCY.get(irrigation_method or "", DEFAULT_EFFICIENCY)
    # Paddy rice: seepage is already counted in extra_water_mm, so use the crop's own efficiency.
    eff = crop.get("application_efficiency", eff)
    n = crop["season_days"]
    kc = kc_curve(crop, n)
    s0, s1 = sensitive_window(crop, n)
    base_t = 5.0 if crop["season"] == "winter" else 10.0

    etcs, irrs, heats, gdds = [], [], [], []
    for y in clim.years:
        start, end = crop_season_dates(crop, y)
        w = d.loc[pd.Timestamp(start):pd.Timestamp(end)]
        if len(w) < n * 0.9:
            continue
        w = w.iloc[:n]
        k = kc[: len(w)]
        etc = float(np.nansum(w["ET0"].to_numpy() * k))
        peff = float(np.nansum(w["PRECTOTCORR"].to_numpy()) * EFFECTIVE_RAIN_FRACTION)
        etcs.append(etc)
        irrs.append(max(0.0, etc - peff) + crop.get("extra_water_mm", 0))
        heats.append(int((w["T2M_MAX"].iloc[s0:s1] > crop["heat_threshold_c"]).sum()))
        tmean = ((w["T2M_MAX"] + w["T2M_MIN"]) / 2).to_numpy()
        gdds.append(float(np.nansum(np.maximum(tmean - base_t, 0))))
    if not etcs:
        raise ValueError(f"not enough climate data to evaluate {crop_id}")
    irr = float(np.mean(irrs))
    gross_mm = irr / eff
    return CropMetrics(
        crop=crop_id, season=crop["season"],
        etc_mm=round(float(np.mean(etcs)), 1),
        irrigation_mm=round(irr, 1),
        gross_m3_per_feddan=round(gross_mm * 10 * FEDDAN_HA, 0),   # 1 mm on 1 ha = 10 m3
        heat_days=round(float(np.mean(heats)), 1),
        gdd=round(float(np.mean(gdds)), 0),
    )


# ---------------------------------------------------------------- NDVI features

@dataclass
class NdviFeatures:
    source: str
    bare_days_per_year: float
    peaks: list[dict]               # [{"date": "2025-02-10", "season": "winter", "ndvi": 0.71}]
    interpolated_share: float
    winter_peak_last_season: bool | None
    summer_peak_last_season: bool | None


def _season_of(ts: pd.Timestamp) -> str:
    return "winter" if ts.month in (11, 12, 1, 2, 3, 4) else "summer"


def ndvi_features(nd: NdviSeries, bare_threshold: float = 0.2, peak_threshold: float = 0.45) -> NdviFeatures:
    s = nd.series.dropna()
    years = max((s.index.max() - s.index.min()).days / 365.25, 0.1)
    step_days = 10
    bare = float((s < bare_threshold).sum() * step_days / years)
    vals = s.to_numpy()
    peaks = []
    for i in range(1, len(vals) - 1):
        if vals[i] >= peak_threshold and vals[i] >= vals[i - 1] and vals[i] > vals[i + 1]:
            ts = s.index[i]
            if peaks and (ts - pd.Timestamp(peaks[-1]["date"])).days < 60:
                if vals[i] > peaks[-1]["ndvi"]:
                    peaks[-1] = {"date": str(ts.date()), "season": _season_of(ts), "ndvi": round(float(vals[i]), 2)}
                continue
            peaks.append({"date": str(ts.date()), "season": _season_of(ts), "ndvi": round(float(vals[i]), 2)})

    def peak_in_last(season: str) -> bool | None:
        today = s.index.max()
        if season == "winter":
            y = today.year if today.month >= 5 else today.year - 1
            lo, hi = pd.Timestamp(y - 1, 11, 1), pd.Timestamp(y, 4, 30)
        else:
            y = today.year if today.month >= 11 else today.year - 1
            lo, hi = pd.Timestamp(y, 5, 1), pd.Timestamp(y, 10, 31)
        if s.index.min() > lo:
            return None
        return any(lo <= pd.Timestamp(p["date"]) <= hi for p in peaks)

    return NdviFeatures(
        source=nd.source,
        bare_days_per_year=round(bare, 0),
        peaks=peaks,
        interpolated_share=round(float(nd.interpolated.mean()) if len(nd.interpolated) else 0.0, 2),
        winter_peak_last_season=peak_in_last("winter"),
        summer_peak_last_season=peak_in_last("summer"),
    )
