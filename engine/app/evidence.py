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
                   mocked: list[str], history_assumed: bool) -> tuple[str, int]:
    score = 90
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
    if history_assumed:
        score -= 10
    score = max(5, min(95, score))
    level = "high" if score >= 70 else "medium" if score >= 45 else "low"
    return level, score


def build_pack(ctx: Context, climate: ClimateData, clim: ClimateFeatures, strategies: list[Strategy],
               recommended_id: str, ndvi: NdviFeatures | None, layers_used: list[str], layers_mocked: list[str],
               layers_unavailable: list[str], scenario: dict[str, float]) -> EvidencePack:
    p = ctx.profile
    notes: list[Fact] = []
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
    shared_gaps.append(fact("crop_values_unverified"))
    shared_gaps.append(fact("income_rough"))

    history_assumed = any(n.code == "history_assumed" for n in ctx.history_notes)
    for st in strategies:
        st.gaps = shared_gaps + st.gaps
        if ndvi is not None and st.kind == "current":
            st.evidence.append(fact("ndvi_bare", days=int(ndvi.bare_days_per_year)))
        st.confidence, st.confidence_score = confidence_for(  # type: ignore[assignment]
            st, p, climate.source, ndvi, layers_mocked, history_assumed and st.kind == "current")

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
