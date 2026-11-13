"""run_analysis(): orchestrates the whole pipeline (guide steps 1-7)."""

from __future__ import annotations

import logging
from typing import Any, Callable

from . import db
from .data import ndvi as ndvi_client
from .data import raster
from .data.power import apply_scenario, load_climate
from .evidence import build_pack
from .features import CROPS, climate_features, ndvi_features
from .llm import narrate
from .profile import ProfileError, parse_profile
from .schemas import EvidencePack, NarrativeOut, Strategy
from .strategies import build_context, score_choice, select_strategies

log = logging.getLogger(__name__)


def _gather(profile, scenario: dict[str, float]):
    climate = load_climate(profile.lat, profile.lng)
    df = apply_scenario(climate.df, scenario.get("temp_delta_c", 0.0), scenario.get("rain_factor", 1.0))
    clim = climate_features(df, profile.lat)

    used, mocked, unavailable = [], [], []
    (used if climate.source == "nasa_power" else unavailable).append("nasa_power")

    nd = ndvi_client.fetch_ndvi(profile.lat, profile.lng)
    nfeat = ndvi_features(nd) if nd is not None else None
    if nd is None:
        unavailable.append("sentinel2_ndvi")
    elif nd.source == "mock":
        mocked.append("sentinel2_ndvi")
    else:
        used.append("sentinel2_ndvi")

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
        _, src = fn(profile.lat, profile.lng)
        {"mock": mocked, "unavailable": unavailable}.get(src, used).append(name)
    return climate, clim, nfeat, gaez, used, mocked, unavailable


def analyze_answers(answers: dict[str, Any], lang: str = "en",
                    scenario: dict[str, float] | None = None,
                    on_stage: Callable[[str], None] | None = None) -> tuple[EvidencePack, NarrativeOut]:
    """Pure analysis: answers in, evidence pack and narrative out. No database access."""
    scenario = {"temp_delta_c": float((scenario or {}).get("temp_delta_c", 0.0)),
                "rain_factor": float((scenario or {}).get("rain_factor", 1.0))}
    profile = parse_profile(answers)
    climate, clim, nfeat, gaez, used, mocked, unavailable = _gather(profile, scenario)
    ctx = build_context(profile, clim, gaez=gaez, gaez_source="gaez" if gaez else "approx")
    strategies, recommended = select_strategies(ctx)
    pack = build_pack(ctx, climate, clim, strategies, recommended, nfeat, used, mocked, unavailable, scenario)
    if on_stage:
        on_stage("writing")
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
        db.update_analysis(analysis_id, status="running", stage="reading_data", error=None)

        profile_row = db.get_profile(user_id)
        if not profile_row or profile_row.get("user_id") != user_id:
            raise ProfileError("Farm setup not found. Please finish the onboarding questions.")

        db.update_analysis(analysis_id, stage="comparing")
        scenario = row.get("scenario") or None
        pack, narrative = analyze_answers(profile_row.get("answers") or {}, lang, scenario,
                                          on_stage=lambda st: db.update_analysis(analysis_id, stage=st))

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
