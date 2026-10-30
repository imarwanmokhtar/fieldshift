"""data/power.py — NASA POWER download + parse + clean (Phase 4)."""
from __future__ import annotations

import json
import time
from datetime import date, datetime
from pathlib import Path

import httpx
import pandas as pd

PARAMS = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN"]
BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
MISSING_CODE = -999
RENAME = {
    "T2M": "t_mean_c", "T2M_MAX": "t_max_c", "T2M_MIN": "t_min_c",
    "PRECTOTCORR": "rain_mm", "ALLSKY_SFC_SW_DWN": "solar_mj_m2",
}


def build_url(lat: float, lon: float, start: str, end: str) -> str:
    """Build the POWER daily point CSV URL from a template (never hard-code the pilot point)."""
    return (
        f"{BASE_URL}?parameters={','.join(PARAMS)}&community=AG"
        f"&longitude={lon}&latitude={lat}&start={start}&end={end}&format=CSV"
    )


def _ymd(d: date | str) -> str:
    if isinstance(d, str):
        d = date.fromisoformat(d)
    return d.strftime("%Y%m%d")


def download_power(lat: float, lon: float, start, end, out_dir: Path,
                   retries: int = 3, timeout: float = 60.0) -> tuple[Path, dict]:
    """Download POWER CSV, save raw + .request.json sidecar, append retrieval log.

    Returns (raw_path, request_meta). Raises on persistent failure.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    s, e = _ymd(start), _ymd(end)
    locid = f"{lat:.2f}_{lon:.2f}"
    raw_path = out_dir / f"power_{locid}_{s}_{e}_{_today()}.csv"
    sidecar = raw_path.with_suffix(".request.json")
    url = build_url(lat, lon, s, e)

    meta = {"url": url, "lat": lat, "lon": lon, "start": s, "end": e,
            "http_status": None, "bytes": None, "attempts": 0}
    last_exc = None
    for attempt in range(1, retries + 1):
        meta["attempts"] = attempt
        try:
            with httpx.Client(timeout=timeout) as client:
                r = client.get(url)
            meta["http_status"] = r.status_code
            if r.status_code == 200:
                raw_path.write_text(r.text, encoding="utf-8")
                meta["bytes"] = len(r.content)
                sidecar.write_text(json.dumps(meta, indent=2), encoding="utf-8")
                return raw_path, meta
            last_exc = RuntimeError(f"HTTP {r.status_code}")
        except Exception as exc:
            last_exc = exc
            meta["http_status"] = None
        time.sleep(2 ** (attempt - 1))
    sidecar.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    raise RuntimeError(f"POWER download failed after {retries} tries: {last_exc}")


def _today() -> str:
    return datetime.now().date().strftime("%Y%m%d")


def parse_power(raw_path: Path) -> pd.DataFrame:
    """Parse a POWER CSV into a tidy DataFrame per DATA.md §5.4."""
    lines = Path(raw_path).read_text(encoding="utf-8").splitlines()
    try:
        end = lines.index("-END HEADER-")
    except ValueError:
        end = next(i for i, ln in enumerate(lines) if "YEAR" in ln.split(",")[:2])
    hdr_idx = end + 1
    if "YEAR" not in lines[hdr_idx].split(",")[:2]:
        hdr_idx = next(i for i in range(end + 1, len(lines)) if "YEAR" in lines[i].split(",")[:2])
    df = pd.read_csv(raw_path, skiprows=hdr_idx)
    # build date
    if {"YEAR", "DOY"} <= set(df.columns):
        df["date"] = pd.to_datetime(df["YEAR"].astype(str), format="%Y") + pd.to_timedelta(
            df["DOY"].astype(int) - 1, unit="D")
    elif {"YEAR", "MO", "DY"} <= set(df.columns):
        df["date"] = pd.to_datetime({"year": df["YEAR"], "month": df["MO"], "day": df["DY"]})
    else:
        raise ValueError("POWER file has neither YEAR+DOY nor YEAR+MO+DY")
    df = df.rename(columns=RENAME)
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    # missing values -> NaN
    for col in ("t_mean_c", "t_max_c", "t_min_c", "rain_mm", "solar_mj_m2"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df.loc[df[col] == MISSING_CODE, col] = float("nan")
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["doy"] = df["date"].dt.dayofyear
    return df.sort_values("date").reset_index(drop=True)


def clean_power(df: pd.DataFrame) -> pd.DataFrame:
    """Build the cleaned daily table with a qc column (DATA.md §5.5)."""
    out = pd.DataFrame({
        "date": df["date"].dt.strftime("%Y-%m-%d"),
        "year": df["date"].dt.year,
        "month": df["date"].dt.month,
        "doy": df["date"].dt.dayofyear,
        "t_mean_c": df["t_mean_c"],
        "t_max_c": df["t_max_c"],
        "t_min_c": df["t_min_c"],
        "rain_mm": df["rain_mm"],
        "solar_mj_m2": df["solar_mj_m2"],
    })
    qc = []
    for _, r in df.iterrows():
        flags = []
        cols = ("t_mean_c", "t_max_c", "t_min_c", "rain_mm", "solar_mj_m2")
        if any(pd.isna(r.get(c)) for c in cols):
            # only flag if the raw was -999 (NaN) — here NaN means missing
            flags.append("missing_value")
        vals = {"t_mean_c": r.get("t_mean_c"), "t_max_c": r.get("t_max_c"),
                "t_min_c": r.get("t_min_c"), "rain_mm": r.get("rain_mm"),
                "solar_mj_m2": r.get("solar_mj_m2")}
        plaus = {"t_mean_c": (-10, 55), "t_max_c": (-10, 55), "t_min_c": (-10, 55),
                 "rain_mm": (0, 200), "solar_mj_m2": (0, 40)}
        for col, (lo, hi) in plaus.items():
            v = vals[col]
            if pd.notna(v) and (v < lo or v > hi):
                flags.append("out_of_range")
        qc.append(";".join(flags) if flags else "ok")
    out["qc"] = qc
    return out


def seasonal_summary(df: pd.DataFrame, thresholds: dict | None = None) -> pd.DataFrame:
    """One row per (slot, year_start) per DATA.md §5.6."""
    if thresholds is None:
        thresholds = {"hot_day_tmax_c": 35, "cold_day_tmin_c": 5, "frost_day_tmin_c": 0}
    hot_t = thresholds.get("hot_day_tmax_c", 35)
    cold_t = thresholds.get("cold_day_tmin_c", 5)
    frost_t = thresholds.get("frost_day_tmin_c", 0)

    def _r(s):
        return round(float(s.mean()), 2) if s.notna().any() else None

    def _mx(s):
        return float(s.max()) if s.notna().any() else None

    def _mn(s):
        return float(s.min()) if s.notna().any() else None

    def _rs(s):
        return round(float(s.sum()), 1) if s.notna().any() else None
    work = df.copy()
    work["date"] = pd.to_datetime(work["date"])
    work["y"] = work["date"].dt.year
    work["m"] = work["date"].dt.month
    rows = []
    for slot in ("winter", "summer"):
        months = {11, 12, 1, 2, 3, 4} if slot == "winter" else {5, 6, 7, 8, 9, 10}
        starts = sorted({y for y, m in zip(work["y"], work["m"], strict=True) if m in months})
        for ys in starts:
            if slot == "winter":
                mask = (((work["y"] == ys) & (work["m"] >= 11)) |
                        ((work["y"] == ys + 1) & (work["m"] <= 4)))
            else:
                mask = (work["y"] == ys) & (work["m"] >= 5) & (work["m"] <= 10)
            w = work[mask]
            if w.empty:
                continue
            n_days = len(w)
            n_missing = (
                int((w["qc"].ne("ok")).sum())
                if "qc" in w.columns
                else int(w.isna().any(axis=1).sum())
            )
            # expected days
            import calendar as _cal
            expected = 181 + (1 if _cal.isleap(ys + 1) else 0) if slot == "winter" else 184
            complete = (n_days == expected) and (n_missing == 0)
            rows.append({
                "slot": slot,
                "year_start": ys,
                "n_days": n_days,
                "n_missing": n_missing,
                "t_mean_c": _r(w["t_mean_c"]),
                "t_max_mean_c": _r(w["t_max_c"]),
                "t_min_mean_c": _r(w["t_min_c"]),
                "t_max_abs_c": _mx(w["t_max_c"]),
                "t_min_abs_c": _mn(w["t_min_c"]),
                "rain_total_mm": _rs(w["rain_mm"]),
                "rain_days_ge_1mm": int((w["rain_mm"] >= 1).sum()),
                "hot_days_tmax_ge_35": int((w["t_max_c"] >= hot_t).sum()),
                "cold_days_tmin_le_5": int((w["t_min_c"] <= cold_t).sum()),
                "frost_days_tmin_le_0": int((w["t_min_c"] <= frost_t).sum()),
                "solar_mean_mj_m2": _r(w["solar_mj_m2"]),
                "complete": bool(complete),
            })
    return pd.DataFrame(rows)
