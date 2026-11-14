"""Candidate rotations, hard-constraint filtering, scoring and strategy selection.

A rotation is two years of (winter crop, summer crop): 4 slots. Every
candidate built from the allowed crops is scored on the same criteria, so the
"current", "soil", "water" and the farmer's own choice are always comparable.
All scores are 0-100 where higher is better (so "water" 100 = uses little water).
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

from .features import CROPS, ClimateFeatures, crop_metrics, crop_season_dates
from .practices import PRACTICES, applicable_practices, missing_equipment, water_factors
from .schemas import CRITERIA, CropMetrics, FarmProfile, Fact, Slot, Strategy
from .texts import STRATEGY_NAMES, fact

CRITERIA_FOR_PRIORITY = {
    "save_water": "water", "higher_income": "income", "better_soil": "soil",
    "lower_costs": "cost", "lower_risk": "risk", "fodder": "forage",
}
RANK_WEIGHTS = [0.40, 0.25, 0.15]      # the remaining 0.20 is spread over the other criteria

WATER_SCALE_M3 = 14000.0               # m3/feddan/year that scores 0 on "water"
DEFAULT_ROTATION = ("wheat", "rice")   # common Dakahlia rotation, used only when history is unknown
MAX_CHANGES = {"stick_to_known": 2, "small_trial": 3, "ready_to_change": 4, None: 4}
NEW_CROP_PENALTY = {"stick_to_known": 15, "small_trial": 8, "ready_to_change": 3, None: 8}
TRANSITION_MIN_DAYS = -15              # allow ~2 weeks overlap (relay planting, early harvest)


def weights_from_priorities(priorities: list[str], all_criteria: list[str] | None = None) -> dict[str, float]:
    all_criteria = all_criteria or CRITERIA
    w = {c: 0.0 for c in all_criteria}
    for rank, p in enumerate(priorities[:3]):
        if p in CRITERIA_FOR_PRIORITY:
            w[CRITERIA_FOR_PRIORITY[p]] += RANK_WEIGHTS[rank]
    rest = [c for c in all_criteria if w[c] == 0.0]
    leftover = 1.0 - sum(w.values())
    for c in rest:
        w[c] = leftover / max(len(rest), 1)
    return {c: round(v, 4) for c, v in w.items()}


# ---------------------------------------------------------------- context

@dataclass
class Context:
    profile: FarmProfile
    clim: ClimateFeatures
    metrics: dict[str, CropMetrics]
    weights: dict[str, float]
    history_crops: set[str]
    current: tuple[str, str]                       # (winter, summer)
    history_notes: list[Fact] = field(default_factory=list)
    gaez: dict[str, float] = field(default_factory=dict)          # crop -> 0..1
    gaez_source: str = "approx"


def _salinity_level(p: FarmProfile) -> int:
    """0 none / 1 some / 2 severe, from the soil and water answers."""
    if p.salinity == "large_areas" or p.water_quality == "salty":
        return 2
    if p.salinity == "some_spots" or p.water_quality == "slightly_salty":
        return 1
    return 0


def allowed_crops(p: FarmProfile, metrics: dict[str, CropMetrics]) -> dict[str, list[str]]:
    """Hard constraints. Returns crop ids per season that may be suggested."""
    sal = _salinity_level(p)
    out: dict[str, list[str]] = {"winter": [], "summer": []}
    for cid, c in CROPS.items():
        if cid == "other_vegetables" or cid not in metrics:
            continue      # too vague to recommend; still scored if it is the farmer's own crop
        if sal == 2 and c["salinity_tolerance"] == "sensitive":
            continue
        if p.soil_texture in ("clay", "loam", "sandy") and c["soil_fit"][p.soil_texture] < 0.4:
            continue
        if p.water_source == ["rain_only"] and metrics[cid].gross_m3_per_feddan > 3500:
            continue
        if p.water_reliability == "rarely" and cid == "rice":
            continue
        out[c["season"]].append(cid)
    return out


def resolve_current(p: FarmProfile) -> tuple[tuple[str, str], list[Fact]]:
    """The farmer's current (winter, summer) pair from last_crop / prev_crop."""
    notes: list[Fact] = []
    winter = summer = None
    for cs in (p.last_crop, p.prev_crop):
        if cs is None:
            continue
        cid = cs.crop
        if cid == "fallow":
            season = cs.season
        elif cid in CROPS:
            season = cs.season or CROPS[cid]["season"]
            # A crop declared in the "wrong" season is placed in its own season.
            if CROPS[cid]["season"] != season and cid != "other_vegetables":
                season = CROPS[cid]["season"]
        else:
            notes.append(fact("history_unsupported", crop=cid))
            continue
        if season == "winter" and winter is None:
            winter = cid
        elif season == "summer" and summer is None:
            summer = cid
    if winter is None and summer is None:
        notes.append(fact("history_assumed", crops=list(DEFAULT_ROTATION)))
        return DEFAULT_ROTATION, notes
    if winter is None or summer is None:
        filled = (winter or DEFAULT_ROTATION[0], summer or DEFAULT_ROTATION[1])
        notes.append(fact("history_assumed", crops=list(filled)))
        return filled, notes
    return (winter, summer), notes


