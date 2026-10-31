"""Evidence-linked explanation blocks for Phase 7."""

from __future__ import annotations

from typing import Any

from ..i18n import text

_BAND_ORDER = {"Poor": 0, "Moderate": 1, "Good": 2}
_FIXED_RISKS = (
    "risk.variety_seed",
    "risk.sowing_dates",
    "risk.pest_disease",
    "risk.market_costs",
    "risk.water_rules",
    "risk.equipment",
)


def _format_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return f"{value:.1f}"
    return str(value)


def evidence_for(strategy, period: str) -> list[dict]:
    evidence = []
    for indicator in strategy.indicators:
        if indicator.band == "Unknown":
            continue
        if indicator.median is None:
            value_range = indicator.band
        else:
            low = _format_value(indicator.min)
            high = _format_value(indicator.max)
            value_range = low if low == high or high is None else f"{low}–{high}"
        evidence.append(
            {
                "indicator": indicator.id,
                "value_range": value_range,
                "unit": indicator.unit,
                "dataset_badge": indicator.status,
                "period": period,
                "n_windows": indicator.n_windows,
                "status": indicator.status,
                "dataset": indicator.dataset,
                "band": indicator.band,
            }
        )
    return evidence


def _why(strategy, hypothesis: str | None, evidence: list[dict], period: str) -> list[str]:
    if strategy.kind.value == "existing":
        base = text("why.existing")
    elif hypothesis:
        base = hypothesis
    elif strategy.kind.value == "custom":
        base = text("why.custom")
    elif strategy.kind.value == "proposed":
        base = text("why.proposed")
    else:
        base = text("why.chosen")
    statements = [base]
    for item in evidence:
        if len(statements) >= 4:
            break
        statements.append(
            text(
                "why.evidence",
                band=item["band"],
                indicator=item["indicator"],
                dataset=item["dataset"],
                period=period,
                evidence_id=item["indicator"],
            )
        )
    return statements


def _benefits(strategy, existing, period: str) -> list[str]:
    if strategy.id == existing.id:
        return []
    current = {indicator.id: indicator for indicator in existing.indicators}
    benefits: list[str] = []
    candidate = {indicator.id: indicator for indicator in strategy.indicators}
    current_etc = current.get("etc_year_mm")
    candidate_etc = candidate.get("etc_year_mm")
    if (
        current_etc
        and candidate_etc
        and current_etc.median
        and candidate_etc.median is not None
        and candidate_etc.median <= current_etc.median * 0.9
    ):
        benefits.append(text("benefit.lower_etc", period=period, evidence_id="etc_year_mm"))
    for indicator_id in (
        "temp_in_range_pct",
        "days_above_tmax",
        "days_below_tmin",
        "heat_days",
        "cold_days",
        "frost_days",
        "ph_fit",
        "salinity_fit",
    ):
        before, after = current.get(indicator_id), candidate.get(indicator_id)
        if (
            not before
            or not after
            or before.band not in _BAND_ORDER
            or after.band not in _BAND_ORDER
        ):
            continue
        if _BAND_ORDER[after.band] > _BAND_ORDER[before.band]:
            benefits.append(
                text(
                    "benefit.improved_band",
                    indicator=indicator_id,
                    band=after.band,
                    dataset=after.dataset or "the listed data",
                    period=period,
                    evidence_id=indicator_id,
                )
            )
    return benefits


def _information_gaps(flags: list[str]) -> list[str]:
    gaps = []
    for flag in sorted(set(flags)):
        message = text(f"flag.{flag}")
        if message == f"flag.{flag}":
            message = text("flag.generic", flag=flag)
        gaps.append(message)
    return gaps


def _risks(flags: list[str]) -> list[str]:
    risks = [text(key) for key in _FIXED_RISKS]
    for flag in (
        "soil_unknown",
        "soil_partial",
        "salinity_unassessed",
        "rice_gross_water_underestimated",
        "season_overlap",
    ):
        if flag in flags:
            risks.append(text(f"risk.{flag}"))
    return risks


def add_explanations(strategies: list, templates: list[dict], period: str) -> list:
    """Return copied strategy models with the five challenge explanation blocks."""
    by_id = {template.get("id"): template for template in templates}
    existing = next(
        (strategy for strategy in strategies if strategy.kind.value == "existing"), None
    )
    explained = []
    for strategy in strategies:
        template = by_id.get(strategy.id, {})
        name = template.get("hypothesis")
        evidence = evidence_for(strategy, period)
        updated = strategy.model_copy(
            update={
                "why_suggested": _why(strategy, name, evidence, period),
                "evidence": evidence,
                "benefits": _benefits(strategy, existing, period) if existing else [],
                "information_gaps": _information_gaps(strategy.flags),
                "risks_for_local_review": _risks(strategy.flags),
            }
        )
        explained.append(updated)
    return explained
