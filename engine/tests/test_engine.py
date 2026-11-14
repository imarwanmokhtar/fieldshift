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
        return json.dumps({"overview": "Saves 424242 m3.", "reminder": "r", "conclusion": {"headline": "h", "steps": ["a", "b", "c"], "check": "c"}, "strategies": [
            {"id": s.id, "summary": "s", "why": "w", "evidence": [], "benefits": [], "gaps": [], "risks": []}
            for s in pack.strategies]})
    monkeypatch.setattr(llm, "_call", fake_call)
    out = llm.narrate(pack, "en")
    assert out.source == "template" and len(calls) == 2 and "424242" in calls[1]
    assert "424242" in (out.fallback_reason or "")

    def good_call(view, lang, feedback=None):
        return "```json\n" + json.dumps({"overview": "We compared options.", "reminder": "Ask an expert.", "conclusion": {"headline": "h", "steps": ["a", "b", "c"], "check": "c"}, "strategies": [
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


def test_gemini_http_error_is_recorded(monkeypatch):
    import httpx
    import app.llm as llm
    monkeypatch.setattr(llm, "settings", type("S", (), {
        "LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "bad", "ANTHROPIC_API_KEY": "", "LLM_MODEL": ""})())
    monkeypatch.setattr(llm.cache, "get", lambda *a, **k: None)
    pack, _ = analyze_answers(ANSWERS, "en")
    monkeypatch.setattr(httpx, "post", lambda url, headers, json, timeout: httpx.Response(
        403, text='{"error":{"status":"PERMISSION_DENIED"}}', request=httpx.Request("POST", url)))
    out = llm.narrate(pack, "en")
    assert out.source == "template" and "403" in out.fallback_reason and "PERMISSION_DENIED" in out.fallback_reason


def test_gemini_request_and_parse(monkeypatch):
    import json
    import httpx
    import app.llm as llm
    monkeypatch.setattr(llm, "settings", type("S", (), {
        "LLM_PROVIDER": "", "GEMINI_API_KEY": "g-key", "ANTHROPIC_API_KEY": "", "LLM_MODEL": ""})())
    monkeypatch.setattr(llm.cache, "get", lambda *a, **k: None)
    monkeypatch.setattr(llm.cache, "put", lambda *a, **k: None)
    assert llm.provider() == "gemini" and llm.model_name("gemini") == "gemini-3.8-flash"
    pack, _ = analyze_answers(ANSWERS, "ar")
    seen = {}

    def fake_post(url, headers, json, timeout):
        seen.update(url=url, headers=headers, body=json)
        reply = {"overview": "قارنّا الخيارات.", "reminder": "راجع مهندساً زراعياً.", "conclusion": {"headline": "h", "steps": ["a", "b", "c"], "check": "c"}, "strategies": [
            {"id": s.id, "summary": f"الدرجة {s.scores['overall']} من 100.", "why": "w", "evidence": [],
             "benefits": [], "gaps": [], "risks": []} for s in pack.strategies]}
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": __import__("json").dumps(reply, ensure_ascii=False)}]}}]},
                              request=httpx.Request("POST", url))
    monkeypatch.setattr(httpx, "post", fake_post)
    out = llm.narrate(pack, "ar")
    assert out.source == "llm" and out.lang == "ar"
    assert seen["url"].endswith("/models/gemini-3.8-flash:generateContent")
    assert seen["body"]["generationConfig"]["thinkingConfig"] == {"thinkingLevel": "low"}
    assert llm._thinking_config("gemini-2.5-flash") == {"thinkingBudget": 0}
    assert seen["headers"]["x-goog-api-key"] == "g-key"
    assert seen["body"]["generationConfig"]["responseMimeType"] == "application/json"
    assert seen["body"]["generationConfig"]["responseSchema"]["required"] == ["overview", "strategies", "reminder", "conclusion"]
    assert "DATA:" in seen["body"]["contents"][0]["parts"][0]["text"]


def test_sync_mode_runs_inline(monkeypatch):
    from fastapi.testclient import TestClient
    import app.main as main
    monkeypatch.setattr(main, "settings", type("S", (), {"ENGINE_API_KEY": "secret", "ENGINE_SYNC": True})())
    ran = []
    monkeypatch.setattr(main, "run_analysis", lambda *a: ran.append(a))
    r = TestClient(main.app).post("/analyze", json={"analysis_id": "a1", "user_id": "u1"},
                                  headers={"X-API-Key": "secret"})
    assert r.status_code == 200 and r.json()["status"] == "finished" and ran == [("a1", "u1", None)]


def test_openrouter_request_and_parse(monkeypatch):
    import json as _json
    import httpx
    import app.llm as llm
    monkeypatch.setattr(llm, "settings", type("S", (), {
        "LLM_PROVIDER": "openrouter", "OPENROUTER_API_KEY": "or-key", "GEMINI_API_KEY": "g",
        "ANTHROPIC_API_KEY": "", "LLM_MODEL": ""})())
    monkeypatch.setattr(llm.cache, "get", lambda *a, **k: None)
    monkeypatch.setattr(llm.cache, "put", lambda *a, **k: None)
    assert llm.provider() == "openrouter" and llm.model_name("openrouter") == "google/gemma-4-31b-it:free"
    pack, _ = analyze_answers(ANSWERS, "ar")
    seen = {}

    def fake_post(url, headers, json, timeout):
        seen.update(url=url, headers=headers, body=json)
        reply = {"overview": "قارنّا الخيارات.", "reminder": "راجع مهندساً زراعياً.", "conclusion": {"headline": "h", "steps": ["a", "b", "c"], "check": "c"}, "strategies": [
            {"id": s.id, "summary": "ملخص.", "why": "w", "evidence": [], "benefits": [], "gaps": [], "risks": []}
            for s in pack.strategies]}
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {
            "content": "```json\n" + _json.dumps(reply, ensure_ascii=False) + "\n```"}}]},
            request=httpx.Request("POST", url))
    monkeypatch.setattr(httpx, "post", fake_post)
    out = llm.narrate(pack, "ar")
    assert out.source == "llm"
    assert seen["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert seen["headers"]["Authorization"] == "Bearer or-key"
    assert seen["body"]["model"] == "google/gemma-4-31b-it:free"
    assert seen["body"]["messages"][0]["role"] == "user" and "DATA:" in seen["body"]["messages"][0]["content"]

    monkeypatch.setattr(httpx, "post", lambda url, headers, json, timeout: httpx.Response(
        429, text='{"error":{"message":"Rate limit exceeded: free-models-per-day"}}', request=httpx.Request("POST", url)))
    out = llm.narrate(pack, "ar")
    assert out.source == "template" and "429" in out.fallback_reason


def test_groq_request(monkeypatch):
    import json as _json
    import httpx
    import app.llm as llm
    monkeypatch.setattr(llm, "settings", type("S", (), {
        "LLM_PROVIDER": "", "GROQ_API_KEY": "gsk-test", "OPENROUTER_API_KEY": "or-key", "GEMINI_API_KEY": "",
        "ANTHROPIC_API_KEY": "", "LLM_MODEL": ""})())
    monkeypatch.setattr(llm.cache, "get", lambda *a, **k: None)
    monkeypatch.setattr(llm.cache, "put", lambda *a, **k: None)
    # Groq comes first when no provider is chosen explicitly.
    assert llm.provider() == "groq" and llm.model_name("groq") == "openai/gpt-oss-120b"
    pack, _ = analyze_answers(ANSWERS, "en")
    seen = {}

    def fake_post(url, headers, json, timeout):
        seen.update(url=url, headers=headers, body=json)
        reply = {"overview": "We compared the options.", "reminder": "Check with an agronomist.", "conclusion": {"headline": "h", "steps": ["a", "b", "c"], "check": "c"}, "strategies": [
            {"id": s.id, "summary": "Summary.", "why": "w", "evidence": [], "benefits": [], "gaps": [], "risks": []}
            for s in pack.strategies]}
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {
            "content": _json.dumps(reply)}}]}, request=httpx.Request("POST", url))
    monkeypatch.setattr(httpx, "post", fake_post)
    out = llm.narrate(pack, "en")
    assert out.source == "llm"
    assert seen["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert seen["headers"]["Authorization"] == "Bearer gsk-test"
    assert "HTTP-Referer" not in seen["headers"]
    assert seen["body"]["model"] == "openai/gpt-oss-120b"


def test_short_rate_limit_is_retried_once(monkeypatch):
    import httpx
    import app.llm as llm
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    calls = []

    def fake_post(url, headers, json, timeout):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(429, text='{"error":{"message":"Please try again in 4.5s."}}',
                                  request=httpx.Request("POST", url))
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": "{}"}}]},
                              request=httpx.Request("POST", url))
    monkeypatch.setattr(httpx, "post", fake_post)
    assert llm._call_openai_compatible("groq", llm.GROQ_URL, "k", "hi", "m") == "{}"
    assert len(calls) == 2

    # A long wait (e.g. a daily limit) is not retried.
    calls.clear()
    monkeypatch.setattr(httpx, "post", lambda url, headers, json, timeout: (calls.append(1), httpx.Response(
        429, headers={"retry-after": "3600"}, text="{}", request=httpx.Request("POST", url)))[1])
    try:
        llm._call_openai_compatible("groq", llm.GROQ_URL, "k", "hi", "m")
        raise AssertionError("expected LlmError")
    except llm.LlmError as exc:
        assert "429" in str(exc)
    assert len(calls) == 1


