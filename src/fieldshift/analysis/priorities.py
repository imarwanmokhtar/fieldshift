"""analysis/priorities.py — ROC weights + indicator→priority mapping (Part 7.7)."""
from __future__ import annotations

PRIORITY_INDICATORS = {
    "reduce_water_use": ["water_demand_rel", "irrigation_dependence", "water_vs_access"],
    "support_soil_health": ["ph_fit", "salinity_fit"],
    "improve_climate_resilience": [
        "heat_days", "cold_days", "frost_days", "days_above_tmax",
        "drought_sensitivity",
    ],
    "maintain_productivity": ["temp_in_range_pct", "days_above_tmax", "ph_fit", "salinity_fit"],
    "budget_market": [],
}


def roc_weights(n: int) -> list[float]:
    """Rank-order-centroid weights for n ranked priorities."""
    if n <= 0:
        return []
    out = []
    for i in range(1, n + 1):
        w = (1.0 / n) * sum(1.0 / k for k in range(i, n + 1))
        out.append(w)
    return out


def build_weights(ranked: list[str], skipped: list[str] | None = None) -> dict[str, float]:
    """Apply ROC to ranked priorities and equal weights to skipped priorities."""
    skipped = list(skipped or [])
    known = list(PRIORITY_INDICATORS)
    ranked = list(dict.fromkeys(ranked))
    if any(p not in PRIORITY_INDICATORS for p in ranked + skipped):
        raise ValueError("unknown priority")
    if set(ranked) & set(skipped):
        raise ValueError("a priority cannot be both ranked and skipped")
    skipped += [p for p in known if p not in ranked and p not in skipped]
    skipped = list(dict.fromkeys(skipped))
    n = len(ranked)
    weights = {p: 0.0 for p in PRIORITY_INDICATORS}
    if n == 0:
        for p in skipped:
            weights[p] = 1.0 / max(len(skipped), 1)
        return weights
    rw = roc_weights(n)
    ranked_share = n / (n + len(skipped))
    for i, p in enumerate(ranked):
        if p in weights:
            weights[p] = rw[i] * ranked_share if i < len(rw) else 0.0
    skipped_weight = (1 - ranked_share) / len(skipped) if skipped else 0.0
    for p in skipped:
        weights[p] = skipped_weight
    return weights
