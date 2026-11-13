"""FastAPI app. Only the Next.js server calls this (header X-API-Key); browsers never do."""

from __future__ import annotations

import hmac
import logging
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Response
from pydantic import BaseModel

from . import db
from .llm import model_name, provider
from .pipeline import compare_choice, run_analysis
from .profile import ProfileError
from .settings import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Field Shift engine", version="1.0.0")


def _check_key(x_api_key: str) -> None:
    if not settings.ENGINE_API_KEY or not hmac.compare_digest(x_api_key, settings.ENGINE_API_KEY):
        raise HTTPException(status_code=401, detail="bad key")


class AnalyzeRequest(BaseModel):
    analysis_id: str
    user_id: str
    lang: Literal["en", "ar"] | None = None


class CompareRequest(BaseModel):
    user_id: str
    crop: str
    season: Literal["winter", "summer"] | None = None


@app.post("/analyze", status_code=202)
def analyze(req: AnalyzeRequest, bg: BackgroundTasks, response: Response, x_api_key: str = Header(...)):
    _check_key(x_api_key)
    if getattr(settings, "ENGINE_SYNC", False):
        # Serverless: do the work now; the result is written to Supabase before we reply.
        run_analysis(req.analysis_id, req.user_id, req.lang)
        response.status_code = 200
        return {"status": "finished"}
    bg.add_task(run_analysis, req.analysis_id, req.user_id, req.lang)
    return {"status": "accepted"}


@app.post("/compare")
def compare(req: CompareRequest, x_api_key: str = Header(...)):
    """Score the farmer's own crop choice next to their current rotation and the best option."""
    _check_key(x_api_key)
    row = db.get_profile(req.user_id)
    if not row:
        raise HTTPException(404, "profile not found")
    try:
        return compare_choice(row.get("answers") or {}, req.crop, req.season)
    except (ProfileError, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/health")
def health():
    prov = provider()
    return {"ok": True, "llm": f"{prov}:{model_name(prov)}" if prov else "templates (no LLM key)",
            "supabase": bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY),
            "copernicus": bool(settings.COPERNICUS_CLIENT_ID), "mock_layers": settings.USE_MOCK_LAYERS}
