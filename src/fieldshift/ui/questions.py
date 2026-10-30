# ruff: noqa: E501
"""ui/questions.py — question catalog (Phase 3). ids are stable API (CLAUDE.md Part 6.5)."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Question:
    id: str
    header: str
    prompt: str
    kind: str  # select | multi | text | number | confirm
    choices: Any = None  # list of (label, value) OR a key resolved by the wizard
    help_text: str | None = None
    skippable: bool = False
    min_val: float | None = None
    max_val: float | None = None
    min_select: int = 0
    default: bool = False
    maps_to: str | None = None
    unknown_flag: str | None = None
    condition: Callable[[dict], bool] = field(default=lambda a: True)


def _crop_choices(crop_ids):
    out = [(cid, cid) for cid in crop_ids if cid != "fallow"]
    out += [("Fallow / bare", "fallow"), ("Other (type it)", "__other__"),
            ("I don't know", "__unknown__")]
    return out


CATALOG: list[Question] = [
    Question("start", "START", "What would you like to do?", "select",
             choices=[("New analysis", "new"), ("Resume saved draft", "resume"),
                      ("Load a saved profile", "load"), ("Run the demo (pilot point)", "demo"),
                      ("Data tools (fetch / validate / view crops)", "tools"),
                      ("Quit", "quit")]),
    Question("loc_mode", "LOCATION", "How do you want to set the field location?", "select",
             choices=[("Use the pilot point near Mansoura, Dakahlia (31.04N, 31.38E — illustrative)", "pilot"),
                      ("Type latitude and longitude", "manual"),
                      ("Load a field boundary file (coming later)", "boundary")]),
    Question("lat", "LOCATION", "Latitude of the field (decimal degrees, e.g. 31.04)", "number",
             help_text="Outside the Egypt box (DATA.md §2) we will ask you to confirm.",
             min_val=-90, max_val=90, condition=lambda a: a.get("loc_mode") == "manual"),
    Question("lon", "LOCATION", "Longitude of the field (decimal degrees, e.g. 31.38)", "number",
             min_val=-180, max_val=180, condition=lambda a: a.get("loc_mode") == "manual"),
    Question("loc_name", "LOCATION", "Give this location a short name (optional)", "text",
             skippable=True),
    Question("coords_real", "LOCATION", "Are these the real coordinates of your field?", "confirm",
             help_text="No → the run is tagged coordinates_illustrative.",
             default=False, condition=lambda a: a.get("loc_mode") == "pilot"),
    Question("prev_crop", "FARM", "What crop did you grow last season?", "select",
             choices="crops", help_text="Other → flag crop_not_in_reference (indicators unknown for it).",
             unknown_flag="history_unknown"),
    Question("prev_season", "FARM", "In which season was that?", "select",
             choices=[("Winter (Nov-Apr)", "winter"), ("Summer (May-Oct)", "summer"),
                      ("I'm not sure", "unknown")],
             unknown_flag="season_unknown",
             condition=lambda a: a.get("prev_crop") not in (None, "__unknown__")),
    Question("has_earlier", "FARM", "Do you know the crops before that?", "confirm", default=False),
    Question("prev2_a", "FARM", "What did you grow 2 seasons ago?", "select", choices="crops", skippable=False,
             condition=lambda a: a.get("has_earlier") is True),
    Question("prev2_b", "FARM", "What did you grow 3 seasons ago?", "select", choices="crops", skippable=False,
             condition=lambda a: a.get("has_earlier") is True),
    Question("irrigation", "WATER", "What is your main irrigation source?", "select",
             choices=[("Nile canal / surface water", "canal"), ("Groundwater well", "well"),
                      ("Canal + well", "both"), ("Rain only (no irrigation)", "rain"),
                      ("Other", "other"), ("I don't know", "unknown")],
             unknown_flag="irrigation_unknown"),
    Question("water_avail", "WATER", "How much irrigation water can you count on?", "select",
             choices=[("Limited", "limited"), ("Moderate", "moderate"), ("High", "high"),
                      ("I'm not sure", "unknown")],
             help_text="Rainfall is not the same as irrigation availability."),
    Question("soil_test", "SOIL", "Do you have a recent soil test for this field?", "confirm", default=False),
    Question("soil_texture", "SOIL", "Soil texture class", "select",
             choices=[("Sand", "sand"), ("Loamy sand", "loamy_sand"), ("Sandy loam", "sandy_loam"),
                      ("Loam", "loam"), ("Silt loam", "silt_loam"), ("Silt", "silt"),
                      ("Sandy clay loam", "sandy_clay_loam"), ("Clay loam", "clay_loam"),
                      ("Silty clay loam", "silty_clay_loam"), ("Sandy clay", "sandy_clay"),
                      ("Silty clay", "silty_clay"), ("Clay", "clay"),
                      ("I don't know", "unknown")],
             unknown_flag="soil_partial", condition=lambda a: a.get("soil_test") is True),
    Question("soil_ph", "SOIL", "Soil pH", "number", skippable=True, min_val=3, max_val=10,
             unknown_flag="soil_partial", condition=lambda a: a.get("soil_test") is True),
    Question("soil_oc", "SOIL", "Organic carbon", "number", skippable=True, min_val=0,
             unknown_flag="soil_partial", condition=lambda a: a.get("soil_test") is True),
    Question("soil_ec", "SOIL", "Salinity: electrical conductivity (ECe) in dS/m", "number",
             skippable=True, min_val=0, help_text="Field/lab EC; HWSD is no substitute.",
             unknown_flag="salinity_unassessed", condition=lambda a: a.get("soil_test") is True),
    Question("soil_depth", "SOIL", "Rooting/sampling depth (cm)", "number", skippable=True,
             min_val=0, max_val=300, condition=lambda a: a.get("soil_test") is True),
    Question("soil_date", "SOIL", "Date of the test (YYYY-MM-DD)", "text", skippable=True,
             condition=lambda a: a.get("soil_test") is True),
    Question("area", "FARM", "Field area in hectares (optional)", "number", skippable=True, min_val=0),
    Question("prio_rank", "PRIORITIES", "Which matters most to you? (then next, then next...)", "select",
             choices="priorities"),
    Question("budget_market", "PRIORITIES", "Do budget or market limits matter?", "select",
             choices=[("No constraint", "none"), ("Low-cost inputs matter", "low_cost"),
                      ("Market / cash value matters", "market"), ("Food or fodder for my own use", "own_use")],
             unknown_flag="priority_unscored"),
    Question("data_mode", "DATA", "Where should climate data come from?", "select",
             choices=[("Saved local files (offline)", "offline"),
                      ("Download fresh NASA POWER data now (internet needed)", "fetch"),
                      ("Auto (local if present, else download)", "auto")]),
    Question("period", "DATA", "Which years of climate history?", "select",
             choices=[("2020-2025 (default from the research plan)", "2020-2025"),
                      ("2011-2025 (15 years - better for variability)", "2011-2025"),
                      ("Custom range", "custom")]),
    Question("horizon", "DATA", "How many years should each rotation cover?", "select",
             choices=[("1", 1), ("2", 2), ("3", 3)]),
    Question("strat_source", "STRATEGIES", "How do you want to choose alternatives to compare?", "select",
             choices=[("Ready-made templates (recommended)", "templates"),
                      ("Build my own", "custom"),
                      ("Let the engine propose candidates (experimental)", "proposed")]),
    Question("existing_edit", "STRATEGIES", "This is your existing rotation. Is it right?", "confirm", default=True),
    Question("existing_other_crop", "STRATEGIES", "What do you grow in the other season?", "select",
             choices="crops", unknown_flag="history_unknown",
             condition=lambda a: a.get("existing_edit") is True),
    Question("existing_winter_crop", "STRATEGIES", "What is your existing winter crop?", "select",
             choices="crops", unknown_flag="history_unknown",
             condition=lambda a: a.get("existing_edit") is False),
    Question("existing_summer_crop", "STRATEGIES", "What is your existing summer crop?", "select",
             choices="crops", unknown_flag="history_unknown",
             condition=lambda a: a.get("existing_edit") is False),
    Question("templates", "STRATEGIES", "Pick at least 2 alternatives to compare with your rotation", "multi",
             choices="templates", min_select=2,
             condition=lambda a: a.get("strat_source") == "templates"),
    Question("custom_winter_1", "STRATEGIES", "Custom strategy 1 — winter crop", "select",
             choices="crops", condition=lambda a: a.get("strat_source") == "custom"),
    Question("custom_summer_1", "STRATEGIES", "Custom strategy 1 — summer crop", "select",
             choices="crops", condition=lambda a: a.get("strat_source") == "custom"),
    Question("custom_name_1", "STRATEGIES", "Name custom strategy 1", "text",
             condition=lambda a: a.get("strat_source") == "custom"),
    Question("custom_winter_2", "STRATEGIES", "Custom strategy 2 — winter crop", "select",
             choices="crops", condition=lambda a: a.get("strat_source") == "custom"),
    Question("custom_summer_2", "STRATEGIES", "Custom strategy 2 — summer crop", "select",
             choices="crops", condition=lambda a: a.get("strat_source") == "custom"),
    Question("custom_name_2", "STRATEGIES", "Name custom strategy 2", "text",
             condition=lambda a: a.get("strat_source") == "custom"),
    Question("review", "REVIEW", "Everything look right?", "select",
             choices=[("Run the analysis", "run"), ("Edit a section", "edit"),
                      ("Save profile and exit", "save")]),
]


def question_by_id(qid: str) -> Question | None:
    for q in CATALOG:
        if q.id == qid:
            return q
    return None


def resolve_choices(q: Question, ctx: dict) -> list:
    key = q.choices
    if isinstance(key, str):
        if key == "crops":
            return _crop_choices(ctx.get("crop_ids", []))
        if key == "templates":
            return [(t, t) for t in ctx.get("template_ids", [])]
        if key == "priorities":
            remaining = [p for p in ["reduce_water_use", "support_soil_health",
                                     "improve_climate_resilience", "maintain_productivity"]
                         if p not in ctx.get("chosen_priorities", [])]
            # include "stop here" terminator
            out = [(p.replace("_", " ").title(), p) for p in remaining]
            out.append(("Stop here — treat the rest as equal", "__stop__"))
            return out
        if key == "seasons":
            return [("Winter (Nov-Apr)", "winter"), ("Summer (May-Oct)", "summer")]
    return key or []


def next_question_id(answers: dict, asked: set[str]) -> str | None:
    for q in CATALOG:
        if q.id in asked:
            continue
        if not q.condition(answers):
            continue
        return q.id
    return None
