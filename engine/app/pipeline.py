"""run_analysis(): orchestrates the whole pipeline (guide steps 1-7)."""

from __future__ import annotations

import logging
from typing import Any, Callable

from . import db
from .data import field_layers
from .data import ndvi as ndvi_client
from .data.ndvi import NdviSeries
from .data import raster
from .data.power import apply_scenario, load_climate
from .evidence import build_pack
from .features import CROPS, climate_features, ndvi_features
from .llm import narrate
from .profile import ProfileError, parse_profile
from .settings import settings
from .schemas import EvidencePack, NarrativeOut, Strategy
from .strategies import build_context, score_choice, select_strategies

log = logging.getLogger(__name__)


# Progress stages, in order. The results page shows one step per stage.
STAGES = ("reading_profile", "collecting_satellite", "fetching_climate", "computing_climate", "satellite_layers",
          "scoring", "evidence", "writing", "saving")


def _report(on_stage: Callable[[str], None] | None, stage: str) -> None:
    """Report progress. A failed progress update must never fail the analysis."""
    if not on_stage:
        return
    try:
        on_stage(stage)
    except Exception:
        log.warning("could not report stage %s", stage, exc_info=True)


def _ndvi_from_layers(feats: dict[str, Any] | None) -> NdviSeries | None:
    """Field NDVI from NASA AppEEARS: HLS 30 m first, MODIS 250 m as the backup."""
    import pandas as pd
    for key, source in (("ndvi_hls", "hls"), ("ndvi_modis", "modis")):
        s = (feats or {}).get(key)
        if s and len(s.get("values", [])) >= 10:
            idx = pd.to_datetime(s["dates"])
            return NdviSeries(series=pd.Series(s["values"], index=idx, dtype=float),
                              interpolated=pd.Series(s["interpolated"], index=idx, dtype=bool), source=source)
    return None


def _gather(profile, scenario: dict[str, float], on_stage: Callable[[str], None] | None = None,
            layers: dict[str, Any] | None = None):
    _report(on_stage, "fetching_climate")
    climate = load_climate(profile.lat, profile.lng)
    _report(on_stage, "computing_climate")
    df = apply_scenario(climate.df, scenario.get("temp_delta_c", 0.0), scenario.get("rain_factor", 1.0))
    clim = climate_features(df, profile.lat, (layers or {}).get("elevation_m"))

    used, mocked, unavailable = [], [], []
    _report(on_stage, "satellite_layers")
    (used if climate.source == "nasa_power" else unavailable).append("nasa_power")

    nd = _ndvi_from_layers(layers)
    if nd is not None:
        used.append(f"{nd.source}_ndvi")
    else:
        nd = ndvi_client.fetch_ndvi(profile.lat, profile.lng)
        if nd is None:
            unavailable.append("satellite_ndvi")
        elif nd.source == "mock":
            mocked.append("sentinel2_ndvi")
        else:
            used.append("sentinel2_ndvi")
    nfeat = ndvi_features(nd) if nd is not None else None
    for key, name in (("et_modis", "modis_et"), ("et_ecostress", "ecostress_et"), ("smap", "smap"), ("elevation_m", "srtm")):
        if (layers or {}).get(key) is not None:
            used.append(name)

    gaez = {}
    for cid in CROPS:
        v = raster.gaez_suitability(cid, profile.lat, profile.lng)
        if v is not None:
            gaez[cid] = v
    if gaez:
        used.append("gaez")
    else:
        unavailable.append("gaez (using approximate values from crops.json)")

    for name, fn in (("smap", raster.smap_anomaly), ("imerg", raster.imerg_trend)):
        if name == "smap" and "smap" in used:
            continue                                      # SMAP already came from AppEEARS
        _, src = fn(profile.lat, profile.lng)
        {"mock": mocked, "unavailable": unavailable}.get(src, used).append(name)
    return climate, clim, nfeat, gaez, used, mocked, unavailable


