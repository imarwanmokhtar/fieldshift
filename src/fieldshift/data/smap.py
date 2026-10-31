"""SMAP soil-moisture context loader for standardized local extracts.

This module does not download data or decode HDF5 flags. The local extract must
preserve the product flag and provide its product-specific quality interpretation.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

SOURCE_URL = "https://nsidc.org/data/spl3smp_e/versions/6"
REQUIRED_COLUMNS = {
    "observation_date",
    "soil_moisture",
    "quality_flag",
    "quality_status",
    "product_id",
    "spatial_resolution_km",
    "product_version",
    "retrieved",
}
GOOD_QUALITY = {"good", "recommended"}


def validate_smap(frame: pd.DataFrame) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        errors.append("missing columns: " + ", ".join(missing))
        return errors, warnings
    dates = pd.to_datetime(frame["observation_date"], errors="coerce")
    if dates.isna().any():
        errors.append("invalid observation_date")
    if frame["observation_date"].duplicated().any():
        errors.append("duplicate daily observations")
    values = pd.to_numeric(frame["soil_moisture"], errors="coerce")
    if values.isna().any():
        warnings.append("soil_moisture contains missing or non-numeric values")
    if ((values.dropna() < 0) | (values.dropna() > 1)).any():
        errors.append("soil_moisture must be volumetric fraction in 0..1 m³/m³")
    resolution = pd.to_numeric(frame["spatial_resolution_km"], errors="coerce")
    if resolution.isna().any() or (resolution <= 0).any():
        errors.append("spatial_resolution_km must be a positive number")
    if (
        frame["product_version"].isna().any()
        or (frame["product_version"].astype(str).str.strip() == "").any()
    ):
        errors.append("product_version must be recorded")
    if not frame["product_id"].astype(str).eq("SPL3SMP_E").all():
        errors.append("product_id must be SPL3SMP_E")
    versions = (
        frame["product_version"]
        .astype(str)
        .str.lower()
        .str.replace("version ", "", regex=False)
        .str.removeprefix("v")
    )
    if not versions.isin({"6", "006"}).all():
        errors.append("this panel accepts SMAP SPL3SMP_E Version 6 only")
    if not resolution.eq(9).all():
        errors.append("SPL3SMP_E Version 6 resolution must be recorded as 9 km")
    if pd.to_datetime(frame["retrieved"], errors="coerce").isna().any():
        errors.append("retrieved must be a valid retrieval date")
    statuses = frame["quality_status"].astype(str).str.lower()
    if not statuses.isin(GOOD_QUALITY | {"uncertain", "bad", "missing"}).all():
        errors.append("quality_status must be good, recommended, uncertain, bad, or missing")
    if statuses.isin({"uncertain", "bad", "missing"}).any():
        warnings.append("some retrievals are not recommended quality and will be excluded")
    if not frame["quality_flag"].notna().all():
        warnings.append("some product-specific quality flags are missing")
    return errors, warnings


def load_smap(path: Path | str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    errors, _ = validate_smap(frame)
    if errors:
        raise ValueError("Invalid SMAP context file: " + "; ".join(errors))
    frame["observation_date"] = pd.to_datetime(frame["observation_date"]).dt.strftime("%Y-%m-%d")
    frame["soil_moisture"] = pd.to_numeric(frame["soil_moisture"], errors="coerce")
    frame["quality_status"] = frame["quality_status"].astype(str).str.lower()
    return frame.sort_values("observation_date").reset_index(drop=True)


def summarize_smap(frame: pd.DataFrame, period: str | None = None) -> dict:
    """Summarize quality-screened surface moisture as regional context only."""
    work = frame.copy()
    work["date"] = pd.to_datetime(work["observation_date"], errors="coerce")
    if period:
        start, end = period.split("-", maxsplit=1)
        work = work[work.date.dt.year.between(int(start), int(end))]
    good = work[
        work["quality_status"].astype(str).str.lower().isin(GOOD_QUALITY)
        & pd.to_numeric(work["soil_moisture"], errors="coerce").notna()
    ].copy()
    good["soil_moisture"] = pd.to_numeric(good["soil_moisture"], errors="coerce")
    monthly = []
    if not good.empty:
        good["month"] = good.date.dt.to_period("M").astype(str)
        monthly = [
            {
                "month": key,
                "median": round(float(group.soil_moisture.median()), 4),
                "n_observations": len(group),
            }
            for key, group in good.groupby("month", sort=True)
        ]
    return {
        "status": "available" if not good.empty else "no_usable_observations",
        "dataset": "NASA SMAP Enhanced L3 Radiometer (SPL3SMP_E)",
        "product_id": "SPL3SMP_E",
        "product_version": str(work.product_version.iloc[0]) if len(work) else None,
        "retrieved": str(work.retrieved.iloc[0]) if len(work) else None,
        "spatial_resolution_km": (
            round(float(pd.to_numeric(work.spatial_resolution_km, errors="coerce").median()), 2)
            if len(work)
            else None
        ),
        "spatial_type": "gridded pixel; regional context, not field measurement",
        "unit": "m³/m³",
        "period": (f"{good.date.min():%Y-%m-%d}/{good.date.max():%Y-%m-%d}" if len(good) else None),
        "valid_observations": len(good),
        "excluded_observations": int(len(work) - len(good)),
        "monthly": monthly,
        "quality_flags": {
            "quality_status": sorted(work.quality_status.astype(str).str.lower().unique().tolist()),
            "product_flag_counts": {
                str(flag): int(count)
                for flag, count in work.quality_flag.value_counts(dropna=False).items()
            },
        }
        if len(work)
        else {},
        "caveat": (
            "Surface moisture is not root-zone water available to crops; "
            "a pixel may cover multiple fields."
        ),
    }