# ---------------------------------------------------------------- scoring

def _transition_gap(winter: str, summer: str) -> int | None:
    """Days between the end of a winter crop and the next summer planting."""
    if winter == "fallow" or summer == "fallow":
        return None
    _, w_end = crop_season_dates(CROPS[winter], 2023)
    s_start, _ = crop_season_dates(CROPS[summer], 2024)
    return (s_start - w_end).days


def _summer_to_winter_gap(summer: str, winter: str) -> int | None:
    if winter == "fallow" or summer == "fallow":
        return None
    _, s_end = crop_season_dates(CROPS[summer], 2024)
    w_start, _ = crop_season_dates(CROPS[winter], 2024)
    return (w_start - s_end).days


def feasible(rot: tuple[str, str, str, str]) -> bool:
    w1, s1, w2, s2 = rot
    for a, b in ((w1, s1), (w2, s2)):
        g = _transition_gap(a, b)
        if g is not None and g < TRANSITION_MIN_DAYS:
            return False
    for a, b in ((s1, w2), (s2, w1)):
        g = _summer_to_winter_gap(a, b)
        if g is not None and g < TRANSITION_MIN_DAYS:
            return False
    return True


@dataclass
class Scored:
    rot: tuple[str, str, str, str]
    scores: dict[str, int]
    metrics: dict[str, float]
    evidence: list[Fact]
    benefits: list[Fact]
    gaps: list[Fact]
    risks: list[Fact]
    changes: int
    practices: list[str] = field(default_factory=list)


def _clamp(x: float) -> int:
    return int(round(max(0.0, min(100.0, x))))


