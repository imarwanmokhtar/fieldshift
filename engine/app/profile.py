"""Turn the raw `field_profiles.answers` JSON into a typed FarmProfile.

Every value is parsed defensively: anything missing, malformed or "unknown"
becomes None (or an empty list) and the question id is added to
`unknown_answers`, which lowers confidence later.
"""

from __future__ import annotations

from typing import Any

from .schemas import FEDDAN_HA, CropSeason, FarmProfile, SoilTest

UNIT_TO_HA = {"feddan": FEDDAN_HA, "kirat": FEDDAN_HA / 24, "hectare": 1.0}

# Questions the engine actually uses (used to count unknowns).
TRACKED = [
    "soil_texture", "drainage", "salinity", "soil_issues", "organic_inputs", "soil_test",
    "water_source", "water_reliability", "irrigation_method", "irrigation_interval",
    "water_quality", "water_cost", "last_crop", "prev_crop", "bare_periods",
    "pest_issues", "fertilizer_level", "risk_tolerance", "equipment", "horizon",
]


class ProfileError(ValueError):
    pass


def _is_unknown(v: Any) -> bool:
    return v is None or v == "unknown" or v == "" or v == [] or v == {}


def _str(v: Any) -> str | None:
    return None if _is_unknown(v) or not isinstance(v, str) else v


def _list(v: Any) -> list[str]:
    if _is_unknown(v):
        return []
    if isinstance(v, str):
        return [v]
    if isinstance(v, list):
        return [x for x in v if isinstance(x, str) and x != "unknown"]
    return []


def _num(v: Any) -> float | None:
    try:
        f = float(v)
        return f if f == f else None
    except (TypeError, ValueError):
        return None


def _crop(v: Any) -> CropSeason | None:
    if isinstance(v, dict) and isinstance(v.get("crop"), str) and v["crop"] not in ("", "unknown"):
        season = v.get("season") if v.get("season") in ("winter", "summer") else None
        typed = v.get("other")
        name = typed.strip()[:40] if v["crop"] == "other" and isinstance(typed, str) and typed.strip() else None
        return CropSeason(crop=v["crop"], season=season, name=name)
    if isinstance(v, str) and v not in ("", "unknown"):
        return CropSeason(crop=v)
    return None


def parse_profile(answers: dict[str, Any]) -> FarmProfile:
    pin = answers.get("pin")
    if not isinstance(pin, dict) or _num(pin.get("lat")) is None or _num(pin.get("lng")) is None:
        raise ProfileError("The field location (pin) is missing.")
    lat, lng = float(pin["lat"]), float(pin["lng"])
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise ProfileError("The field location is not a valid coordinate.")

    area = answers.get("area")
    area_ha = area_value = area_unit = None
    if isinstance(area, dict):
        area_value, area_unit = _num(area.get("value")), area.get("unit")
        area_ha = _num(area.get("hectares"))
        if area_ha is None and area_value is not None and area_unit in UNIT_TO_HA:
            area_ha = area_value * UNIT_TO_HA[area_unit]
    elif _num(area) is not None:
        area_value, area_unit = _num(area), "feddan"
        area_ha = area_value * FEDDAN_HA
    if not area_ha or area_ha <= 0:
        raise ProfileError("The field size is missing.")

    st_raw = answers.get("soil_test")
    soil_test = None
    if isinstance(st_raw, dict):
        has = bool(st_raw.get("hasTest", st_raw.get("has_test", False)))
        soil_test = SoilTest(
            has_test=has, ph=_num(st_raw.get("ph")), ec=_num(st_raw.get("ec")),
            organic_matter=_num(st_raw.get("organicMatter", st_raw.get("organic_matter"))),
            n=_num(st_raw.get("n")), p=_num(st_raw.get("p")), k=_num(st_raw.get("k")),
        )
    elif st_raw in ("no", "yes"):
        soil_test = SoilTest(has_test=st_raw == "yes")

    interval = answers.get("irrigation_interval")
    i_summer = _num(interval.get("summer")) if isinstance(interval, dict) else None
    i_winter = _num(interval.get("winter")) if isinstance(interval, dict) else None

    def none_aware(items: list[str]) -> list[str]:
        return [] if items == ["none"] else [x for x in items if x != "none"]

    profile = FarmProfile(
        lat=round(lat, 5), lng=round(lng, 5), area_ha=round(area_ha, 4),
        area_value=area_value, area_unit=area_unit if isinstance(area_unit, str) else None,
        field_name=_str(answers.get("field_name")),
        soil_texture=_str(answers.get("soil_texture")),
        drainage=_str(answers.get("drainage")),
        salinity=_str(answers.get("salinity")),
        soil_issues=none_aware(_list(answers.get("soil_issues"))),
        organic_inputs=_str(answers.get("organic_inputs")),
        soil_test=soil_test,
        water_source=_list(answers.get("water_source")),
        water_reliability=_str(answers.get("water_reliability")),
        irrigation_method=_str(answers.get("irrigation_method")),
        irrigation_interval_summer=i_summer,
        irrigation_interval_winter=i_winter,
        water_quality=_str(answers.get("water_quality")),
        water_cost=_str(answers.get("water_cost")),
        last_crop=_crop(answers.get("last_crop")),
        prev_crop=_crop(answers.get("prev_crop")),
        bare_periods=_str(answers.get("bare_periods")),
        pest_issues=none_aware(_list(answers.get("pest_issues"))),
        fertilizer_level=_str(answers.get("fertilizer_level")),
        priorities=_list(answers.get("priorities"))[:3],
        risk_tolerance=_str(answers.get("risk_tolerance")),
        equipment=_list(answers.get("equipment")),
        horizon=_str(answers.get("horizon")),
    )
    unknown = []
    for qid in TRACKED:
        v = answers.get(qid)
        if qid == "soil_test":
            if soil_test is None:
                unknown.append(qid)
        elif qid in ("last_crop", "prev_crop"):
            if _crop(v) is None:
                unknown.append(qid)
        elif qid == "irrigation_interval":
            if i_summer is None and i_winter is None:
                unknown.append(qid)
        elif _is_unknown(v):
            unknown.append(qid)
    profile.unknown_answers = unknown
    if not profile.priorities:
        profile.priorities = ["better_soil", "save_water", "higher_income"]
        profile.unknown_answers.append("priorities")
    return profile
