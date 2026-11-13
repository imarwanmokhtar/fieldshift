"""Sentinel-2 NDVI at the pin, via the Copernicus Data Space Sentinel Hub Statistical API.

Status: written against the public API docs but NOT yet tested with real
credentials (see the checklist in python-engine-guide.md section 10).
- With COPERNICUS_CLIENT_ID / COPERNICUS_CLIENT_SECRET set: calls the API, caches per pin.
- Without them: returns None (layer "unavailable"), or a clearly labelled mock
  series when USE_MOCK_LAYERS=true.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import date, timedelta

import httpx
import numpy as np
import pandas as pd

from ..settings import settings
from . import cache

log = logging.getLogger(__name__)

TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
STATS_URL = "https://sh.dataspace.copernicus.eu/api/v1/statistics"

# NDVI with the Sentinel-2 scene classification (SCL) used as a cloud / shadow mask.
EVALSCRIPT = """//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B04", "B08", "SCL", "dataMask"] }],
    output: [
      { id: "ndvi", bands: 1, sampleType: "FLOAT32" },
      { id: "dataMask", bands: 1 }
    ]
  };
}
function evaluatePixel(s) {
  // SCL 3 = cloud shadow, 8/9 = cloud, 10 = cirrus, 11 = snow
  var bad = [3, 8, 9, 10, 11].indexOf(s.SCL) !== -1;
  var ndvi = (s.B08 - s.B04) / (s.B08 + s.B04);
  return { ndvi: [ndvi], dataMask: [s.dataMask && !bad ? 1 : 0] };
}
"""


@dataclass
class NdviSeries:
    series: pd.Series          # date -> mean NDVI (interpolated, 10-day steps)
    interpolated: pd.Series    # date -> bool (True where the value was gap-filled)
    source: str                # "sentinel2" or "mock"


def _square(lat: float, lng: float, half_m: float = 30.0) -> list[list[float]]:
    dlat = half_m / 111_320
    dlng = half_m / (111_320 * math.cos(math.radians(lat)))
    return [[lng - dlng, lat - dlat], [lng + dlng, lat - dlat], [lng + dlng, lat + dlat],
            [lng - dlng, lat + dlat], [lng - dlng, lat - dlat]]


def _token() -> str:
    r = httpx.post(TOKEN_URL, data={
        "grant_type": "client_credentials",
        "client_id": settings.COPERNICUS_CLIENT_ID,
        "client_secret": settings.COPERNICUS_CLIENT_SECRET,
    }, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def _fetch_stats(lat: float, lng: float, start: date, end: date) -> list[dict]:
    body = {
        "input": {
            "bounds": {"geometry": {"type": "Polygon", "coordinates": [_square(lat, lng)]}},
            "data": [{"type": "sentinel-2-l2a", "dataFilter": {"maxCloudCoverage": 80}}],
        },
        "aggregation": {
            "timeRange": {"from": f"{start}T00:00:00Z", "to": f"{end}T23:59:59Z"},
            "aggregationInterval": {"of": "P10D"},
            "evalscript": EVALSCRIPT,
            "resx": 10, "resy": 10,
        },
    }
    r = httpx.post(STATS_URL, json=body, headers={"Authorization": f"Bearer {_token()}"}, timeout=90)
    r.raise_for_status()
    return r.json().get("data", [])


def _to_series(rows: list[dict]) -> tuple[pd.Series, pd.Series]:
    points = {}
    for row in rows:
        try:
            st = row["outputs"]["ndvi"]["bands"]["B0"]["stats"]
            if st.get("sampleCount", 0) - st.get("noDataCount", 0) <= 0:
                continue
            points[pd.Timestamp(row["interval"]["from"][:10])] = float(st["mean"])
        except (KeyError, TypeError, ValueError):
            continue
    s = pd.Series(points).sort_index()
    if s.empty:
        return s, s.astype(bool)
    full = pd.date_range(s.index.min(), s.index.max(), freq="10D")
    s = s.reindex(s.index.union(full))
    interp = s.isna()
    s = s.interpolate(method="time").reindex(full)
    return s, interp.reindex(full).fillna(False)


def _mock(lat: float, lng: float, years: int = 3) -> NdviSeries:
    """Two crop cycles a year (winter peak ~Feb, summer peak ~Aug) with bare gaps."""
    end = date.today()
    idx = pd.date_range(end - timedelta(days=365 * years), end, freq="10D")
    doy = idx.dayofyear.to_numpy()
    winter = 0.72 * np.exp(-((((doy - 50 + 182) % 365) - 182) / 38.0) ** 2)
    summer = 0.68 * np.exp(-((((doy - 225 + 182) % 365) - 182) / 32.0) ** 2)
    vals = np.clip(0.12 + winter + summer, 0, 0.9)
    s = pd.Series(vals, index=idx)
    return NdviSeries(series=s, interpolated=pd.Series(False, index=idx), source="mock")


def fetch_ndvi(lat: float, lng: float, years: int = 3) -> NdviSeries | None:
    if not (settings.COPERNICUS_CLIENT_ID and settings.COPERNICUS_CLIENT_SECRET):
        return _mock(lat, lng, years) if settings.USE_MOCK_LAYERS else None
    end = date.today()
    start = end - timedelta(days=365 * years)
    key = f"ndvi:{round(lat, 4)}:{round(lng, 4)}:{start.isoformat()[:7]}"
    rows = cache.get("ndvi", key, max_age_s=7 * 24 * 3600)
    try:
        if rows is None:
            rows = _fetch_stats(lat, lng, start, end)
            cache.put("ndvi", key, rows)
        s, interp = _to_series(rows)
        if len(s) < 10:
            return None
        return NdviSeries(series=s, interpolated=interp, source="sentinel2")
    except Exception as exc:
        log.warning("Sentinel-2 NDVI unavailable: %s", exc)
        return None
