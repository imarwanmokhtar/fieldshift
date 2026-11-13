"""Engine tests. They run fully offline: NASA POWER is forced to the bundled fallback climate."""

from __future__ import annotations

import pytest

from app.data import power
from app.features import CROPS, climate_features, crop_metrics, et0_hargreaves, extraterrestrial_radiation
from app.llm import allowed_numbers, fallback_text, llm_view, unsupported_numbers
from app.pipeline import analyze_answers, compare_choice
from app.profile import ProfileError, parse_profile
from app.schemas import CRITERIA, EvidencePack, Narrative, StrategyText
from app.strategies import build_context, score_rotation, weights_from_priorities

ANSWERS = {
    "pin": {"lat": 31.0412, "lng": 31.3807},
    "area": {"value": 3, "unit": "feddan", "hectares": 1.26},
    "soil_texture": "clay", "drainage": "day", "salinity": "some_spots", "soil_issues": ["low_fertility"],
    "organic_inputs": "once_year", "soil_test": {"hasTest": False}, "water_source": ["nile_canal"],
    "water_reliability": "often_late", "irrigation_method": "flood",
    "irrigation_interval": {"summer": 7, "winter": 14}, "water_quality": "good", "water_cost": "somewhat",
    "last_crop": {"crop": "rice", "season": "summer"}, "prev_crop": {"crop": "wheat", "season": "winter"},
    "bare_periods": "1_to_3_months", "pest_issues": ["insects"], "fertilizer_level": "high",
    "priorities": ["save_water", "better_soil", "higher_income"], "risk_tolerance": "small_trial",
    "equipment": ["tractor", "pump"], "horizon": "2_to_3_years",
}


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    def no_network(*a, **k):
        raise ConnectionError("offline test")
    monkeypatch.setattr(power, "fetch_power", no_network)
    monkeypatch.setattr("app.llm.settings", type("S", (), {"ANTHROPIC_API_KEY": "", "LLM_MODEL": "x"})())


@pytest.fixture(scope="module")
def clim():
    return climate_features(power.fallback_climate(31.04, 31.38), 31.04)


# ---------------------------------------------------------------- weights

def test_weights_follow_rank_and_sum_to_one():
    w = weights_from_priorities(["save_water", "better_soil", "higher_income"])
    assert w["water"] == 0.40 and w["soil"] == 0.25 and w["income"] == 0.15
    assert abs(sum(w.values()) - 1.0) < 1e-6
    assert all(w[c] > 0 for c in CRITERIA)


def test_weights_with_one_priority():
    w = weights_from_priorities(["fodder"])
    assert w["forage"] == 0.40
    assert abs(sum(w.values()) - 1.0) < 1e-6


# ---------------------------------------------------------------- profile

def test_profile_requires_pin_and_area():
    with pytest.raises(ProfileError):
        parse_profile({"area": {"value": 1, "unit": "feddan"}})
    with pytest.raises(ProfileError):
        parse_profile({"pin": {"lat": 31, "lng": 31}})


def test_profile_unknowns_are_tracked():
    p = parse_profile({"pin": {"lat": 31, "lng": 31.4}, "area": {"value": 24, "unit": "kirat"}, "drainage": "unknown"})
    assert abs(p.area_feddan - 1.0) < 1e-6
    assert "drainage" in p.unknown_answers and "last_crop" in p.unknown_answers


# ---------------------------------------------------------------- climate maths

def test_ra_and_hargreaves_are_plausible():
    import numpy as np
    ra = extraterrestrial_radiation(31.0, np.array([172]))[0]      # June solstice, ~41-42 MJ/m2/day
    assert 40 < ra < 43
    et0 = et0_hargreaves(np.array([34.0]), np.array([21.0]), np.array([ra]))[0]
    assert 6 < et0 < 9