def test_practice_option_saves_water_with_same_crops():
    pack, _ = analyze_answers(ANSWERS, "en")
    by = {s.kind: s for s in pack.strategies}
    assert "practice" in by
    cur, pr = by["current"], by["practice"]
    assert [sl.crop for sl in pr.slots] == [sl.crop for sl in cur.slots]
    assert pr.practices and pr.changes_from_current == 0
    assert pr.metrics["water_m3_per_feddan_year"] < cur.metrics["water_m3_per_feddan_year"]
    assert pr.scores["water"] >= cur.scores["water"]
    assert any(g.code == "practice_values_unverified" for g in pr.gaps)
    assert pr.confidence_score < cur.confidence_score or cur.confidence_score <= 5


def test_practice_uses_low_end_of_range():
    from app.practices import PRACTICES, water_factors
    f = water_factors(["laser_leveling", "raised_beds"], {"wheat", "rice"})
    lo_l = PRACTICES["laser_leveling"]["water_saving_pct"][0] / 100
    lo_b = PRACTICES["raised_beds"]["water_saving_pct"][0] / 100
    assert abs(f["rice"] - (1 - lo_l)) < 1e-9
    assert abs(f["wheat"] - (1 - lo_l) * (1 - lo_b)) < 1e-9


def test_practice_rules_drip_and_salt():
    from app.practices import applicable_practices
    from app.schemas import FarmProfile
    base = dict(lat=31.0, lng=31.4, area_ha=1.0)
    drip = FarmProfile(**base, irrigation_method="drip")
    ids, _ = applicable_practices(drip, {"wheat", "rice"}, 0)
    assert ids == ["awd_rice"]                      # levelling and beds are for surface irrigation only
    flood = FarmProfile(**base, irrigation_method="flood")
    ids, skipped = applicable_practices(flood, {"rice"}, 1)
    assert "awd_rice" not in ids and skipped == ["awd_rice"]
    ids, _ = applicable_practices(flood, {"rice"}, 0)
    assert set(ids) == {"laser_leveling", "awd_rice"}


