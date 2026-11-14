"""NASA AppEEARS client: point time series for HLS, MODIS, ECOSTRESS, SMAP and SRTM.

AppEEARS (LP DAAC) does the heavy satellite processing on NASA's side and returns
small CSV files for one point, which suits a serverless engine (no GDAL/rasterio).

Flow: login (Earthdata username + password -> bearer token, ~48 h) -> submit a
point task -> poll its status -> list the bundle -> download the CSV files.
API reference: https://appeears.earthdatacloud.nasa.gov/api/
"""

from __future__ import annotations

import io
import logging
import time
from datetime import date

import httpx
import numpy as np
import pandas as pd

from ..settings import settings
from . import cache

log = logging.getLogger(__name__)

API = "https://appeears.earthdatacloud.nasa.gov/api"
TOKEN_MAX_AGE_S = 40 * 3600          # tokens last ~48 h; refresh well before that


class AppeearsError(RuntimeError):
    pass


def configured() -> bool:
    return bool(settings.EARTHDATA_USERNAME and settings.EARTHDATA_PASSWORD)


_token: dict[str, float | str] = {}


def _login() -> str:
    if not configured():
        raise AppeearsError("EARTHDATA_USERNAME / EARTHDATA_PASSWORD are not set")
    r = httpx.post(f"{API}/login", auth=(settings.EARTHDATA_USERNAME, settings.EARTHDATA_PASSWORD),
                   headers={"Content-Length": "0"}, timeout=30)
    if r.status_code >= 400:
        raise AppeearsError(f"AppEEARS login failed: HTTP {r.status_code}")
    return r.json()["token"]


def token(force: bool = False) -> str:
    """Bearer token, reused across calls (memory, then disk cache) until it is old."""
    now = time.time()
    if not force and _token and now - float(_token["at"]) < TOKEN_MAX_AGE_S:
        return str(_token["value"])
    if not force:
        hit = cache.get("appeears", "token", max_age_s=TOKEN_MAX_AGE_S)
        if hit:
            _token.update(value=hit, at=now)
            return hit
    value = _login()
    _token.update(value=value, at=now)
    cache.put("appeears", "token", value)
    return value


def _request(method: str, path: str, **kw) -> httpx.Response:
    """Authenticated call; on 401/403 (expired token) log in again once."""
    for attempt in range(2):
        headers = {"Authorization": f"Bearer {token(force=attempt == 1)}", **kw.pop("headers", {})}
        r = httpx.request(method, f"{API}{path}", headers=headers, timeout=kw.pop("timeout", 60), **kw)
        if r.status_code in (401, 403) and attempt == 0:
            continue
        if r.status_code >= 400:
            raise AppeearsError(f"AppEEARS {method} {path}: HTTP {r.status_code} {r.text[:200]}")
        return r
    raise AppeearsError("unreachable")


def _mdy(d: date) -> str:
    return d.strftime("%m-%d-%Y")


def submit_point_task(name: str, lat: float, lng: float, start: date, end: date,
                      layers: list[tuple[str, str]]) -> str:
    """Submit one point request. `layers` = [(product_id, layer_name), ...]. Returns the task id."""
    body = {
        "task_type": "point",
        "task_name": name,
        "params": {
            "dates": [{"startDate": _mdy(start), "endDate": _mdy(end)}],
            "layers": [{"product": p, "layer": layer} for p, layer in layers],
            "coordinates": [{"latitude": round(lat, 5), "longitude": round(lng, 5), "id": "field", "category": "field"}],
        },
    }
    r = _request("POST", "/task", json=body)
    task_id = r.json().get("task_id")
    if not task_id:
        raise AppeearsError(f"AppEEARS did not return a task id: {r.text[:200]}")
    return task_id


def task_status(task_id: str) -> str:
    """'pending' | 'queued' | 'processing' | 'done' | 'error' (as reported by AppEEARS)."""
    return str(_request("GET", f"/task/{task_id}").json().get("status", "unknown"))


def download_csvs(task_id: str) -> dict[str, str]:
    """All CSV files of a finished task: {file_name: csv_text}."""
    files = _request("GET", f"/bundle/{task_id}").json().get("files", [])
    out = {}
    for f in files:
        if f.get("file_type") == "csv" or str(f.get("file_name", "")).endswith(".csv"):
            r = _request("GET", f"/bundle/{task_id}/{f['file_id']}", follow_redirects=True, timeout=120)
            out[f["file_name"]] = r.text
    return out


# ---------------------------------------------------------------- CSV parsing

def column_for(df: pd.DataFrame, product: str, layer: str) -> str | None:
    """AppEEARS point CSV columns are named '<PRODUCT>_<VERSION>_<LAYER>', e.g.
    'MOD13Q1_061__250m_16_days_NDVI' or 'HLSL30_VI_020_NDVI'."""
    prefix = product.replace(".", "_")
    exact = f"{prefix}_{layer}"
    if exact in df.columns:
        return exact
    for c in df.columns:              # tolerate small naming differences
        if c.startswith(prefix) and c.endswith(f"_{layer}"):
            return c
    return None


def read_layer(csv_text: str, product: str, layer: str, fill: float | None = None,
               scale: float | None = None, valid: tuple[float, float] | None = None) -> pd.Series:
    """One layer as a date-indexed float series with missing values removed.

    AppEEARS normally writes values already scaled; if the values are clearly raw
    integers (outside `valid` but inside it once scaled) the scale factor is applied.
    Values equal to the fill value or outside `valid` become NaN and are dropped,
    never filled in.
    """
    df = pd.read_csv(io.StringIO(csv_text))
    col = column_for(df, product, layer)
    if col is None or "Date" not in df.columns:
        return pd.Series(dtype=float)
    s = pd.to_numeric(df[col], errors="coerce")
    s.index = pd.to_datetime(df["Date"], errors="coerce")
    s = s[s.index.notna()]
    if fill is not None:
        s = s.mask(np.isclose(s, fill))
    if scale and valid is not None:
        med = s.abs().median()
        if pd.notna(med) and med > max(abs(valid[0]), abs(valid[1])) and med * scale <= max(abs(valid[0]), abs(valid[1])):
            s = s * scale
    if valid is not None:
        s = s.mask((s < valid[0]) | (s > valid[1]))
    return s.dropna().sort_index()
