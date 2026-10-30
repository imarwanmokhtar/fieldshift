"""analysis/compare.py — bands, composite, tie handling, equal-weights stability (Part 7.7)."""
from __future__ import annotations

BAND_TO_NUM = {"Good": 1.0, "Moderate": 0.5, "Similar": 0.5,
               "Poor": 0.0, "Unknown": None}


def priority_score(indicator_bands: list[str]) -> float | None:
    """Mean of available indicator numbers (Unknown excluded). None if none available."""
    nums = [BAND_TO_NUM[b] for b in indicator_bands if BAND_TO_NUM.get(b) is not None]
    if not nums:
        return None
    return sum(nums) / len(nums)


def overall_number(priority_scores: dict[str, float | None],
                   weights: dict[str, float]) -> tuple[float | None, str]:
    """Returns (value, basis). value=None if suppressed."""
    data_weight = 0.0
    total_weight = 0.0
    numerator = 0.0
    for p, sc in priority_scores.items():
        w = weights.get(p, 0.0)
        total_weight += w
        if sc is not None and w > 0:
            numerator += w * sc
            data_weight += w
    if total_weight == 0:
        return None, "no priorities with data"
    if data_weight / total_weight < 0.5:
        return None, "not enough data for an overall comparison"
    value = numerator / data_weight
    basis = (
        f"{sum(1 for s in priority_scores.values() if s is not None)} "
        f"of {len(priority_scores)} priorities had data"
    )
    return value, basis


def overall_band(value: float | None) -> str:
    if value is None:
        return "Unknown"
    if value >= 0.67:
        return "Good"
    if value >= 0.34:
        return "Moderate"
    return "Poor"


def too_close(a: float | None, b: float | None, tol: float = 0.05) -> bool:
    if a is None or b is None:
        return False
    return abs(a - b) < tol


def rank_strategies(strategies: list[dict]) -> list[str]:
    """Sort by overall value desc; None last."""
    def key(s):
        v = s.get("overall_value")
        return (0 if v is not None else 1, -(v if v is not None else 0))
    return [s["id"] for s in sorted(strategies, key=key)]


def equal_weights_order(strategies: list[dict], all_priorities: list[str]) -> list[str]:
    eq = {p: 1.0 / len(all_priorities) for p in all_priorities}
    enriched = []
    for s in strategies:
        # recompute overall with equal weights using stored priority_scores
        ps = s.get("priority_scores", {})
        val, _ = overall_number(ps, eq)
        enriched.append({"id": s["id"], "overall_value": val})
    return rank_strategies(enriched)