def test_et0_and_water_ranking(clim):
    assert 1300 < clim.et0_annual_mm < 2000
    m = {c: crop_metrics(c, clim, "flood") for c in ("rice", "wheat", "berseem", "sorghum")}
    assert m["rice"].gross_m3_per_feddan > m["sorghum"].gross_m3_per_feddan > m["wheat"].gross_m3_per_feddan
    assert 5000 < m["rice"].gross_m3_per_feddan < 9000


def test_drip_uses_less_water_than_flood(clim):
    assert crop_metrics("maize", clim, "drip").gross_m3_per_feddan < crop_metrics("maize", clim, "flood").gross_m3_per_feddan


# ---------------------------------------------------------------- scoring

def test_scores_in_range_and_legume_helps_soil(clim):
    ctx = build_context(parse_profile(ANSWERS), clim)
    cereal = score_rotation(("wheat", "rice", "wheat", "rice"), ctx)
    legume = score_rotation(("berseem", "rice", "wheat", "rice"), ctx)
    for s in (cereal, legume):
        assert all(0 <= v <= 100 for v in s.scores.values())
    assert legume.scores["soil"] > cereal.scores["soil"]
    sorghum = score_rotation(("wheat", "sorghum", "wheat", "sorghum"), ctx)
    assert sorghum.scores["water"] > cereal.scores["water"]


# ---------------------------------------------------------------- pipeline + pack

def test_pipeline_builds_valid_pack_with_three_strategies():
    pack, narr = analyze_answers(ANSWERS, "en")
    EvidencePack.model_validate(pack.model_dump(mode="json"))
    ids = [s.id for s in pack.strategies]
    assert ids[0] == "current" and len(ids) >= 3
    assert pack.recommended_id in ids
    assert pack.observations["climate_source"] == "fallback_climatology"
    assert "nasa_power" in pack.data_quality.layers_unavailable
    for s in pack.strategies:
        assert s.confidence in ("high", "medium", "low")
        assert s.evidence and s.gaps
    assert narr.source == "template" and [t.id for t in narr.strategies] == ids


def test_arabic_fallback_is_arabic():
    pack, narr = analyze_answers(ANSWERS, "ar")
    assert any("؀" <= ch <= "ۿ" for ch in narr.overview)
    assert "مهندس زراعي" in narr.reminder


def test_compare_choice():
    r = compare_choice(ANSWERS, "cotton")
    assert r["choice"]["kind"] == "custom"
    assert set(r["delta_vs_current"]) == set(r["choice"]["scores"])


# ---------------------------------------------------------------- number guardrail

def test_number_guardrail():
    pack, _ = analyze_answers(ANSWERS, "en")
    allowed = allowed_numbers(llm_view(pack))
    good = fallback_text(pack, "en")
    assert unsupported_numbers(Narrative(**good.model_dump(exclude={"lang", "source"})), allowed) == []

    bad = Narrative(overview="This saves 98765 m3 of water.", reminder="Check locally.",
                    strategies=[StrategyText(id="current", summary="s", why="w", evidence=[], benefits=[],
                                             gaps=[], risks=[])])
    assert 98765.0 in unsupported_numbers(bad, allowed)

    arabic = Narrative(overview="يوفر ٩٨٧٦٥ متر مكعب", reminder="r",
                       strategies=[StrategyText(id="current", summary="s", why="w", evidence=[], benefits=[],
                                                gaps=[], risks=[])])
    assert 98765.0 in unsupported_numbers(arabic, allowed)


def test_crop_table_is_complete():
    needed = {"season", "kc_ini", "kc_mid", "kc_end", "season_days", "salinity_tolerance", "income_index", "soil_fit"}
    for cid, c in CROPS.items():
        assert needed <= set(c), cid


# ---------------------------------------------------------------- LLM path (fake model)

