"""Builds the evidence pack: the single JSON document the UI shows and the LLM explains."""

from __future__ import annotations

from .data.power import ClimateData
from .features import ClimateFeatures, NdviFeatures
from .schemas import DataQuality, EvidencePack, Fact, FarmProfile, Strategy
from .strategies import Context
from .texts import fact

# Answers whose absence really matters for the result get a bigger confidence cut.
KEY_ANSWERS = {"last_crop", "prev_crop", "irrigation_method", "water_reliability", "salinity", "soil_texture"}


def confidence_for(st: Strategy, profile: FarmProfile, climate_source: str, ndvi: NdviFeatures | None,
                   mocked: list[str], history_assumed: bool, et_check: int = 0) -> tuple[str, int]:
    """`et_check`: +1 when satellite-observed water use agrees with our estimate, -1 when it does not."""
    score = 90 + 5 * et_check
    for q in profile.unknown_answers:
        score -= 5 if q in KEY_ANSWERS else 2
    if climate_source != "nasa_power":
        score -= 25
    if ndvi is None:
        score -= 5
    elif ndvi.interpolated_share > 0.3:
        score -= 5
    score -= 5 * len(mocked)
    score -= 10                                      # crop table not yet verified locally
    score -= 3 * sum(1 for r in st.risks if r.code == "new_crop")
    if st.practices:
        score -= 5                                   # practice water savings are general ranges, not verified
    if history_assumed:
        score -= 10
    score = max(5, min(95, score))
    level = "high" if score >= 70 else "medium" if score >= 45 else "low"
    return level, score


ET_AGREE_PCT = 30          # model vs satellite water use within this % counts as agreement


def satellite_facts(ctx: Context, layers: dict) -> dict:
    """Facts from the NASA AppEEARS layers (HLS, MODIS, ECOSTRESS, SMAP, SRTM).

    These check the engine's answers against observations; they do not change scores.
    """
    feats = layers.get("features") or {}
    state = layers.get("state", "unavailable")
    notes: list[Fact] = []
    gaps: list[Fact] = []
    current_evidence: list[Fact] = []
    et_check = 0
    obs: dict = {"state": state, "sources": layers.get("sources") or []}

    if state in ("requested", "processing"):
        gaps.append(fact("layers_pending"))
    elif state == "failed":
        gaps.append(fact("layers_failed"))

    # Water: our modelled crop water use for the current rotation vs what satellites saw.
    model_mm = sum(ctx.metrics[c].etc_mm for c in ctx.current if c in ctx.metrics)
    et = feats.get("et_modis")
    if et and model_mm > 0 and et.get("mean_annual_mm"):
        sat_mm = float(et["mean_annual_mm"])
        diff = int(round((model_mm - sat_mm) / sat_mm * 100))
        current_evidence.append(fact("et_check_modis", sat=int(sat_mm), model=int(round(model_mm)),
                                     y0=et["years"][0], y1=et["years"][1]))
        if abs(diff) <= ET_AGREE_PCT:
            et_check = 1
            notes.append(fact("et_check_agrees", pct=abs(diff)))
        else:
            et_check = -1
            gaps.append(fact("et_check_differs", pct=abs(diff)))
        obs["et_check"] = {"model_mm_per_year": round(model_mm), "modis_mm_per_year": int(sat_mm),
                           "difference_pct": diff, "years": et["years"]}
    eco = feats.get("et_ecostress")
    if eco:
        notes.append(fact("ecostress_et", mm=eco["median_mm_day"], n=eco["n_obs"]))
        obs["ecostress"] = eco

    smap = feats.get("smap") or {}
    pct = smap.get("rootzone_pctl_last90")
    if pct is not None:
        code = "smap_dry" if pct < 20 else "smap_wet" if pct > 80 else "smap_normal"
        notes.append(fact(code, pct=int(pct)))
        obs["smap"] = smap

    if feats.get("elevation_m") is not None:
        notes.append(fact("elevation", m=int(feats["elevation_m"])))
        obs["elevation_m"] = feats["elevation_m"]

    # Standing water in summer (HLS NDWI > 0) is the usual signature of flooded rice.
    share = feats.get("flooded_summer_share")
    if share is not None:
        summer_crop = ctx.current[1]
        if summer_crop == "rice" and share < 0.1:
            gaps.append(fact("flood_not_seen"))
        elif summer_crop != "rice" and share >= 0.5:
            gaps.append(fact("flood_seen", crop=summer_crop))
        obs["flooded_summer_share"] = share

    return {"notes": notes, "gaps": gaps, "current_evidence": current_evidence,
            "et_check": et_check, "observations": obs}


