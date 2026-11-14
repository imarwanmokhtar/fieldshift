"""Water-saving farming practices that keep the farmer's current crops.

A practice option is the current rotation grown with better practices. Each
practice reduces the irrigation water of the crops it applies to. Values come
from practices.json (illustrative, TODO-verify) and scoring always uses the
LOW end of each reported range, so the benefit is not overstated.
"""

from __future__ import annotations

import json
from pathlib import Path

from .schemas import FarmProfile

PRACTICES: dict = {k: v for k, v in json.loads((Path(__file__).parent / "practices.json").read_text("utf-8")).items()
                   if not k.startswith("_")}

# Irrigation methods where field levelling and beds make sense. Unknown counts as
# surface irrigation, the usual method in the Nile Delta.
SURFACE_METHODS = {"flood", "furrow", "other", None, ""}


def _applies_to(practice: dict, crops: set[str]) -> set[str]:
    return set(crops) if practice["crops"] == "all" else crops & set(practice["crops"])


def applicable_practices(profile: FarmProfile, crops: set[str], salinity_level: int) -> tuple[list[str], list[str]]:
    """Practices that fit this field and these crops.

    Returns (practice ids to apply, practice ids skipped because of salt).
    """
    surface = profile.irrigation_method in SURFACE_METHODS
    chosen, skipped_salt = [], []
    for pid, pr in PRACTICES.items():
        if not _applies_to(pr, crops):
            continue
        if pr["surface_irrigation_only"] and not surface:
            continue
        if pr.get("skip_if_salinity") and salinity_level > 0:
            skipped_salt.append(pid)
            continue
        chosen.append(pid)
    return chosen, skipped_salt


def water_factors(practice_ids: list[str], crops: set[str]) -> dict[str, float]:
    """Multiplier on each crop's irrigation water, using the low end of each saving range.

    Savings from several practices on one crop combine multiplicatively
    (e.g. 15% and 20% -> 0.85 * 0.80 = 0.68 of the original water).
    """
    factors = {c: 1.0 for c in crops}
    for pid in practice_ids:
        pr = PRACTICES[pid]
        low = pr["water_saving_pct"][0] / 100
        for c in _applies_to(pr, crops):
            factors[c] *= 1 - low
    return factors


def missing_equipment(practice_id: str, equipment: list[str]) -> bool:
    need = PRACTICES[practice_id]["needs_equipment"]
    return bool(need) and not any(e in equipment for e in need)