def test_llm_bad_numbers_fall_back_after_retry(monkeypatch, tmp_path):
    import json
    import app.llm as llm
    monkeypatch.setattr(llm, "settings", type("S", (), {"ANTHROPIC_API_KEY": "k", "LLM_MODEL": "m"})())
    monkeypatch.setattr(llm.cache, "get", lambda *a, **k: None)
    monkeypatch.setattr(llm.cache, "put", lambda *a, **k: None)
    pack, _ = analyze_answers(ANSWERS, "en")
    calls = []

    def fake_call(view, lang, feedback=None):
        calls.append(feedback)
        return json.dumps({"overview": "Saves 424242 m3.", "reminder": "r", "strategies": [
            {"id": s.id, "summary": "s", "why": "w", "evidence": [], "benefits": [], "gaps": [], "risks": []}
            for s in pack.strategies]})
    monkeypatch.setattr(llm, "_call", fake_call)
    out = llm.narrate(pack, "en")
    assert out.source == "template" and len(calls) == 2 and "424242" in calls[1]

    def good_call(view, lang, feedback=None):
        return "```json\n" + json.dumps({"overview": "We compared options.", "reminder": "Ask an expert.", "strategies": [
            {"id": s.id, "summary": f"Score {s.scores['overall']} out of 100.", "why": "w", "evidence": [],
             "benefits": [], "gaps": [], "risks": []} for s in pack.strategies]}) + "\n```"
    monkeypatch.setattr(llm, "_call", good_call)
    assert llm.narrate(pack, "en").source == "llm"


# ---------------------------------------------------------------- API

def test_api_key_and_health(monkeypatch):
    from fastapi.testclient import TestClient
    import app.main as main
    monkeypatch.setattr(main, "settings", type("S", (), {
        "ENGINE_API_KEY": "secret", "ANTHROPIC_API_KEY": "", "SUPABASE_URL": "u",
        "SUPABASE_SERVICE_ROLE_KEY": "k", "COPERNICUS_CLIENT_ID": "", "USE_MOCK_LAYERS": False})())
    ran = []
    monkeypatch.setattr(main, "run_analysis", lambda *a: ran.append(a))
    c = TestClient(main.app)
    assert c.get("/health").json()["ok"] is True
    body = {"analysis_id": "a1", "user_id": "u1", "lang": "ar"}
    assert c.post("/analyze", json=body, headers={"X-API-Key": "wrong"}).status_code == 401
    r = c.post("/analyze", json=body, headers={"X-API-Key": "secret"})
    assert r.status_code == 202 and ran == [("a1", "u1", "ar")]


def test_gemini_request_and_parse(monkeypatch):
    import json
    import httpx
    import app.llm as llm
    monkeypatch.setattr(llm, "settings", type("S", (), {
        "LLM_PROVIDER": "", "GEMINI_API_KEY": "g-key", "ANTHROPIC_API_KEY": "", "LLM_MODEL": ""})())
    monkeypatch.setattr(llm.cache, "get", lambda *a, **k: None)
    monkeypatch.setattr(llm.cache, "put", lambda *a, **k: None)
    assert llm.provider() == "gemini" and llm.model_name("gemini") == "gemini-2.5-flash"
    pack, _ = analyze_answers(ANSWERS, "ar")
    seen = {}

    def fake_post(url, headers, json, timeout):
        seen.update(url=url, headers=headers, body=json)
        reply = {"overview": "قارنّا الخيارات.", "reminder": "راجع مهندساً زراعياً.", "strategies": [
            {"id": s.id, "summary": f"الدرجة {s.scores['overall']} من 100.", "why": "w", "evidence": [],
             "benefits": [], "gaps": [], "risks": []} for s in pack.strategies]}
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": __import__("json").dumps(reply, ensure_ascii=False)}]}}]},
                              request=httpx.Request("POST", url))
    monkeypatch.setattr(httpx, "post", fake_post)
    out = llm.narrate(pack, "ar")
    assert out.source == "llm" and out.lang == "ar"
    assert seen["url"].endswith("/models/gemini-2.5-flash:generateContent")
    assert seen["headers"]["x-goog-api-key"] == "g-key"
    assert seen["body"]["generationConfig"]["responseMimeType"] == "application/json"
    assert "DATA:" in seen["body"]["contents"][0]["parts"][0]["text"]