def build_pack(ctx: Context, climate: ClimateData, clim: ClimateFeatures, strategies: list[Strategy],
               recommended_id: str, ndvi: NdviFeatures | None, layers_used: list[str], layers_mocked: list[str],
               layers_unavailable: list[str], scenario: dict[str, float],
               layers: dict | None = None) -> EvidencePack:
    p = ctx.profile
    notes: list[Fact] = []
    sat = satellite_facts(ctx, layers or {})
    notes.extend(sat["notes"])
    if climate.source == "nasa_power":
        notes.append(fact("note_climate_resolution"))
    else:
        notes.append(fact("note_fallback_heat"))
    if ndvi is not None and ndvi.interpolated_share > 0:
        notes.append(fact("note_interpolated", pct=int(round(ndvi.interpolated_share * 100))))
    if layers_mocked:
        notes.append(fact("note_mock_layers", layers=layers_mocked))
    if scenario.get("temp_delta_c") or scenario.get("rain_factor", 1.0) != 1.0:
        notes.append(fact("note_scenario", temp=scenario.get("temp_delta_c", 0.0),
                          rain=int(round(scenario.get("rain_factor", 1.0) * 100))))

    # Gaps shared by every strategy
    shared_gaps: list[Fact] = list(ctx.history_notes)
    unknown_display = [q for q in p.unknown_answers if q not in ("last_crop", "prev_crop")]
    if unknown_display:
        shared_gaps.append(fact("unknown_answers", items=unknown_display))
    if p.soil_test is None or not p.soil_test.has_test:
        shared_gaps.append(fact("no_soil_test"))
    if climate.source != "nasa_power":
        shared_gaps.append(fact("climate_fallback"))
    if ndvi is None:
        shared_gaps.append(fact("ndvi_unavailable"))
    else:
        if p.last_crop and p.last_crop.crop not in ("fallow",):
            season = p.last_crop.season
            seen = ndvi.winter_peak_last_season if season == "winter" else ndvi.summer_peak_last_season if season == "summer" else None
            if seen is False:
                shared_gaps.append(fact("ndvi_mismatch", season=season, crop=p.last_crop.crop))
    shared_gaps.extend(sat["gaps"])
    shared_gaps.append(fact("crop_values_unverified"))
    shared_gaps.append(fact("income_rough"))

    history_assumed = any(n.code == "history_assumed" for n in ctx.history_notes)
    for st in strategies:
        st.gaps = shared_gaps + st.gaps
        if ndvi is not None and st.kind == "current":
            st.evidence.append(fact("ndvi_bare", days=int(ndvi.bare_days_per_year)))
        if st.kind == "current":
            st.evidence.extend(sat["current_evidence"])
        st.confidence, st.confidence_score = confidence_for(  # type: ignore[assignment]
            st, p, climate.source, ndvi, layers_mocked, history_assumed and st.kind == "current", sat["et_check"])

    observations = {
        "climate_source": climate.source,
        "climate_years": [min(clim.years), max(clim.years)] if clim.years else [],
        "hot_days_per_year": {"threshold_c": 35, "mean": round(clim.hot_days_mean, 1),
                              "trend_per_year": round(clim.hot_days_trend_per_year, 2),
                              "by_year": clim.hot_days_per_year},
        "annual_mean_temp_c": round(clim.annual_mean_temp, 1),
        "temp_trend_c_per_decade": round(clim.temp_trend_per_decade, 2),
        "monthly_mean_temp_c": {m: round(v, 1) for m, v in clim.monthly_mean_temp.items()},
        "reference_et0_mm_per_year": round(clim.et0_annual_mm),
        "rain_mm_per_year": round(clim.rain_annual_mm),
        "rain_winter_mm": round(clim.rain_winter_mm),
        "rain_summer_mm": round(clim.rain_summer_mm),
        "crop_metrics": {cid: m.model_dump() for cid, m in ctx.metrics.items()},
        "satellite": sat["observations"],
    }
    if ndvi is not None:
        observations["ndvi"] = {"source": ndvi.source, "bare_field_days_per_year": ndvi.bare_days_per_year,
                                "peaks": ndvi.peaks[-6:], "interpolated_share": ndvi.interpolated_share}

    return EvidencePack(
        field={"lat": p.lat, "lng": p.lng, "area_feddan": round(p.area_feddan, 2), "area_ha": round(p.area_ha, 2),
               "name": p.field_name, "soil_texture": p.soil_texture, "irrigation_method": p.irrigation_method,
               "current_rotation": list(ctx.current)},
        farmer_priorities=p.priorities,
        weights=ctx.weights,
        scenario=scenario,
        data_quality=DataQuality(unknown_answers=p.unknown_answers, layers_used=layers_used,
                                 layers_mocked=layers_mocked, layers_unavailable=layers_unavailable, notes=notes),
        observations=observations,
        strategies=strategies,
        recommended_id=recommended_id,
    )
