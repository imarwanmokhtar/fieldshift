"""Profile-to-result orchestration for Phase 7."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

from . import __version__
from .analysis.evaluate import evaluate_rotation_set
from .analysis.explain import add_explanations
from .analysis.proposed import propose_candidate_strategies
from .analysis.rotation import expand_template, load_rules, load_templates
from .analysis.seasons import build_existing_sequence
from .data.crops import load_crop_table
from .data.crops import validate as validate_crops
from .data.modis import SOURCE_URL as MODIS_URL
from .data.modis import load_modis, summarize_modis
from .data.power import clean_power, parse_power, seasonal_summary
from .data.provenance import QualityFlag
from .data.smap import SOURCE_URL as SMAP_URL
from .data.smap import load_smap, summarize_smap
from .data.soil import load_soil, soil_path
from .data.validate import v_power, v_soil
from .i18n import text
from .models import Comparison, RunResult


def _profile(path: Path) -> tuple[dict, dict, list[str]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(text("result.profile_invalid"))
    answers = value.get("answers", value)
    if not isinstance(answers, dict):
        raise ValueError(text("result.profile_invalid"))
    return value, answers, list(value.get("flags", []))


def _location(a: dict) -> tuple[float, float]:
    if a.get("loc_mode") == "pilot":
        return 31.04, 31.38
    try:
        return float(a["lat"]), float(a["lon"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(text("result.profile_invalid")) from exc


def _crop_answer(answers: dict, key: str) -> str:
    value = answers.get(key)
    if value == "__other__":
        typed = str(answers.get(f"{key}_other") or "unknown crop").strip()
        return f"other_crop:{typed}"
    if value in (None, "__unknown__"):
        return "unreferenced_crop"
    return str(value)


def _period(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d{4})-(\d{4})", value)
    if not match or int(match.group(1)) >= int(match.group(2)):
        raise ValueError(text("result.period_invalid"))
    return int(match.group(1)), int(match.group(2))


def _climate(
    dd: Path, lat: float, lon: float, a: dict, period: str, fetch: bool, offline: bool
) -> tuple[pd.DataFrame, Path]:
    locid = f"{lat:.2f}_{lon:.2f}"
    path = dd / "cleaned" / f"climate_daily_{locid}.csv"
    start, end = _period(period)
    if not path.is_file():
        should_fetch = fetch or (not offline and a.get("data_mode") in ("fetch", "auto"))
        if not should_fetch:
            raise FileNotFoundError(text("result.fetch_required"))
        from .data.power import download_power

        raw, meta = download_power(lat, lon, f"{start}-01-01", f"{end}-12-31", dd / "raw" / "power")
        from .data.provenance import append_retrieval_log

        append_retrieval_log(
            dd / "metadata" / "retrieval_log.jsonl",
            source_id="NASA_POWER_DAILY",
            action="download",
            url=meta["url"],
            http_status=meta.get("http_status"),
            bytes_=meta.get("bytes"),
            file=str(raw.relative_to(dd)),
            sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),
            note=f"run climate fetch {lat},{lon} {start}..{end}",
        )
        frame = clean_power(parse_power(raw))
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)
    df = pd.read_csv(path)
    if "date" not in df:
        raise ValueError("Climate data is missing its date column.")
    dates = pd.to_datetime(df["date"], errors="coerce")
    df = df.loc[dates.dt.year.between(start, end)].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    if df.empty:
        raise ValueError(f"No climate rows are available for {period}.")
    return df.reset_index(drop=True), path


def _season_summary(df: pd.DataFrame, period: str) -> dict:
    summary = seasonal_summary(df)
    out = {}
    for slot in ("winter", "summer"):
        sub = summary[(summary.slot == slot) & summary.complete]

        def med(frame, key):
            values = pd.to_numeric(frame[key], errors="coerce").dropna()
            return round(float(values.median()), 1) if len(values) else None

        out[slot] = {
            "label": slot.title(),
            "t_mean_c": med(sub, "t_mean_c"),
            "t_min_c": med(sub, "t_min_abs_c"),
            "t_max_c": med(sub, "t_max_abs_c"),
            "rain_total_mm": med(sub, "rain_total_mm"),
            "heat_days": med(sub, "hot_days_tmax_ge_35"),
            "cold_days": med(sub, "cold_days_tmin_le_5"),
            "frost_days": med(sub, "frost_days_tmin_le_0"),
            "n_complete_windows": len(sub),
            "period": period,
        }
    out["n_complete_windows"] = {
        slot: out[slot]["n_complete_windows"] for slot in ("winter", "summer")
    }
    return out


def _source_records(
    dd: Path, period: str, climate_path: Path, crop_table, crop_ids: set[str], soil: dict
) -> list[dict]:
    sources = {}
    csv_path = dd / "metadata" / "sources.csv"
    if csv_path.is_file():
        with csv_path.open(encoding="utf-8", newline="") as fh:
            sources = {row.get("source_id"): row for row in csv.DictReader(fh)}
    ids = {
        obj.get("src")
        for crop in crop_table.crops
        if crop.get("crop_id") in crop_ids
        for obj in crop.values()
        if isinstance(obj, dict) and obj.get("src")
    }
    ids.update(
        obj.get("src")
        for obj in soil.get("fields", {}).values()
        if isinstance(obj, dict) and obj.get("src")
    )
    power = sources.get("NASA_POWER_DAILY", {})
    records = [
        {
            "id": "NASA_POWER_DAILY",
            "name": power.get("source_name", "NASA POWER daily"),
            "url": power.get("url", "https://power.larc.nasa.gov/"),
            "version": power.get("dataset_version"),
            "retrieved": power.get("retrieved"),
            "period": period,
            "resolution": power.get("spatial_resolution"),
            "spatial_type": power.get("spatial_type", "gridded"),
            "units": {"temperature": "°C", "rain": "mm/day", "solar": "MJ/m²/day"},
            "missing_value_rule": power.get("missing_value_rule", "Missing days are not filled"),
            "status": "extracted",
            "file": str(climate_path),
        }
    ]
    for sid in sorted(ids - {None, "NASA_POWER_DAILY"}):
        row = sources.get(sid, {})
        records.append(
            {
                "id": sid,
                "name": row.get("source_name", sid),
                "url": row.get("url", ""),
                "version": row.get("dataset_version"),
                "retrieved": row.get("retrieved"),
                "period": row.get("coverage_start", "reference"),
                "resolution": row.get("spatial_resolution"),
                "spatial_type": row.get("spatial_type", "non-spatial reference"),
                "units": row.get("units"),
                "missing_value_rule": row.get("missing_value_rule"),
                "status": "extracted",
            }
        )
    return records


def _crop_rows(crop_table, ids: set[str]) -> list[dict]:
    out = []
    for crop in crop_table.crops:
        cid = crop.get("crop_id")
        if cid not in ids:
            continue
        fields = {
            key: {k: value for k, value in obj.items() if k in ("v", "unit", "src", "status")}
            for key, obj in crop.items()
            if isinstance(obj, dict) and "status" in obj
        }
        names = crop.get("names") or {}
        out.append(
            {
                "crop_id": cid,
                "name": names.get("en", cid) if isinstance(names, dict) else cid,
                "fields": fields,
            }
        )
    return out


def _optional_context(dd: Path, locid: str, period: str) -> tuple[dict, list[dict], list[str]]:
    panels = {}
    sources = []
    flags = []
    specs = (
        (
            "smap",
            dd / "cleaned" / f"smap_daily_{locid}.csv",
            load_smap,
            summarize_smap,
            "NSIDC_SMAP",
            "NASA SMAP Enhanced L3 Radiometer (SPL3SMP_E)",
            "Version 6 · 9 km",
            "9 km",
            SMAP_URL,
            "m³/m³; soil moisture is surface context, not root-zone water",
        ),
        (
            "modis",
            dd / "cleaned" / f"modis_mod13q1_{locid}.csv",
            load_modis,
            summarize_modis,
            "MODIS_MOD13Q1",
            "MODIS MOD13Q1.061 Terra Vegetation Indices",
            "Version 061 · 250 m · 16-day composites",
            "250 m",
            MODIS_URL,
            "unitless NDVI/EVI; 0.0001 scale factor applied",
        ),
    )
    for key, path, loader, summarize, source_id, name, version, resolution, url, units in specs:
        if not path.is_file():
            panels[key] = {
                "status": "not_provided",
                "dataset": name,
                "period": None,
                "monthly": [],
                "valid_observations": 0,
                "excluded_observations": 0,
                "quality_flags": [],
                "caveat": "Optional context file not supplied; core analysis is unchanged.",
            }
            sources.append(
                {
                    "id": source_id,
                    "name": name,
                    "url": url,
                    "version": version,
                    "retrieved": None,
                    "period": None,
                    "resolution": resolution,
                    "spatial_type": "gridded context",
                    "units": units,
                    "missing_value_rule": "Quality-screened; missing observations are not filled.",
                    "status": "missing",
                    "file": None,
                }
            )
            continue
        try:
            frame = loader(path)
            panel = summarize(frame, period)
            panels[key] = panel
            sources.append(
                {
                    "id": source_id,
                    "name": name,
                    "url": url,
                    "version": panel.get("product_version") or version,
                    "retrieved": panel.get("retrieved"),
                    "period": panel.get("period"),
                    "resolution": (
                        f"{panel.get('spatial_resolution_km')} km" if key == "smap" else resolution
                    ),
                    "spatial_type": panel.get("spatial_type", "gridded context"),
                    "units": units,
                    "missing_value_rule": (
                        "Product quality fields retained; rejected observations excluded; "
                        "no gap filling."
                    ),
                    "status": "extracted",
                    "file": str(path),
                }
            )
            if panel.get("status") != "available":
                flags.append(f"{key}_no_usable_observations")
        except Exception as exc:
            panels[key] = {
                "status": "invalid",
                "dataset": name,
                "period": None,
                "monthly": [],
                "valid_observations": 0,
                "excluded_observations": 0,
                "quality_flags": [str(exc)],
                "caveat": "This optional file was excluded; core analysis is unchanged.",
            }
            sources.append(
                {
                    "id": source_id,
                    "name": name,
                    "url": url,
                    "version": version,
                    "retrieved": None,
                    "period": None,
                    "resolution": resolution,
                    "spatial_type": "gridded context",
                    "units": units,
                    "missing_value_rule": "Invalid file excluded from the context panel.",
                    "status": "missing",
                    "file": str(path),
                }
            )
            flags.append(f"{key}_invalid")
    return panels, sources, flags


def build_result(
    profile_path: Path | str,
    data_dir: Path | str,
    period: str | None = None,
    fetch: bool = False,
    offline: bool = False,
    run_id: str | None = None,
) -> RunResult:
    ppath, dd = Path(profile_path), Path(data_dir)
    original, a, wizard_flags = _profile(ppath)
    lat, lon = _location(a)
    selected_period = period or a.get("period", "2020-2025")
    start_year, end_year = _period(selected_period)
    crop_path = dd / "cleaned" / "crop_reference.yaml"
    if not crop_path.is_file():
        raise FileNotFoundError(text("result.crop_data_required"))
    crop_table = load_crop_table(crop_path)
    crop_errors, crop_warnings = validate_crops(crop_table.doc)
    if crop_errors:
        raise ValueError(text("result.crop_data_required") + " " + "; ".join(crop_errors[:4]))
    climate, climate_path = _climate(dd, lat, lon, a, selected_period, fetch, offline)
    climate_errors, climate_warnings = v_power(climate, list(climate.columns), lat=lat, lon=lon)
    if climate_errors:
        raise ValueError("Climate data failed validation: " + "; ".join(climate_errors))
    locid = f"{lat:.2f}_{lon:.2f}"
    soil = load_soil(soil_path(dd, locid)) or {
        "schema_version": 1,
        "location_id": locid,
        "fields": {},
    }
    soil_errors, soil_warnings = v_soil(soil)
    if soil_errors:
        raise ValueError("Soil data failed validation: " + "; ".join(soil_errors))
    horizon = int(a.get("horizon", 1))
    prev = _crop_answer(a, "prev_crop")
    other = _crop_answer(a, "existing_other_crop")
    if a.get("existing_edit") is False:
        winter = _crop_answer(a, "existing_winter_crop")
        summer = _crop_answer(a, "existing_summer_crop")
        existing = [
            {
                "slot": slot,
                "year": y,
                "crop_id": cid,
            }
            for y in range(1, horizon + 1)
            for slot, cid in (("winter", winter), ("summer", summer))
        ]
    else:
        season = a.get("prev_season", "unknown")
        existing = build_existing_sequence(prev, season, other, horizon)
    templates = load_templates(dd / "references" / "rotation_templates.yaml")
    rules = load_rules(dd / "references" / "rotation_rules.yaml")
    bands_path = Path(__file__).parent.parent.parent / "config" / "bands.yaml"
    thresholds_path = Path(__file__).parent.parent.parent / "config" / "thresholds.yaml"
    bands = yaml.safe_load(bands_path.read_text()) if bands_path.is_file() else {}
    thresholds = yaml.safe_load(thresholds_path.read_text()) if thresholds_path.is_file() else {}

    ranks = a.get("prio_rank_list") or original.get("chosen_priorities") or []
    ranks = [
        value
        for value in ranks
        if value
        in (
            "reduce_water_use",
            "support_soil_health",
            "improve_climate_resilience",
            "maintain_productivity",
        )
    ]
    skipped = []
    if a.get("budget_market", "none") != "none":
        skipped.append("budget_market")

    alternatives = []
    strat_source = a.get("strat_source", "templates")
    if strat_source == "templates":
        for tid in a.get("templates", []):
            tpl = next((item for item in templates if item.get("id") == tid), None)
            if tpl is None:
                raise ValueError(f"Unknown strategy template: {tid}")
            alternatives.append(
                {
                    "id": tid,
                    "name": (tpl.get("name") or {}).get("en", tid),
                    "kind": "template",
                    "sequence": expand_template(tpl, horizon),
                }
            )
    elif strat_source == "custom":
        for i in (1, 2):
            seq = [
                {
                    "slot": slot,
                    "year": y,
                    "crop_id": _crop_answer(a, f"custom_{slot}_{i}"),
                }
                for y in range(1, horizon + 1)
                for slot in ("winter", "summer")
            ]
            alternatives.append(
                {
                    "id": f"custom-{i}",
                    "name": a.get(f"custom_name_{i}") or f"Custom strategy {i}",
                    "kind": "custom",
                    "sequence": seq,
                }
            )
    elif strat_source == "proposed":
        alternatives = propose_candidate_strategies(
            crop_table=crop_table,
            existing_sequence=existing,
            horizon=horizon,
            daily_climate=climate,
            soil_record=soil,
            latitude=lat,
            ranked_priorities=ranks,
            skipped_priorities=skipped,
            water_availability=a.get("water_avail", "unknown"),
            rules=rules,
            thresholds=thresholds,
            bands=bands,
            max_candidates=3,
        )
    else:
        raise ValueError(
            f"Unknown strategy source: {strat_source}; choose templates, custom, or proposed."
        )
    if len(alternatives) < 2:
        raise ValueError("Choose at least two alternative strategies to compare.")
    flags = list(wizard_flags)
    if end_year - start_year + 1 < 15:
        flags.append("climate_short_record")
    if soil.get("spatial_representation") == "gridded" and soil.get("fields"):
        flags.append("soil_regional_only")
    if a.get("loc_mode") == "pilot" and not a.get("coords_real"):
        flags.append("coordinates_illustrative")
    if not a.get("existing_edit", True):
        flags.append("baseline_assumed")
    if a.get("prev_crop") == "__unknown__":
        flags.append("history_unknown")
    if a.get("prev_season") == "unknown":
        flags.append("season_unknown")
    if a.get("irrigation") == "unknown" or a.get("water_avail") == "unknown":
        flags.append("irrigation_unknown")
    if lat < 22 or lat > 32 or lon < 25 or lon > 37:
        flags.append("outside_egypt")
    evaluated = evaluate_rotation_set(
        climate,
        crop_table,
        soil,
        lat,
        existing,
        alternatives,
        ranked_priorities=ranks,
        skipped_priorities=skipped,
        water_availability=a.get("water_avail", "unknown"),
        rules=rules,
        thresholds=thresholds,
        bands=bands,
        flags=flags,
        horizon=horizon,
        baseline_assumed=not a.get("existing_edit", True),
    )
    explained = add_explanations(evaluated["strategies"], templates, selected_period)
    used_ids = {step.crop_id for strategy in explained for step in strategy.sequence}
    validation_codes = []
    for warning in climate_warnings:
        if "climate_missing_values" in warning:
            validation_codes.append("climate_missing_values")
        elif "out_of_range" in warning:
            validation_codes.append("climate_out_of_range")
    for warning in soil_warnings:
        if "gridded" in warning:
            validation_codes.append("soil_regional_only")
    quality_codes = set(flags + validation_codes + crop_warnings)
    quality_codes.update(flag for s in explained for flag in s.flags)
    optional_context, optional_sources, optional_flags = _optional_context(
        dd, locid, selected_period
    )
    quality_codes.update(optional_flags)
    quality = [
        QualityFlag(
            code=code,
            text_key=f"flag.{code}" if text(f"flag.{code}") != f"flag.{code}" else "flag.generic",
        )
        for code in sorted(quality_codes)
    ]
    sources = _source_records(dd, selected_period, climate_path, crop_table, used_ids, soil)
    sources.extend(optional_sources)
    raw_sha = None
    raw_dir = dd / "raw" / "power"
    if raw_dir.is_dir():
        candidates = sorted(raw_dir.glob(f"power_{locid}_*.csv"))
        if candidates:
            raw_sha = hashlib.sha256(candidates[-1].read_bytes()).hexdigest()
    clean_profile = {k: v for k, v in a.items() if not k.startswith("_") and k not in ("loc_name",)}
    clean_profile.update(
        {"latitude": lat, "longitude": lon, "period": selected_period, "raw_sha256": raw_sha}
    )
    comparison = evaluated["comparison"]
    return RunResult(
        engine_version=__version__,
        run_id=run_id or datetime.now().strftime("%Y%m%d-%H%M%S"),
        profile=clean_profile,
        data_sources=sources,
        quality_flags=quality,
        climate_summary=_season_summary(climate, selected_period),
        optional_context=optional_context,
        crops_used=_crop_rows(crop_table, used_ids),
        strategies=explained,
        comparison=Comparison(
            order=comparison["order"],
            too_close=comparison["too_close"],
            order_equal_weights=comparison["order_equal_weights"],
            ranking_stable=comparison["ranking_stable"],
            priority_sensitivity=comparison.get("priority_sensitivity"),
        ),
        limitations=[text(f"result.methodology.{i}") for i in range(1, 6)],
        local_review=[text(f"result.local_review.{i}") for i in range(1, 4)],
    )