def score_rotation(rot: tuple[str, str, str, str], ctx: Context,
                   water_factor: dict[str, float] | None = None) -> Scored:
    """Score a rotation. `water_factor` scales a crop's irrigation water (practice options)."""
    p = ctx.profile
    wf = water_factor or {}

    def gross(c: str) -> float:
        return ctx.metrics[c].gross_m3_per_feddan * wf.get(c, 1.0)

    slots = [("winter", rot[0]), ("summer", rot[1]), ("winter", rot[2]), ("summer", rot[3])]
    crops = [c for _, c in slots if c != "fallow"]
    m = ctx.metrics
    evidence: list[Fact] = []
    risks: list[Fact] = []

    # --- water (m3 per feddan per year, averaged over the two years)
    water_m3 = sum(gross(c) for c in crops) / 2
    water = _clamp(100 * (1 - water_m3 / WATER_SCALE_M3))
    evidence.append(fact("water_total", m3=int(round(water_m3, -1))))

    # --- heat
    heat_days = sum(m[c].heat_days for c in crops) / 2
    heat = _clamp(100 - 2 * heat_days)

    # --- bare days per year (time not covered by a crop)
    covered = sum(CROPS[c]["season_days"] for c in crops) / 2
    bare_days = max(0.0, 365 - covered)
    evidence.append(fact("bare_days", days=int(round(bare_days))))

    # --- soil
    soil = 50.0
    low_fert = "low_fertility" in p.soil_issues or p.fertilizer_level == "high"
    hard = "hard_layer" in p.soil_issues
    for _, c in slots:
        if c == "fallow":
            continue
        cc = CROPS[c]
        if cc["n_fixing"]:
            soil += 12 * (1.5 if low_fert else 1.0)
        soil += {"high": 6, "medium": 3, "low": 0}[cc["organic_matter"]]
        if cc["deep_root"]:
            soil += 3 * (2 if hard else 1)
    cyc = slots + slots[:1]
    cereal_pairs = 0
    for (_, a), (_, b) in zip(cyc, cyc[1:]):
        if a == "fallow" or b == "fallow":
            continue
        fa, fb = CROPS[a]["family"], CROPS[b]["family"]
        if fa == "cereal" and fb == "cereal":
            soil -= 4
            cereal_pairs += 1
        if fa in CROPS[b]["pest_break_for"]:
            soil += 4
    for season, a, b in (("winter", rot[0], rot[2]), ("summer", rot[1], rot[3])):
        if a == b and a != "fallow" and not CROPS[a]["n_fixing"]:
            soil -= 6
            risks.append(fact("monoculture", crop=a, season=season))
    soil -= bare_days / 10
    soil = _clamp(soil)
    if cereal_pairs >= 3:
        risks.append(fact("cereal_after_cereal"))

    # --- income (relative index, scaled by suitability and soil fit)
    inc = []
    for _, c in slots:
        if c == "fallow":
            inc.append(0.0)
            continue
        cc = CROPS[c]
        suit = ctx.gaez.get(c, cc["gaez_suitability_approx"])
        fit = cc["soil_fit"].get(p.soil_texture, 0.9) if p.soil_texture in ("clay", "loam", "sandy") else 0.9
        inc.append(cc["income_index"] * (0.7 + 0.3 * suit) * (0.6 + 0.4 * fit))
    income = _clamp(100 * sum(inc) / len(inc) / 0.85)

    # --- cost
    cost_idx = sum(CROPS[c]["input_cost_index"] if c != "fallow" else 0.0 for _, c in slots) / 4
    cost = 100 - 100 * cost_idx
    if p.water_cost == "heavy" or "groundwater_well" in p.water_source:
        cost -= 30 * water_m3 / WATER_SCALE_M3
    elif p.water_cost == "somewhat":
        cost -= 15 * water_m3 / WATER_SCALE_M3
    cost = _clamp(cost)

    # --- forage
    forage = _clamp(100 * sum(CROPS[c]["forage_value"] if c != "fallow" else 0 for _, c in slots) / 4)

    # --- risk
    risk = 100.0
    new = sorted({c for c in crops if c not in ctx.history_crops})
    for c in new:
        risk -= NEW_CROP_PENALTY.get(p.risk_tolerance, 8)
        risks.append(fact("new_crop", crop=c))
    uniq = sorted(set(crops))
    vol = sum(CROPS[c]["price_volatility"] for c in crops) / max(len(crops), 1)
    risk -= 20 * vol
    for c in uniq:
        if CROPS[c]["price_volatility"] >= 0.7:
            risks.append(fact("price_swings", crop=c))
    sal = _salinity_level(p)
    if sal:
        for c in uniq:
            t = CROPS[c]["salinity_tolerance"]
            if c == "rice":
                continue   # flooded rice washes salt down; handled in the crop notes
            pen = {"sensitive": 15, "moderately_sensitive": 6}.get(t, 0) * (1 if sal == 2 else 0.5)
            if pen:
                risk -= pen
                if t == "sensitive" or sal == 2:
                    risks.append(fact("salt_sensitive", crop=c))
    if p.water_reliability in ("often_late", "rarely"):
        for c in uniq:
            if gross(c) > 5000:
                risk -= 10
                risks.append(fact("water_unreliable", crop=c))
    for c in uniq:
        if m[c].heat_days >= 10:
            risk -= 5
            risks.append(fact("heat_exposure", crop=c, days=int(round(m[c].heat_days))))
    if "waterlogging" in p.soil_issues or p.drainage == "several_days":
        for c in uniq:
            if CROPS[c]["waterlogging_tolerance"] == "low":
                risk -= 3
        bad = [c for c in uniq if CROPS[c]["waterlogging_tolerance"] == "low"]
        if bad:
            risks.append(fact("waterlogging", crop=bad[0]))
    if p.soil_texture in ("clay", "loam", "sandy"):
        for c in uniq:
            if CROPS[c]["soil_fit"][p.soil_texture] < 0.7:
                risk -= 5
                risks.append(fact("soil_fit_poor", crop=c, texture=p.soil_texture))
    if p.equipment == ["hand_labor"]:
        for c in uniq:
            if CROPS[c]["mechanization_need"] >= 0.7:
                risk -= 5
                risks.append(fact("needs_machinery", crop=c))
    for a, b in ((rot[0], rot[1]), (rot[2], rot[3])):
        g = _transition_gap(a, b)
        if g is not None and g < 0:
            risk -= 6
            risks.append(fact("tight_transition", crop_a=a, crop_b=b))
    if "rice" in crops:
        risk -= 3
        risks.append(fact("rice_regulated"))
    risk = _clamp(risk)

    # --- crop-level evidence
    for c in uniq:
        evidence.append(fact("crop_water", crop=c, season=CROPS[c]["season"], m3=int(round(gross(c), -1))))
        if CROPS[c]["n_fixing"]:
            evidence.append(fact("n_fixing", crop=c))
        suit = ctx.gaez.get(c, CROPS[c]["gaez_suitability_approx"])
        evidence.append(fact("gaez", crop=c, score=int(round(suit * 100))))
    for (sa, a), (sb, b) in zip(cyc, cyc[1:]):
        if a != "fallow" and b != "fallow" and CROPS[a]["family"] in CROPS[b]["pest_break_for"]:
            evidence.append(fact("pest_break", crop=b, prev=a))
            break

    scores = {"water": water, "heat": heat, "soil": soil, "income": income,
              "cost": cost, "risk": risk, "forage": forage}
    scores["overall"] = _clamp(sum(ctx.weights[k] * scores[k] for k in CRITERIA))
    cur = (ctx.current[0], ctx.current[1], ctx.current[0], ctx.current[1])
    changes = sum(1 for a, b in zip(rot, cur) if a != b)
    metrics = {"water_m3_per_feddan_year": round(water_m3, 0), "bare_days_per_year": round(bare_days, 0),
               "heat_days_per_year": round(heat_days, 1),
               "water_m3_field_year": round(water_m3 * p.area_feddan, 0)}
    return Scored(rot=rot, scores=scores, metrics=metrics, evidence=evidence, benefits=[], gaps=[],
                  risks=_dedupe(risks), changes=changes)


