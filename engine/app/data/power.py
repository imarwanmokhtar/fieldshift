"""NASA POWER daily point client (live, no key) with disk cache and -999 handling.

If POWER cannot be reached, `load_climate` falls back to a small bundled monthly
climatology for the Dakahlia area (data/fallback_climatology_dakahlia.json).
That fallback is approximate, is NOT NASA data, and is always flagged in the
evidence pack so the farmer sees lower confidence.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import httpx
import numpy as np
import pandas as pd

from ..settings import settings
from . import cache

log = logging.getLogger(__name__)

URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMS = "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,ALLSKY_SFC_SW_DWN,RH2M,WS2M"
COLUMNS = PARAMS.split(",")


@dataclass
class ClimateData:
    df: pd.DataFrame          # daily, DatetimeIndex, columns = COLUMNS
    source: str               # "nasa_power" or "fallback_climatology"
    lat: float
    lng: float


def fetch_power(lat: float, lng: float, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    start = start or settings.POWER_START
    end = end or settings.POWER_END
    lat_r, lng_r = round(lat, 2), round(lng, 2)
    key = f"power:{lat_r}:{lng_r}:{start}:{end}:{PARAMS}"
    raw = cache.get("power", key)
    if raw is None:
        r = httpx.get(URL, params={
            "parameters": PARAMS, "community": "AG",
            "latitude": lat_r, "longitude": lng_r,
            "start": start, "end": end, "format": "JSON",
        }, timeout=90)
        r.raise_for_status()
        raw = r.json()["properties"]["parameter"]
        cache.put("power", key, raw)
    df = pd.DataFrame(raw)
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df = df.astype(float).mask(lambda d: d <= -990)   # -999 is POWER's missing value
    return df.sort_index()


def fallback_climate(lat: float, lng: float, years: int = 10) -> pd.DataFrame:
    """Daily series built by interpolating a monthly climatology (same every year)."""
    clim = json.loads((settings.DATA_DIR / "fallback_climatology_dakahlia.json").read_text(encoding="utf-8"))
    months = clim["monthly"]
    end_year = int(settings.POWER_END[:4])
    idx = pd.date_range(f"{end_year - years + 1}-01-01", f"{end_year}-12-31", freq="D")
    # Mid-month anchors, interpolated by day of year (wraps around the year).
    anchor_doy = np.array([15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349])
    doy = idx.dayofyear.to_numpy()
    out = {}
    for col in ["T2M_MAX", "T2M_MIN", "ALLSKY_SFC_SW_DWN", "RH2M", "WS2M"]:
        vals = np.array([m[col] for m in months], dtype=float)
        x = np.concatenate([anchor_doy - 365, anchor_doy, anchor_doy + 365])
        y = np.concatenate([vals, vals, vals])
        out[col] = np.interp(doy, x, y)
    df = pd.DataFrame(out, index=idx)
    df["T2M"] = (df["T2M_MAX"] + df["T2M_MIN"]) / 2
    # Spread each month's rainfall evenly over its days.
    rain_month = np.array([m["PRECTOTCORR_MONTH_MM"] for m in months], dtype=float)
    df["PRECTOTCORR"] = rain_month[idx.month - 1] / idx.days_in_month
    return df[COLUMNS]


def load_climate(lat: float, lng: float) -> ClimateData:
    try:
        df = fetch_power(lat, lng)
        if df["T2M_MAX"].notna().sum() < 365:
            raise ValueError("too little POWER data")
        return ClimateData(df=df, source="nasa_power", lat=lat, lng=lng)
    except Exception as exc:  # network, HTTP or parse error
        log.warning("NASA POWER unavailable (%s); using fallback climatology", exc)
        return ClimateData(df=fallback_climate(lat, lng), source="fallback_climatology", lat=lat, lng=lng)


def apply_scenario(df: pd.DataFrame, temp_delta_c: float = 0.0, rain_factor: float = 1.0) -> pd.DataFrame:
    """'What if it gets hotter / drier?' Shift temperatures and scale rainfall."""
    if temp_delta_c == 0.0 and rain_factor == 1.0:
        return df
    out = df.copy()
    for col in ("T2M", "T2M_MAX", "T2M_MIN"):
        out[col] = out[col] + temp_delta_c
    out["PRECTOTCORR"] = out["PRECTOTCORR"] * rain_factor
    return out
