"""analysis/proposed.py — Engine-proposed candidate rotation generator (Phase 8)."""

from __future__ import annotations

import itertools
from typing import Any

import pandas as pd

from .compare import overall_number, priority_score
from .priorities import PRIORITY_INDICATORS, build_weights


def _get_crops_by_slot(crop_table: dict | Any) -> tuple[list[str], list[str]]:
    """Return (winter_crops, summer_crops) available in crop reference."""
    doc = crop_table.doc if hasattr(crop_table, "doc") else crop_table
    crops = doc.get("crops", [])
    winter = [
        c["crop_id"]
        for c in crops
        if c.get("usual_slot") == "winter" and c.get("crop_id") != "fallow"
    ]
    summer = [
        c["crop_id"]
        for c in crops
        if c.get("usual_slot") == "summer" and c.get("crop_id") != "fallow"
    ]
    return winter, summer


def enumerate_candidate_sequences(
    crop_table: dict | Any,
    horizon: int = 1,
    first_slot: str = "winter",
    existing_sequence: list[dict] | None = None,
) -> list[list[dict]]:
    """Enumerate all valid crop sequences honoring the slot and rotation constraints.

    Constraint: No identical crop in consecutive same-type slots.
    The sequence must also differ from existing_sequence.
    """
    winter_crops, summer_crops = _get_crops_by_slot(crop_table)
    if not winter_crops or not summer_crops:
        return []

    # Sequence of slots across years
    slots_per_year = ["winter", "summer"] if first_slot == "winter" else ["summer", "winter"]

    # Enumerate winter sequences for H years where winter[y] != winter[y-1]
    winter_seqs = []
    for p in itertools.product(winter_crops, repeat=horizon):
        if all(p[i] != p[i - 1] for i in range(1, len(p))):
            winter_seqs.append(p)

    # Enumerate summer sequences for H years where summer[y] != summer[y-1]
    summer_seqs = []
    for p in itertools.product(summer_crops, repeat=horizon):
        if all(p[i] != p[i - 1] for i in range(1, len(p))):
            summer_seqs.append(p)

    existing_tuples = None
    if existing_sequence:
        existing_tuples = tuple(s.get("crop_id", s.get("crop")) for s in existing_sequence)

    candidates = []
    for w_seq in winter_seqs:
        for s_seq in summer_seqs:
            full_seq = []
            crop_tuple = []
            for y in range(1, horizon + 1):
                for slot in slots_per_year:
                    cid = w_seq[y - 1] if slot == "winter" else s_seq[y - 1]
                    full_seq.append({"slot": slot, "year": y, "crop_id": cid})
                    crop_tuple.append(cid)
            if existing_tuples and tuple(crop_tuple) == existing_tuples:
                continue
            candidates.append(full_seq)

    return candidates


def propose_candidate_strategies(
    crop_table: dict | Any,
    existing_sequence: list[dict],
    horizon: int,
    daily_climate: pd.DataFrame,
    soil_record: dict,
    latitude: float,
    ranked_priorities: list[str] | None = None,
    skipped_priorities: list[str] | None = None,
    water_availability: str = "unknown",
    rules: list[dict] | None = None,
    thresholds: dict | None = None,
    bands: dict | None = None,
    flags: list[str] | None = None,
    max_candidates: int = 3,
) -> list[dict]:
    """Evaluate candidate sequences and return the top 2-3 as 'candidates to explore'."""
    from .evaluate import _metric_values

    doc = crop_table.doc if hasattr(crop_table, "doc") else crop_table
    crops = {c["crop_id"]: c for c in doc.get("crops", [])}
    first_slot = existing_sequence[0].get("slot", "winter") if existing_sequence else "winter"

    candidate_seqs = enumerate_candidate_sequences(
        crop_table, horizon=horizon, first_slot=first_slot, existing_sequence=existing_sequence
    )
    if not candidate_seqs:
        raise ValueError("No candidate sequences could be generated from available crops.")

    thresholds = thresholds or {}
    bands = bands or {}
    stage_split_defaults = doc.get("defaults", {}).get("stage_split_if_missing") or {
        "ini": 0.15,
        "dev": 0.25,
        "mid": 0.40,
        "late": 0.20,
    }

    # Precompute per-crop metrics for all crops in crop table once
    crop_metrics: dict[str, dict] = {}
    for cid, crop_data in crops.items():
        metrics, _, _, _ = _metric_values(
            daily_climate,
            crop_data,
            latitude,
            soil_record,
            water_availability,
            thresholds,
            bands,
            stage_split_defaults,
        )
        crop_metrics[cid] = metrics

    weights = build_weights(ranked_priorities or [], skipped_priorities or [])

    # Evaluate each candidate sequence
    scored_candidates = []
    for seq in candidate_seqs:
        # Rank only from the priority indicators shown in the final comparison.
        p_scores: dict[str, float | None] = {}
        for priority, ind_ids in PRIORITY_INDICATORS.items():
            priority_bands = []
            for step in seq:
                cid = step["crop_id"]
                if cid not in crop_metrics:
                    continue
                cm = crop_metrics[cid]
                for ind_id in ind_ids:
                    if ind_id in cm and "band" in cm[ind_id]:
                        priority_bands.append(cm[ind_id]["band"])
            score = priority_score(priority_bands)
            p_scores[priority] = score

        overall_val, _ = overall_number(p_scores, weights)
        scored_candidates.append(
            {
                "sequence": seq,
                "overall_value": overall_val,
                "priority_scores": p_scores,
            }
        )

    # Stable sort on the scored priority value; unsupported rules never affect ranking.
    def sort_key(c):
        val = c["overall_value"]
        return (0 if val is not None else 1, -(val if val is not None else 0.0))

    scored_candidates.sort(key=sort_key)

    # Select top max_candidates distinct sequences
    selected = scored_candidates[:max_candidates]
    if len(selected) < 2:
        raise ValueError("Could not find at least two viable candidate strategies.")

    # Format into strategy alternatives
    alternatives = []
    for idx, cand in enumerate(selected, 1):
        seq = cand["sequence"]
        crop_names = []
        for s in seq:
            c = crops.get(s["crop_id"], {})
            name = (c.get("names") or {}).get("en") or s["crop_id"].replace("_", " ").title()
            crop_names.append(name)
        display_name = f"Candidate {idx} ({' / '.join(crop_names)})"
        alternatives.append(
            {
                "id": f"proposed-{idx}",
                "name": display_name,
                "kind": "proposed",
                "sequence": seq,
            }
        )

    return alternatives