def _dedupe(facts: list[Fact]) -> list[Fact]:
    seen, out = set(), []
    for f in facts:
        key = (f.code, tuple(sorted((k, str(v)) for k, v in f.params.items())))
        if key not in seen:
            seen.add(key)
            out.append(f)
    return out


# ---------------------------------------------------------------- comparison facts

def _compare_facts(s: Scored, base: Scored, ctx: Context) -> list[Fact]:
    """Benefits of `s` relative to the current rotation `base`."""
    b: list[Fact] = []
    if s.rot == base.rot:
        b.append(fact("familiar"))
    dw = base.metrics["water_m3_per_feddan_year"] - s.metrics["water_m3_per_feddan_year"]
    if dw >= 200:
        b.append(fact("saves_water", m3=int(round(dw, -1))))
    if s.scores["soil"] - base.scores["soil"] >= 8:
        b.append(fact("builds_soil"))
    dbare = base.metrics["bare_days_per_year"] - s.metrics["bare_days_per_year"]
    if dbare >= 15:
        b.append(fact("fewer_bare_days", days=int(round(dbare))))
    if s.scores["income"] - base.scores["income"] >= 5:
        b.append(fact("more_income"))
    if s.scores["cost"] - base.scores["cost"] >= 5:
        b.append(fact("lower_cost"))
    if s.scores["heat"] - base.scores["heat"] >= 5:
        b.append(fact("less_heat"))
    for c in sorted(set(s.rot) - {"fallow"}):
        if CROPS[c]["forage_value"] >= 0.6:
            b.append(fact("forage", crop=c))
        if CROPS[c]["government_procurement"]:
            b.append(fact("govt_buyer", crop=c))
    return b


