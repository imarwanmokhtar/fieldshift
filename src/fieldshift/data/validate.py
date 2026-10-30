"""data/validate.py — V-* checks (Phase 4: V-POWER; others added in later phases)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .crops import validate as validate_crops


def v_power(df: pd.DataFrame, raw_params: list[str], header_txt: str = "",
            lat: float | None = None, lon: float | None = None) -> tuple[list[str], list[str]]:
    """V-POWER-001..010 style checks. Returns (errors, warns)."""
    errors: list[str] = []
    warns: list[str] = []
    cleaned_need = ["t_mean_c", "t_max_c", "t_min_c", "rain_mm", "solar_mj_m2"]
    for p in cleaned_need:
        if p not in df.columns:
            errors.append(f"V-POWER-002 missing column {p}")
    # V-POWER-001 row count >= 1
    if len(df) == 0:
        errors.append("V-POWER-001 empty dataframe")
    # missing values
    n = len(df)
    miss = 0
    for col in cleaned_need:
        if col in df.columns:
            miss += int(df[col].isna().sum())
    if n > 0 and miss / n >= 0.20:
        errors.append("V-POWER-005 climate_missing_values")
    elif n > 0 and miss / n >= 0.05:
        warns.append("V-POWER-005 climate_missing_values")
    # plausibility
    plaus = {"t_mean_c": (-10, 55), "t_max_c": (-10, 55), "t_min_c": (-10, 55),
             "rain_mm": (0, 200), "solar_mj_m2": (0, 40)}
    oor = []
    for col, (lo, hi) in plaus.items():
        if col in df.columns:
            s = df[col].dropna()
            bad = int(((s < lo) | (s > hi)).sum())
            if bad:
                oor.append(f"{col}({bad})")
    if oor:
        warns.append("V-POWER-006 out_of_range:" + ",".join(oor))
    # header lat/lon check (best-effort from header_txt)
    if lat is not None and lon is not None and header_txt:
        import re
        mlat = re.search(r"latitude\s+([\d.]+)", header_txt)
        mlon = re.search(r"longitude\s+([\d.]+)", header_txt)
        if mlat and abs(float(mlat.group(1)) - lat) > 1e-9:
            errors.append("V-POWER-010 latitude mismatch")
        if mlon and abs(float(mlon.group(1)) - lon) > 1e-9:
            errors.append("V-POWER-010 longitude mismatch")
    # date uniqueness/sort
    if "date" in df.columns:
        if df["date"].duplicated().any():
            errors.append("V-POWER-003 duplicate dates")
        if not df["date"].is_monotonic_increasing:
            errors.append("V-POWER-003 dates not sorted")
    return errors, warns


def v_crops(doc: dict) -> tuple[list[str], list[str]]:
    return validate_crops(doc)


def v_soil(record: dict) -> tuple[list[str], list[str]]:
    errors, warns = [], []
    if not isinstance(record, dict):
        errors.append("V-SOIL-001 not a dict")
        return errors, warns
    if record.get("spatial_representation") == "gridded":
        warns.append("soil_gridded_not_field_test")
    fields = record.get("fields", {}) or {}
    for name, obj in fields.items():
        if not isinstance(obj, dict):
            errors.append(f"V-SOIL-002 {name} not an object")
            continue
        if obj.get("status") not in {
            "verified", "extracted", "general_fact", "placeholder", "missing", "farmer",
        }:
            errors.append(f"V-SOIL-002 {name} bad status")
    return errors, warns


def v_all(data_dir: Path) -> dict:
    from pathlib import Path as _P
    data_dir = _P(data_dir)
    out = {}
    # crops
    cp = data_dir / "cleaned" / "crop_reference.yaml"
    if cp.is_file():
        import yaml
        doc = yaml.safe_load(cp.read_text(encoding="utf-8"))
        e, w = v_crops(doc)
        out["crops"] = (e, w)
    # climate
    cd = data_dir / "cleaned" / "climate_daily_31.04_31.38.csv"
    if cd.is_file():
        df = pd.read_csv(cd)
        e, w = v_power(df, list(df.columns))
        out["climate"] = (e, w)
    # soil
    sp = data_dir / "cleaned" / "soil_31.04_31.38.json"
    if sp.is_file():
        import json
        rec = json.loads(sp.read_text(encoding="utf-8"))
        e, w = v_soil(rec)
        out["soil"] = (e, w)
    return out