def analyze_answers(answers: dict[str, Any], lang: str = "en",
                    scenario: dict[str, float] | None = None,
                    on_stage: Callable[[str], None] | None = None,
                    layers: tuple[dict[str, Any] | None, str, list] | None = None) -> tuple[EvidencePack, NarrativeOut]:
    """Pure analysis: answers in, evidence pack and narrative out. No database access.

    `layers` = (features, state, sources) from data.field_layers.for_analysis (NASA AppEEARS)."""
    feats, layer_state, layer_sources = layers or (None, "unavailable", [])
    scenario = {"temp_delta_c": float((scenario or {}).get("temp_delta_c", 0.0)),
                "rain_factor": float((scenario or {}).get("rain_factor", 1.0))}
    profile = parse_profile(answers)
    climate, clim, nfeat, gaez, used, mocked, unavailable = _gather(profile, scenario, on_stage, feats)
    _report(on_stage, "scoring")
    ctx = build_context(profile, clim, gaez=gaez, gaez_source="gaez" if gaez else "approx")
    strategies, recommended = select_strategies(ctx)
    _report(on_stage, "evidence")
    pack = build_pack(ctx, climate, clim, strategies, recommended, nfeat, used, mocked, unavailable, scenario,
                      layers={"features": feats or {}, "state": layer_state, "sources": layer_sources})
    _report(on_stage, "writing")
    return pack, narrate(pack, lang)


def compare_choice(answers: dict[str, Any], crop: str, season: str | None = None) -> dict[str, Any]:
    """'Farmer picked another crop': same scoring, side by side with current and the best option."""
    profile = parse_profile(answers)
    climate, clim, nfeat, gaez, used, mocked, unavailable = _gather(profile, {})
    ctx = build_context(profile, clim, gaez=gaez)
    strategies, recommended = select_strategies(ctx)
    choice: Strategy = score_choice(ctx, crop, season)
    by_id = {s.id: s for s in strategies}
    current, best = by_id["current"], by_id[recommended]
    criteria = list(choice.scores)
    return {
        "choice": choice.model_dump(),
        "current": current.model_dump(),
        "recommended": best.model_dump(),
        "delta_vs_current": {k: choice.scores[k] - current.scores[k] for k in criteria},
        "delta_vs_recommended": {k: choice.scores[k] - best.scores[k] for k in criteria},
        "climate_source": climate.source,
    }


def run_analysis(analysis_id: str, user_id: str, lang: str | None = None) -> None:
    """Background task: mark running, load profile, analyse, save. Never raises."""
    try:
        row = db.get_analysis(analysis_id)
        if not row or row.get("user_id") != user_id:
            log.error("analysis %s not found for user", analysis_id)
            return
        lang = lang or row.get("lang") or "ar"
        db.update_analysis(analysis_id, status="running", stage="reading_profile", error=None)

        profile_row = db.get_profile(user_id)
        if not profile_row or profile_row.get("user_id") != user_id:
            raise ProfileError("Farm setup not found. Please finish the onboarding questions.")

        scenario = row.get("scenario") or None
        answers = profile_row.get("answers") or {}
        layers = None
        try:
            p = parse_profile(answers)
            _report(lambda st: db.update_analysis(analysis_id, stage=st), "collecting_satellite")
            layers = field_layers.for_analysis(user_id, p.lat, p.lng, budget_s=settings.LAYERS_BUDGET_S)
        except ProfileError:
            pass                                          # analyze_answers raises the same error with a clear message
        pack, narrative = analyze_answers(answers, lang, scenario, layers=layers,
                                          on_stage=lambda st: db.update_analysis(analysis_id, stage=st))
        _report(lambda st: db.update_analysis(analysis_id, stage=st), "saving")

        db.update_analysis(analysis_id, status="done", stage="done",
                           result=pack.model_dump(mode="json"), narrative=narrative.model_dump(mode="json"))
    except ProfileError as exc:
        _fail(analysis_id, str(exc))
    except Exception as exc:
        log.exception("analysis %s failed", analysis_id)
        _fail(analysis_id, f"The analysis could not be completed ({type(exc).__name__}). Please try again.")


def _fail(analysis_id: str, message: str) -> None:
    try:
        db.update_analysis(analysis_id, status="failed", stage="failed", error=message[:500])
    except Exception:
        log.exception("could not mark analysis %s as failed", analysis_id)