def _water_vs_current(s: Scored, base: Scored) -> Fact | None:
    bw, sw = base.metrics["water_m3_per_feddan_year"], s.metrics["water_m3_per_feddan_year"]
    if (s.rot == base.rot and not s.practices) or bw <= 0:
        return None
    pct = int(round(abs(sw - bw) / bw * 100))
    if pct < 3:
        return None
    return fact("water_less" if sw < bw else "water_more", pct=pct)


# ---------------------------------------------------------------- selection

def build_context(profile: FarmProfile, clim: ClimateFeatures, gaez: dict[str, float] | None = None,
                  gaez_source: str = "approx") -> Context:
    metrics = {cid: crop_metrics(cid, clim, profile.irrigation_method) for cid in CROPS}
    current, notes = resolve_current(profile)
    history = {c for c in current if c != "fallow"}
    for cs in (profile.last_crop, profile.prev_crop):
        if cs and cs.crop in CROPS:
            history.add(cs.crop)
    return Context(profile=profile, clim=clim, metrics=metrics,
                   weights=weights_from_priorities(profile.priorities), history_crops=history,
                   current=current, history_notes=notes, gaez=gaez or {}, gaez_source=gaez_source)


def candidate_rotations(ctx: Context) -> list[Scored]:
    allowed = allowed_crops(ctx.profile, ctx.metrics)
    max_changes = MAX_CHANGES.get(ctx.profile.risk_tolerance, 4)
    out = []
    for w1, s1, w2, s2 in itertools.product(allowed["winter"], allowed["summer"], allowed["winter"], allowed["summer"]):
        rot = (w1, s1, w2, s2)
        if not feasible(rot):
            continue
        sc = score_rotation(rot, ctx)
        if sc.changes > max_changes:
            continue
        out.append(sc)
    return out


def _to_strategy(kind: str, s: Scored, base: Scored, ctx: Context, idx: int) -> Strategy:
    slots = [Slot(year=1, season="winter", crop=s.rot[0]), Slot(year=1, season="summer", crop=s.rot[1]),
             Slot(year=2, season="winter", crop=s.rot[2]), Slot(year=2, season="summer", crop=s.rot[3])]
    pairs = [(sl.season, sl.crop) for sl in slots]
    evidence = list(s.evidence)
    wv = _water_vs_current(s, base)
    if wv:
        evidence.insert(1, wv)
    if ctx.clim.hot_days_trend_per_year > 0.1:
        s.risks.append(fact("heat_rising", per_decade=round(ctx.clim.hot_days_trend_per_year * 10, 1)))
    return Strategy(
        id=kind if kind != "custom" else f"custom-{idx}",
        kind=kind,  # type: ignore[arg-type]
        name=STRATEGY_NAMES[kind]["en"], name_ar=STRATEGY_NAMES[kind]["ar"],
        sequence=[f"{c} ({season})" for season, c in pairs],
        slots=slots, scores=s.scores, metrics=s.metrics,
        evidence=evidence, benefits=_compare_facts(s, base, ctx), gaps=list(s.gaps), risks=_dedupe(s.risks),
        confidence="medium", confidence_score=0, changes_from_current=s.changes, practices=list(s.practices),
    )


