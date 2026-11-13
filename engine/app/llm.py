"""LLM step: turn the evidence pack into farmer-friendly text. The LLM only explains.

Guardrails:
- JSON-only output validated with pydantic, and the strategy ids must match the pack.
- Number check: every number in the generated text must already appear in the pack.
  On failure we retry once, then fall back to template text built from the same pack.
- Only the evidence pack is sent (no email, no user id). Results are cached by pack hash.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from typing import Any

from pydantic import ValidationError

from .data import cache
from .schemas import EvidencePack, Narrative, NarrativeOut, StrategyText
from .settings import settings
from .texts import CONFIDENCE_NAMES, STRATEGY_NAMES, render, sequence_text

log = logging.getLogger(__name__)

SYSTEM = """You explain crop-rotation analysis results to a farmer in Egypt's Nile Delta.
Use ONLY the facts and numbers in the DATA. Never add numbers, crops, prices, dates or advice that are not in it.
Write short, simple sentences with no jargon. If you use a technical term, explain it in a few words.
For every strategy return: summary (2 sentences), why, evidence (list), benefits (list), gaps (list), risks (list).
Keep every strategy id exactly as given. Keep the strategies in the same order.
Mention uncertainty and the confidence level honestly. Do not oversell any option.
The "reminder" is one sentence telling the farmer to review the options with a local agricultural expert.
Reply in the requested language (en = English, ar = simple Modern Standard Arabic that Egyptian farmers understand).
Write numbers with Western digits (0-9), exactly as they appear in the DATA.
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
        if any(a and abs(n - a) / abs(a) <= 0.01 for a in allowed):
            continue
        bad.append(n)
    return bad


# ---------------------------------------------------------------- template fallback

def fallback_text(pack: EvidencePack, lang: str) -> NarrativeOut:
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
                        lang=lang, source="template")  # type: ignore[arg-type]


# ---------------------------------------------------------------- LLM call

def _strip_fences(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
    start, end = raw.find("{"), raw.rfind("}")
    return raw[start:end + 1] if start != -1 and end != -1 else raw


def _call(view: dict[str, Any], lang: str, feedback: str | None = None) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    content = (f"Language: {lang}\nSCHEMA: {json.dumps(Narrative.model_json_schema())}\n"
               f"DATA: {json.dumps(view, ensure_ascii=False)}")
    if feedback:
        content += f"\n\nYour previous answer was rejected: {feedback} Fix it and return the full JSON again."
    msg = client.messages.create(
        model=settings.LLM_MODEL, max_tokens=6000, temperature=0.2, system=SYSTEM,
        messages=[{"role": "user", "content": content}],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


def narrate(pack: EvidencePack, lang: str = "en") -> NarrativeOut:
    if lang not in ("en", "ar"):
        lang = "en"
    if not settings.ANTHROPIC_API_KEY:
        return fallback_text(pack, lang)

    view = llm_view(pack)
    key = hashlib.sha256((settings.LLM_MODEL + lang + json.dumps(view, sort_keys=True, ensure_ascii=False)).encode()).hexdigest()
    hit = cache.get("llm", key)
    if hit:
        return NarrativeOut(**hit)

    allowed = allowed_numbers(view)
    ids = [s.id for s in pack.strategies]
    feedback = None
    for attempt in range(2):          # first try + one retry
        try:
            narr = Narrative.model_validate_json(_strip_fences(_call(view, lang, feedback)))
        except ValidationError as exc:
            feedback = f"invalid JSON for the schema ({exc.error_count()} errors)."
            continue
        except Exception as exc:      # network / auth / rate limit: no point retrying the same way
            log.warning("LLM call failed: %s", exc)
            break
        if [s.id for s in narr.strategies] != ids:
            feedback = f"the strategy ids must be exactly {ids} in this order."
            continue
        bad = unsupported_numbers(narr, allowed)
        if bad:
            feedback = f"these numbers are not in the DATA: {bad[:8]}. Only use numbers from the DATA."
            log.info("LLM attempt %d used unsupported numbers %s", attempt + 1, bad[:8])
            continue
        out = NarrativeOut(**narr.model_dump(), lang=lang, source="llm")  # type: ignore[arg-type]
        cache.put("llm", key, out.model_dump())
        return out
    return fallback_text(pack, lang)
