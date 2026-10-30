#!/usr/bin/env python3
"""Pre-engine helper: validate + clean the NASA POWER pilot download.

INTERIM script written during the pre-engine data sprint (before the
fieldshift engine exists). The engine's data/power.py will implement the
same rules properly (CLAUDE.md Part 4/5); raw/ stays the single source of
truth and cleaned/ is regenerated from raw.

Implements:
  * DATA.md §5.4 parsing rules (header block, -999 -> NaN, YEAR+DOY / YEAR+MO+DY)
  * V-POWER-002..010 checks (DATA.md §12)
  * cleaned/climate_daily_<locid>.csv      (§5.5)
  * cleaned/climate_seasonal_<locid>.csv   (§5.6)
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

RAW = ("FieldShift_Data/raw/power/"
       "power_31.04_31.38_20110101_20251231_20261030.csv")
LOCID = "31.04_31.38"
OUT_DAILY = f"FieldShift_Data/cleaned/climate_daily_{LOCID}.csv"
OUT_SEASON = f"FieldShift_Data/cleaned/climate_seasonal_{LOCID}.csv"
OUT_HEADER = f"FieldShift_Data/metadata/power_{LOCID}_header.txt"
MISSING_CODE = -999.0           # confirmed in header
REQ_LAT, REQ_LON = 31.04, 31.38
HOT_T, COLD_T, FROST_T = 35.0, 5.0, 0.0   # generic context thresholds (thresholds.yaml later)
PLAUSIBLE = {"temp": (-10, 55), "rain": (0, 200), "solar": (0, 40)}

# ---------------------------------------------------------------- parse
def load_raw(path: str):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    # rule 1: find -END HEADER-, store metadata verbatim
    try:
        end = lines.index("-END HEADER-")
    except ValueError:
        end = next(i for i, l in enumerate(lines) if "YEAR" in l.split(",")[:2])
        header_lines = lines[:end]
    else:
        header_lines = lines[: end + 1]
    header_txt = "\n".join(header_lines)
    table = lines[end + 1:]
    df = pd.read_csv(__import__("io").StringIO("\n".join(table)))
    raw_params = [c for c in df.columns if c not in {"YEAR", "DOY", "MO", "DY"}]
    return df, raw_params, header_txt, header_lines

def build_dates(df: pd.DataFrame) -> pd.DataFrame:
    if {"YEAR", "DOY"} <= set(df.columns):
        df["date"] = pd.to_datetime(
            df["YEAR"].astype(str), format="%Y") + pd.to_timedelta(df["DOY"].astype(int) - 1, unit="D")
    elif {"YEAR", "MO", "DY"} <= set(df.columns):
        df["date"] = pd.to_datetime(
            {"year": df["YEAR"], "month": df["MO"], "day": df["DY"]})
    else:
        raise SystemExit("V-POWER: neither YEAR+DOY nor YEAR+MO+DY present")
    return df

# ---------------------------------------------------------------- checks
def main() -> int:
    errors, warns = [], []
    df, raw_params, header_txt, _header_lines = load_raw(RAW)
    with open(OUT_HEADER, "w", encoding="utf-8") as fh:
        fh.write(header_txt + "\n")

    # V-POWER-002 header names all five parameters
    need = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN"]
    if not all(p in raw_params for p in need):
        errors.append("header_mismatch")
    # V-POWER-003 dates
    df = build_dates(df)
    if df["date"].isna().any():
        errors.append("bad_dates")
    if not df["date"].is_monotonic_increasing or df["date"].duplicated().any():
        errors.append("bad_dates")
    # V-POWER-004 gaps
    span = (df["date"].max() - df["date"].min()).days + 1
    if len(df) != span:
        warns.append("date_gaps")
    # missing-code scan (§5.3 candidate confirmation)
    miss_counts = {c: int((df[c] == MISSING_CODE).sum()) for c in raw_params}
    df = df.replace(MISSING_CODE, np.nan)
    # V-POWER-005 missing share
    n = len(df)
    for k in miss_counts.values():
        if k and 0.05 <= k / n < 0.20:
            warns.append("climate_missing_values")
        if k / n >= 0.20:
            errors.append("climate_missing_values")
    ren = {"T2M": "t_mean_c", "T2M_MAX": "t_max_c", "T2M_MIN": "t_min_c",
           "PRECTOTCORR": "rain_mm", "ALLSKY_SFC_SW_DWN": "solar_mj_m2"}
    df = df.rename(columns=ren)
    # V-POWER-006 temperature consistency (missing-aware)
    bad_t = df[["t_mean_c", "t_max_c", "t_min_c"]].dropna()
    viol = (bad_t["t_min_c"] > bad_t["t_mean_c"]) | (bad_t["t_mean_c"] > bad_t["t_max_c"])
    if viol.any():
        warns.append("inconsistent_temperature")
    # V-POWER-007 plausibility
    oor = []
    for col, lo, hi in (("t_mean_c", -10, 55), ("t_max_c", -10, 55), ("t_min_c", -10, 55),
                        ("rain_mm", 0, 200), ("solar_mj_m2", 0, 40)):
        s = df[col].dropna()
        if ((s < lo) | (s > hi)).any():
            oor.append(f"{col}({int(((s<lo)|(s>hi)).sum())})")
    if oor:
        warns.append("out_of_range:" + ",".join(oor))
    # V-POWER-008 complete years & record length
    yrs = sorted(df["date"].dt.year.unique())
    complete_years = [int(y) for y in yrs
                      if df["date"].dt.year.eq(y).sum() == (366 if __import__("calendar").isleap(y) else 365)]
    short = len(complete_years) < 5
    if short:
        warns.append("climate_short_record")
    # V-POWER-010 header location within 1 deg
    import re
    m = re.search(r"latitude\s+(-?[\d.]+)\s+longitude\s+(-?[\d.]+)", header_txt)
    hdr_lat, hdr_lon = float(m.group(1)), float(m.group(2)) if m else (np.nan, np.nan)
    if abs(hdr_lat - REQ_LAT) > 1 or abs(hdr_lon - REQ_LON) > 1:
        warns.append("grid_cell_far")

    # -------------------------------------------------- clean table (§5.5)
    clean = pd.DataFrame({"date": df["date"].dt.strftime("%Y-%m-%d"),
                          "year": df["date"].dt.year, "month": df["date"].dt.month,
                          "doy": df["date"].dt.day_of_year,
                          "t_mean_c": df["t_mean_c"], "t_max_c": df["t_max_c"],
                          "t_min_c": df["t_min_c"],
                          "rain_mm": df["rain_mm"],
                          "solar_mj_m2": df["solar_mj_m2"]})
    qc = "ok"
    qcmap = clean[["t_mean_c", "t_max_c", "t_min_c", "rain_mm", "solar_mj_m2"]].isna().any(axis=1)
    qc = np.where(qcmap, "missing_value", "ok")
    # re-mark plausibility outliers per row
    for col, lo, hi in (("t_mean_c", -10, 55), ("t_max_c", -10, 55), ("t_min_c", -10, 55),
                        ("rain_mm", 0, 200), ("solar_mj_m2", 0, 40)):
        bad = df[col].notna() & ((df[col] < lo) | (df[col] > hi))
        qc = np.where(bad, np.char.add(qc.astype(str), ";out_of_range"), qc)
    clean["qc"] = qc
    clean.to_csv(OUT_DAILY, index=False)

    # -------------------------------------------------- seasonal (§5.6)
    rows = []
    d = clean.copy()
    d["date"] = pd.to_datetime(d["date"])
    d["y"] = d["date"].dt.year; d["m"] = d["date"].dt.month
    for slot in ("winter", "summer"):
        months = {11, 12, 1, 2, 3, 4} if slot == "winter" else {5, 6, 7, 8, 9, 10}
        starts = sorted({y for y, m in zip(d["y"], d["m"]) if m in months})
        for ys in starts:
            mask = d["m"].isin(months)
            if slot == "winter":
                # window = Nov of ys .. Apr of ys+1; year_start = year holding November
                mask &= (((d["y"] == ys) & (d["m"] >= 11)) | ((d["y"] == ys + 1) & (d["m"] <= 4)))
            else:
                mask &= (d["y"] == ys) & (d["m"] >= 5) & (d["m"] <= 10)
            w = d[mask]
            if w.empty:
                continue
            n_days = len(w); n_missing = int((w["qc"] != "ok").sum())
            import calendar as _cal
            expected = 181 + (1 if _cal.isleap(ys + 1) else 0) if slot == "winter" else 184
            # complete = fully inside the data period AND no missing values
            complete = n_days == expected and n_missing == 0
            rows.append({
                "slot": slot, "year_start": ys, "n_days": n_days, "n_missing": n_missing,
                "t_mean_c": round(w["t_mean_c"].mean(), 2),
                "t_max_mean_c": round(w["t_max_c"].mean(), 2),
                "t_max_abs_c": w["t_max_c"].max(),
                "t_min_mean_c": round(w["t_min_c"].mean(), 2),
                "t_min_abs_c": w["t_min_c"].min(),
                "rain_total_mm": round(w["rain_mm"].sum(), 2),
                "rain_days_ge_1mm": int((w["rain_mm"] >= 1).sum()),
                "hot_days_tmax_ge_35": int((w["t_max_c"] >= HOT_T).sum()),
                "cold_days_tmin_le_5": int((w["t_min_c"] <= COLD_T).sum()),
                "frost_days_tmin_le_0": int((w["t_min_c"] <= FROST_T).sum()),
                "solar_mean_mj_m2": round(w["solar_mj_m2"].mean(), 2),
                "complete": complete})
    seas = pd.DataFrame(rows).sort_values(["slot", "year_start"]).reset_index(drop=True)
    seas.to_csv(OUT_SEASON, index=False)

    # -------------------------------------------------- report
    print("=" * 64)
    print("V-POWER VALIDATION REPORT —", RAW.replace("FieldShift_Data/", ""))
    print("=" * 64)
    print(f"rows={len(df)}  span={df['date'].min().date()}..{df['date'].max().date()}  expected={span}")
    print(f"missing -999 per column: {miss_counts}")
    print(f"complete years ({len(complete_years)}): {complete_years}")
    print(f"header location: lat {hdr_lat} lon {hdr_lon} (requested {REQ_LAT}/{REQ_LON})")
    print("ERRORS:", errors if errors else "none")
    print("WARNS :", warns if warns else "none")
    print("-" * 64)
    print("Seasonal windows — complete count by slot:")
    comp = seas.groupby("slot")["complete"].sum().to_dict()
    print(comp)
    print("\nWinter median across years: hot_days, cold_days, frost_days, rain_total_mm")
    wdf = seas[seas.slot == "winter"]
    print(wdf[["hot_days_tmax_ge_35", "cold_days_tmin_le_5", "frost_days_tmin_le_0",
               "rain_total_mm", "t_max_mean_c", "t_min_mean_c"]].median().round(1).to_dict())
    print("\nSummer median across years:")
    sdf = seas[seas.slot == "summer"]
    print(sdf[["hot_days_tmax_ge_35", "rain_total_mm", "t_max_mean_c", "t_min_mean_c",
               "solar_mean_mj_m2"]].median().round(1).to_dict())
    print(f"\nwrote: {OUT_DAILY} {OUT_SEASON} {OUT_HEADER}")
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