def select_strategies(ctx: Context) -> tuple[list[Strategy], str]:
    cur_rot = (ctx.current[0], ctx.current[1], ctx.current[0], ctx.current[1])
    base = score_rotation(cur_rot, ctx)
    cands = [c for c in candidate_rotations(ctx) if c.rot != cur_rot]
    chosen: list[tuple[str, Scored]] = [("current", base)]
    practice = practice_option(ctx, cur_rot)
    if practice is not None:
        chosen.append(("practice", practice))

    def canon(rot: tuple[str, str, str, str]) -> tuple:
        # The same two years in the opposite order is the same rotation.
        return tuple(sorted([(rot[0], rot[1]), (rot[2], rot[3])]))

    used = {canon(cur_rot)}

    def pick(kind: str, key) -> None:
        pool = [c for c in cands if canon(c.rot) not in used]
        if not pool:
            return
        best = max(pool, key=key)
        if kind == "balanced" and any(best.scores["overall"] <= s.scores["overall"]
                                      for k, s in chosen if k not in ("current", "practice")):
            return   # an option already shown is at least as good overall: no need for a 4th card
        chosen.append((kind, best))
        used.add(canon(best.rot))

    pick("soil", lambda c: (0.7 * c.scores["soil"] + 0.3 * c.scores["overall"], c.scores["overall"]))
    pick("water", lambda c: (0.7 * c.scores["water"] + 0.3 * c.scores["overall"], c.scores["overall"]))
    top = ctx.profile.priorities[0] if ctx.profile.priorities else None
    if top == "higher_income":
        pick("income", lambda c: (0.7 * c.scores["income"] + 0.3 * c.scores["overall"], c.scores["overall"]))
    elif top == "fodder":
        pick("fodder", lambda c: (0.7 * c.scores["forage"] + 0.3 * c.scores["overall"], c.scores["overall"]))
    pick("balanced", lambda c: (c.scores["overall"], c.scores["risk"]))

    strategies = [_to_strategy(kind, s, base, ctx, i) for i, (kind, s) in enumerate(chosen)]
    recommended = max(strategies, key=lambda st: (st.scores["overall"], st.kind == "current"))
    return strategies, recommended.id


def practice_option(ctx: Context, rot: tuple[str, str, str, str]) -> Scored | None:
    """The same rotation grown with the water-saving practices that fit this field.

    Returns None when no practice applies (e.g. drip irrigation and no rice).
    """
    crops = {c for c in rot if c != "fallow"}
    ids, skipped_salt = applicable_practices(ctx.profile, crops, _salinity_level(ctx.profile))
    if not ids:
        return None
    sc = score_rotation(rot, ctx, water_factors(ids, crops))
    sc.practices = ids
    practice_facts = []
    for pid in ids:
        lo, hi = PRACTICES[pid]["water_saving_pct"]
        practice_facts.append(fact(f"practice_{pid}", low=lo, high=hi))
        if missing_equipment(pid, ctx.profile.equipment):
            sc.risks.append(fact(f"practice_{pid}_service"))
    # Keep the total-water line first (the 'less than current' line is inserted after it).
    sc.evidence = sc.evidence[:1] + practice_facts + sc.evidence[1:]
    if "awd_rice" in ids:
        sc.risks.append(fact("practice_awd_rice_care"))
    for pid in skipped_salt:
        sc.gaps.append(fact(f"practice_{pid}_skipped_salt"))
    sc.gaps.append(fact("practice_values_unverified"))
    return sc


def score_choice(ctx: Context, crop: str, season: str | None = None) -> Strategy:
    """'What if I grow X?' Put the farmer's crop into its season in both years and score it."""
    if crop not in CROPS:
        raise ValueError(f"unknown crop: {crop}")
    season = season or CROPS[crop]["season"]
    w, s = ctx.current
    rot = (crop, s, crop, s) if season == "winter" else (w, crop, w, crop)
    cur_rot = (w, s, w, s)
    base = score_rotation(cur_rot, ctx)
    sc = score_rotation(rot, ctx)
    st = _to_strategy("custom", sc, base, ctx, 0)
    if not feasible(rot):
        st.risks.insert(0, fact("tight_transition", crop_a=rot[0] if season == "summer" else w,
                                crop_b=rot[1] if season == "summer" else s))
    return st
