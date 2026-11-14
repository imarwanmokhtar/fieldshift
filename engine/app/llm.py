"""LLM step: turn the evidence pack into farmer-friendly text. The LLM only explains.

Guardrails:
- JSON-only output validated with pydantic, and the strategy ids must match the pack.
- Number check: every number in the generated text must already appear in the pack.
  On failure we retry once, then fall back to template text built from the same pack.
- Only the evidence pack is sent (no email, no user id). Results are cached by pack hash.
- Provider: Groq (GROQ_API_KEY), OpenRouter (OPENROUTER_API_KEY), Gemini (GEMINI_API_KEY) or Claude (ANTHROPIC_API_KEY); see settings.LLM_PROVIDER.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from typing import Any

from pydantic import ValidationError

from .data import cache
from .schemas import EvidencePack, Narrative, NarrativeOut, StrategyText
from .settings import settings
from .practices import PRACTICES
from .texts import CONFIDENCE_NAMES, STRATEGY_NAMES, render, sequence_text

log = logging.getLogger(__name__)

SYSTEM = """You explain crop-rotation analysis results to a farmer in Egypt's Nile Delta.
Use ONLY the facts and numbers in the DATA. Never add numbers, crops, prices, dates or advice that are not in it.
Write short, simple sentences with no jargon. If you use a technical term, explain it in a few words.
For every strategy return: summary (2 sentences), why, evidence (list), benefits (list), gaps (list), risks (list).
Keep every strategy id exactly as given. Keep the strategies in the same order.
Mention uncertainty and the confidence level honestly. Do not oversell any option.
A strategy with "practices" keeps the same crops and changes how they are grown. Its water savings are general
reported ranges, not verified on this field: say so, never call them proven or documented, and never claim that
income or yield stays the same or improves. Name each practice exactly as in "practices" (English) or "practices_ar" (Arabic).
The "reminder" is one sentence telling the farmer to review the options with a local agricultural expert.
Reply in the requested language (en = English, ar = simple Modern Standard Arabic that Egyptian farmers understand).
Write numbers with Western digits (0-9), exactly as they appear in the DATA.
Keep it short: at most 4 short items in each list, and one sentence per item.
Return only valid JSON matching the schema, with no extra text."""

_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩٫٬", "0123456789.,")
_NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")


# ---------------------------------------------------------------- what the LLM sees

def llm_view(pack: EvidencePack) -> dict[str, Any]:
    """A compact, text-first view of the pack (no raw crop tables, no ids of people)."""
    obs = pack.observations
    return {
        "field": {"area_feddan": pack.field["area_feddan"], "current_rotation": pack.field["current_rotation"]},
        "farmer_priorities": pack.farmer_priorities,
        "recommended_id": pack.recommended_id,
        "climate": {
            "source": obs.get("climate_source"),
            "hot_days_above_35c_per_year": obs.get("hot_days_per_year", {}).get("mean"),
            "hot_days_trend_per_year": obs.get("hot_days_per_year", {}).get("trend_per_year"),
            "annual_mean_temp_c": obs.get("annual_mean_temp_c"),
            "rain_mm_per_year": obs.get("rain_mm_per_year"),
        },
        "data_quality_notes": [n.text for n in pack.data_quality.notes],
        "strategies": [{
            "id": s.id, "name": s.name, "sequence": s.sequence,
            **({"practices": [PRACTICES[p]["name_en"] for p in s.practices],
                "practices_ar": [PRACTICES[p]["name_ar"] for p in s.practices]} if s.practices else {}),
            "scores_out_of_100": s.scores, "confidence": s.confidence,
            "evidence": [f.text for f in s.evidence], "benefits": [f.text for f in s.benefits],
            "gaps": [f.text for f in s.gaps], "risks": [f.text for f in s.risks],
        } for s in pack.strategies],
    }


# ---------------------------------------------------------------- number guardrail

def _numbers(text: str) -> list[float]:
    out = []
    for tok in _NUM_RE.findall(text.translate(_ARABIC_DIGITS)):
        t = tok
        if re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d+)?", t):   # 2,430 -> 2430
            t = t.replace(",", "")
        t = t.replace(",", ".")
        try:
            out.append(float(t))
        except ValueError:
            continue
    return out


def allowed_numbers(view: dict[str, Any]) -> set[float]:
    nums = set(_numbers(json.dumps(view, ensure_ascii=False)))
    nums |= {float(i) for i in range(0, 13)}          # counting words: "2 years", "3 options"
    nums |= {100.0, 10.0, 35.0, 50.0}                  # "out of 100", "every 10 years", 35°C, 50 km
    return nums


def unsupported_numbers(narr: Narrative, allowed: set[float]) -> list[float]:
    text = json.dumps(narr.model_dump(), ensure_ascii=False)
    bad = []
    for n in _numbers(text):
        if n in allowed or round(n) in allowed:
            continue
        if any(a and abs(n - a) / abs(a) <= 0.02 for a in allowed):
            continue
        bad.append(n)
    return bad


# ---------------------------------------------------------------- template fallback

def fallback_text(pack: EvidencePack, lang: str, reason: str | None = None) -> NarrativeOut:
    by_id = {s.id: s for s in pack.strategies}
    best = by_id[pack.recommended_id]
    best_name = best.name_ar if lang == "ar" else best.name
    overview_code = "overview" if pack.observations.get("climate_source") == "nasa_power" else "overview_fallback_climate"
    overview = render(overview_code, {
        "n": len(pack.strategies), "area": f"{pack.field['area_feddan']:g}",
        "priorities": pack.farmer_priorities, "best": best_name}, lang)
    texts = []
    for s in pack.strategies:
        name = STRATEGY_NAMES[s.kind][lang]
        seq = sequence_text([(sl.season, sl.crop) for sl in s.slots], lang)
        summary = render("summary", {"name": name, "sequence": seq, "overall": s.scores["overall"],
                                     "confidence": CONFIDENCE_NAMES[s.confidence][lang]}, lang)
        texts.append(StrategyText(
            id=s.id, summary=summary, why=render(f"why_{s.kind}", {}, lang),
            evidence=[render(f.code, f.params, lang) for f in s.evidence[:6]],
            benefits=[render(f.code, f.params, lang) for f in s.benefits[:6]],
            gaps=[render(f.code, f.params, lang) for f in s.gaps[:6]],
            risks=[render(f.code, f.params, lang) for f in s.risks[:6]],
        ))
    return NarrativeOut(overview=overview, strategies=texts, reminder=render("reminder", {}, lang),
                        lang=lang, source="template", fallback_reason=reason)  # type: ignore[arg-type]


# ---------------------------------------------------------------- LLM call

def _strip_fences(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
    start, end = raw.find("{"), raw.rfind("}")
    return raw[start:end + 1] if start != -1 and end != -1 else raw


DEFAULT_MODELS = {"groq": "openai/gpt-oss-120b", "openrouter": "google/gemma-4-31b-it:free",
                  "gemini": "gemini-3.8-flash", "anthropic": "claude-sonnet-5-5"}
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
KEY_FIELDS = {"groq": "GROQ_API_KEY", "openrouter": "OPENROUTER_API_KEY", "gemini": "GEMINI_API_KEY",
              "anthropic": "ANTHROPIC_API_KEY"}
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def provider() -> str | None:
    """Which LLM to use: LLM_PROVIDER if set (and its key exists), otherwise the first key present."""
    def has(p: str) -> bool:
        return bool(getattr(settings, KEY_FIELDS[p], "") or "")
    chosen = getattr(settings, "LLM_PROVIDER", "") or ""
    if chosen in KEY_FIELDS:
        return chosen if has(chosen) else None
    for p in ("groq", "openrouter", "gemini", "anthropic"):
        if has(p):
            return p
    return None


def model_name(prov: str) -> str:
    return (getattr(settings, "LLM_MODEL", "") or "") or DEFAULT_MODELS[prov]


def _prompt(view: dict[str, Any], lang: str, feedback: str | None) -> str:
    content = (f"Language: {lang}\nSCHEMA: {json.dumps(Narrative.model_json_schema())}\n"
               f"DATA: {json.dumps(view, ensure_ascii=False)}")
    if feedback:
        content += f"\n\nYour previous answer was rejected: {feedback} Fix it and return the full JSON again."
    return content


_STR = {"type": "STRING"}
_STR_LIST = {"type": "ARRAY", "items": _STR}
GEMINI_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "overview": _STR,
        "strategies": {"type": "ARRAY", "items": {
            "type": "OBJECT",
            "properties": {"id": _STR, "summary": _STR, "why": _STR, "evidence": _STR_LIST,
                           "benefits": _STR_LIST, "gaps": _STR_LIST, "risks": _STR_LIST},
            "required": ["id", "summary", "why", "evidence", "benefits", "gaps", "risks"],
            "propertyOrdering": ["id", "summary", "why", "evidence", "benefits", "gaps", "risks"],
        }},
        "reminder": _STR,
    },
    "required": ["overview", "strategies", "reminder"],
    "propertyOrdering": ["overview", "strategies", "reminder"],
}


class LlmError(RuntimeError):
    pass


def _thinking_config(model: str) -> dict:
    """We only need rephrasing, so keep "thinking" as low as the model allows (faster, cheaper).
    Gemini 2.5 uses a token budget (0 = off); Gemini 3.x uses a level ("low" is the lowest on 3.8)."""
    if model.startswith("gemini-2."):
        return {"thinkingBudget": 0}
    return {"thinkingLevel": "low"}


def _call_gemini(content: str, model: str) -> str:
    import httpx

    r = httpx.post(
        GEMINI_URL.format(model=model),
        headers={"x-goog-api-key": settings.GEMINI_API_KEY, "Content-Type": "application/json"},
        json={
            "systemInstruction": {"parts": [{"text": SYSTEM}]},
            "contents": [{"role": "user", "parts": [{"text": content}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 16384,
                "responseMimeType": "application/json",
                "responseSchema": GEMINI_SCHEMA,
                "thinkingConfig": _thinking_config(model),
            },
        },
        timeout=55,
    )
    if r.status_code >= 400:
        raise LlmError(f"gemini HTTP {r.status_code}: {r.text[:300]}")
    data = r.json()
    cands = data.get("candidates") or []
    if not cands:
        raise LlmError(f"gemini returned no answer: {str(data.get('promptFeedback'))[:200]}")
    finish = cands[0].get("finishReason")
    if finish and finish not in ("STOP", "FINISH_REASON_UNSPECIFIED"):
        raise LlmError(f"gemini stopped early: {finish}")
    parts = (cands[0].get("content") or {}).get("parts") or []
    return "".join(p.get("text", "") for p in parts if not p.get("thought"))


def _call_openrouter(content: str, model: str) -> str:
    """OpenRouter. The system prompt is sent inside the user message,
    because some open models (e.g. Gemma) do not accept a separate system role."""
    return _call_openai_compatible("openrouter", OPENROUTER_URL, settings.OPENROUTER_API_KEY, content, model,
                                   {"HTTP-Referer": "https://fieldshift-one.vercel.app", "X-Title": "Field Shift"})


def _call_groq(content: str, model: str) -> str:
    """Groq (OpenAI-compatible), default model openai/gpt-oss-120b."""
    return _call_openai_compatible("groq", GROQ_URL, settings.GROQ_API_KEY, content, model)


def _call_openai_compatible(name: str, url: str, key: str, content: str, model: str,
                            extra_headers: dict[str, str] | None = None) -> str:
    """One chat-completions request to an OpenAI-compatible API (OpenRouter, Groq)."""
    import httpx

    for attempt in range(2):
        r = _post_chat(url, key, content, model, extra_headers)
        # Short per-minute rate limits (e.g. Groq's free tier): wait it out once, then retry.
        wait = _retry_after_seconds(r) if r.status_code == 429 and attempt == 0 else None
        if wait is None or wait > MAX_RATE_LIMIT_WAIT_S:
            break
        log.info("%s rate-limited, retrying in %.1fs", name, wait)
        time.sleep(wait + 0.5)
    return _parse_chat(name, r)


MAX_RATE_LIMIT_WAIT_S = 20.0


def _retry_after_seconds(r) -> float | None:
    """Seconds to wait, from the Retry-After header or a 'try again in 4.5s' message."""
    header = r.headers.get("retry-after")
    try:
        if header is not None:
            return float(header)
    except ValueError:
        pass
    m = re.search(r"try again in ([0-9.]+)(ms|s)", r.text)
    if m:
        return float(m.group(1)) / (1000 if m.group(2) == "ms" else 1)
    return None


def _post_chat(url: str, key: str, content: str, model: str, extra_headers: dict[str, str] | None):
    import httpx

    return httpx.post(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            **(extra_headers or {}),
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": f"{SYSTEM}\n\n{content}"}],
            "temperature": 0.2,
            "max_tokens": 8000,
            "response_format": {"type": "json_object"},
        },
        timeout=55,
    )


def _parse_chat(name: str, r) -> str:
    if r.status_code >= 400:
        raise LlmError(f"{name} HTTP {r.status_code}: {r.text[:300]}")
    data = r.json()
    if data.get("error"):
        raise LlmError(f"{name} error: {str(data['error'])[:300]}")
    choices = data.get("choices") or []
    if not choices:
        raise LlmError(f"{name} returned no answer")
    finish = choices[0].get("finish_reason")
    if finish == "length":
        raise LlmError(f"{name} stopped early: answer too long")
    text = (choices[0].get("message") or {}).get("content") or ""
    if not text.strip():
        raise LlmError(f"{name} returned an empty answer")
    return text


def _call_anthropic(content: str, model: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model=model, max_tokens=6000, temperature=0.2, system=SYSTEM,
        messages=[{"role": "user", "content": content}],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


def _call(view: dict[str, Any], lang: str, feedback: str | None = None) -> str:
    prov = provider()
    content = _prompt(view, lang, feedback)
    if prov == "groq":
        return _call_groq(content, model_name(prov))
    if prov == "openrouter":
        return _call_openrouter(content, model_name(prov))
    if prov == "gemini":
        return _call_gemini(content, model_name(prov))
    return _call_anthropic(content, model_name("anthropic"))


def narrate(pack: EvidencePack, lang: str = "en") -> NarrativeOut:
    if lang not in ("en", "ar"):
        lang = "en"
    prov = provider()
    if prov is None:
        return fallback_text(pack, lang, reason="no LLM API key set")

    view = llm_view(pack)
    key = hashlib.sha256((prov + model_name(prov) + lang + json.dumps(view, sort_keys=True, ensure_ascii=False)).encode()).hexdigest()
    hit = cache.get("llm", key)
    if hit:
        return NarrativeOut(**hit)

    allowed = allowed_numbers(view) | set(_numbers(pack.model_dump_json()))
    ids = [s.id for s in pack.strategies]
    feedback = None
    reason = "unknown"
    started = time.monotonic()
    for attempt in range(2):          # first try + one retry
        if attempt and time.monotonic() - started > 25:
            reason += " (no time left to retry)"
            break
        try:
            raw = _call(view, lang, feedback)
        except Exception as exc:      # network / auth / quota / truncated: retrying the same way rarely helps
            reason = f"{type(exc).__name__}: {str(exc)[:300]}"
            log.warning("LLM call failed: %s", reason)
            break
        try:
            narr = Narrative.model_validate_json(_strip_fences(raw))
        except ValidationError as exc:
            reason = f"invalid JSON from model ({exc.error_count()} errors): {str(exc)[:200]}"
            feedback = f"invalid JSON for the schema ({exc.error_count()} errors)."
            log.warning("LLM attempt %d: %s", attempt + 1, reason)
            continue
        if [s.id for s in narr.strategies] != ids:
            reason = f"wrong strategy ids {[s.id for s in narr.strategies]} (expected {ids})"
            feedback = f"the strategy ids must be exactly {ids} in this order."
            log.warning("LLM attempt %d: %s", attempt + 1, reason)
            continue
        bad = unsupported_numbers(narr, allowed)
        if bad:
            reason = f"numbers not in the data: {bad[:8]}"
            feedback = f"these numbers are not in the DATA: {bad[:8]}. Only use numbers from the DATA."
            log.warning("LLM attempt %d: %s", attempt + 1, reason)
            continue
        out = NarrativeOut(**narr.model_dump(), lang=lang, source="llm")  # type: ignore[arg-type]
        cache.put("llm", key, out.model_dump())
        return out
    return fallback_text(pack, lang, reason=reason)
