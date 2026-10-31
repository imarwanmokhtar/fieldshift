"""MODIS MOD13Q1 vegetation-index context loader for local extracts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

SOURCE_URL = "https://doi.org/10.5067/MODIS/MOD13Q1.061"
SCALE_FACTOR = 0.0001
FILL_VALUE = -3000
VALID_MIN = -2000
VALID_MAX = 10000
REQUIRED_COLUMNS = {
    "observation_date",
    "ndvi",
    "evi",
    "pixel_quality",
    "product_id",
    "product_version",
    "scale_factor",
    "retrieved",
}


def validate_modis(frame: pd.DataFrame) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        errors.append("missing columns: " + ", ".join(missing))
        return errors, warnings
    dates = pd.to_datetime(frame.observation_date, errors="coerce")
    if dates.isna().any():
        errors.append("invalid observation_date")
    if frame.observation_date.duplicated().any():
        errors.append("duplicate 16-day composite observations")
    quality = pd.to_numeric(frame.pixel_quality, errors="coerce")
    if quality.isna().any() or not quality.dropna().isin([0, 1, 2, 3]).all():
        errors.append("pixel_quality must preserve MOD13Q1 reliability codes 0..3")
    factors = pd.to_numeric(frame.scale_factor, errors="coerce")
    if factors.isna().any() or not factors.eq(SCALE_FACTOR).all():
        errors.append("scale_factor must be the product value 0.0001")
    for field in ("ndvi", "evi"):
        values = pd.to_numeric(frame[field], errors="coerce")
        bad = values.notna() & values.ne(FILL_VALUE) & ~values.between(VALID_MIN, VALID_MAX)
        if bad.any():
            errors.append(f"{field} is outside the MOD13Q1 valid raw range")
        if values.eq(FILL_VALUE).any():
            warnings.append(f"{field} contains fill values; they will be excluded")
    if (quality > 0).any():
        warnings.append("marginal, snow/ice, or cloudy pixels will be excluded")
    if (
        frame.product_version.isna().any()
        or (frame.product_version.astype(str).str.strip() == "").any()
    ):
        errors.append("product_version must be recorded")
    if not frame.product_id.astype(str).eq("MOD13Q1.061").all():
        errors.append("product_id must be MOD13Q1.061")
    if not frame.product_version.astype(str).eq("061").all():
        errors.append("product_version must be 061")
    if pd.to_datetime(frame["retrieved"], errors="coerce").isna().any():
        errors.append("retrieved must be a valid retrieval date")
    return errors, warnings


def load_modis(path: Path | str) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"product_id": str, "product_version": str})
    errors, _ = validate_modis(frame)
    if errors:
        raise ValueError("Invalid MODIS context file: " + "; ".join(errors))
    frame["observation_date"] = pd.to_datetime(frame.observation_date).dt.strftime("%Y-%m-%d")
    for field in ("ndvi", "evi"):
        raw = pd.to_numeric(frame[field], errors="coerce")
        frame[field] = (raw * SCALE_FACTOR).where(raw.between(VALID_MIN, VALID_MAX))
    frame["pixel_quality"] = pd.to_numeric(frame.pixel_quality, errors="coerce").astype("Int64")
    return frame.sort_values("observation_date").reset_index(drop=True)


def summarize_modis(frame: pd.DataFrame, period: str | None = None) -> dict:
    """Return monthly medians from best-reliability pixels without filling gaps."""
    work = frame.copy()
    work["date"] = pd.to_datetime(work.observation_date, errors="coerce")
    if period:
        start, end = period.split("-", maxsplit=1)
        work = work[work.date.dt.year.between(int(start), int(end))]
    good = work[
        pd.to_numeric(work.pixel_quality, errors="coerce").eq(0)
        & pd.to_numeric(work.ndvi, errors="coerce").notna()
        & pd.to_numeric(work.evi, errors="coerce").notna()
    ].copy()
    if len(good):
        good["month"] = good.date.dt.month
        monthly = [
            {
                "month": int(month),
                "ndvi_median": round(float(group.ndvi.median()), 4),
                "evi_median": round(float(group.evi.median()), 4),
                "n_observations": len(group),
            }
            for month, group in good.groupby("month", sort=True)
        ]
    else:
        monthly = []
    return {
        "status": "available" if not good.empty else "no_usable_observations",
        "dataset": "MODIS MOD13Q1.061 Terra Vegetation Indices",
        "product_id": "MOD13Q1.061",
        "product_version": str(work.product_version.iloc[0]) if len(work) else None,
        "retrieved": str(work.retrieved.iloc[0]) if len(work) else None,
        "spatial_resolution_m": 250,
        "temporal_resolution_days": 16,
        "spatial_type": "gridded pixel; mixed land covers may occur",
        "unit": "unitless vegetation index",
        "scale_factor": SCALE_FACTOR,
        "period": (f"{good.date.min():%Y-%m-%d}/{good.date.max():%Y-%m-%d}" if len(good) else None),
        "valid_observations": len(good),
        "excluded_observations": int(len(work) - len(good)),
        "monthly": monthly,
        "quality_flags": {
            "pixel_reliability_codes": sorted(
                pd.to_numeric(work.pixel_quality, errors="coerce")
                .dropna()
                .unique()
                .astype(int)
                .tolist()
            ),
            "pixel_reliability_counts": {
                str(int(flag)): int(count)
                for flag, count in pd.to_numeric(work.pixel_quality, errors="coerce")
                .value_counts()
                .items()
            },
        }
        if len(work)
        else {},
        "caveat": (
            "Greenness is not a direct measure of soil health; 250 m pixels can mix "
            "fields and other land cover."
        ),
    }