def test_plan_facts_and_template_conclusion():
    import app.llm as llm
    pack, _ = analyze_answers(ANSWERS, "en")
    codes = [f.code for f in pack.plan]
    assert codes[0] in ("plan_recommend", "plan_keep")
    assert codes[-1] == "plan_check" and "plan_confidence" in codes
    out = llm.fallback_text(pack, "ar")
    assert out.conclusion is not None and out.conclusion.headline
    assert 1 <= len(out.conclusion.steps) <= 5
    assert "مهندس زراعي" in out.conclusion.check


def test_llm_must_return_conclusion(monkeypatch):
    import json as _json
    import httpx
    import app.llm as llm
    monkeypatch.setattr(llm, "settings", type("S", (), {
        "LLM_PROVIDER": "groq", "GROQ_API_KEY": "k", "OPENROUTER_API_KEY": "", "GEMINI_API_KEY": "",
        "ANTHROPIC_API_KEY": "", "LLM_MODEL": ""})())
    monkeypatch.setattr(llm.cache, "get", lambda *a, **k: None)
    monkeypatch.setattr(llm.cache, "put", lambda *a, **k: None)
    pack, _ = analyze_answers(ANSWERS, "en")
    base = {"overview": "o", "reminder": "r", "strategies": [
        {"id": s.id, "summary": "s", "why": "w", "evidence": [], "benefits": [], "gaps": [], "risks": []}
        for s in pack.strategies]}
    replies = [base, {**base, "conclusion": {"headline": "h", "steps": ["a", "b", "c"], "check": "c"}}]

    def fake_post(url, headers, json, timeout):
        body = replies.pop(0)
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": _json.dumps(body)}}]},
                              request=httpx.Request("POST", url))
    monkeypatch.setattr(httpx, "post", fake_post)
    out = llm.narrate(pack, "en")
    assert out.source == "llm" and out.conclusion.steps == ["a", "b", "c"]   # first reply rejected, second accepted
