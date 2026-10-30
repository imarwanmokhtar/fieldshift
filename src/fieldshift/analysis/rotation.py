"""analysis/rotation.py — strategy building + rotation rule notes (Part 7.6)."""
from __future__ import annotations

from pathlib import Path

import yaml


def load_rules(path) -> list[dict]:
    p = Path(path)
    if not p.is_file():
        return []
    d = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return d.get("rules", []) or []


def load_templates(path) -> list[dict]:
    p = Path(path)
    if not p.is_file():
        return []
    d = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return d.get("templates", []) or []


def template_by_id(templates: list[dict], tid: str) -> dict | None:
    for t in templates:
        if t.get("id") == tid:
            return t
    return None


def expand_template(tpl: dict, horizon: int) -> list[dict]:
    """Expand a one-year template over `horizon` years."""
    seq = tpl.get("sequence", [])
    out = []
    for y in range(1, horizon + 1):
        for step in seq:
            out.append({"slot": step["slot"], "year": y, "crop_id": step["crop"]})
    return out


def evaluate_rules(rules: list[dict], sequence: list[dict], crop_lookup: dict) -> dict:
    """Evaluate rotation rules; return triggered/rules notes/facts."""
    triggered = []
    notes = []
    n_fixer = 0
    family_repeat = 0
    bare_slots = 0
    # family repeat: same family in consecutive seasons (slots in sequence order)
    families = []
    for step in sequence:
        cid = step["crop_id"]
        if cid == "fallow":
            bare_slots += 1
            families.append(None)
            continue
        crop = crop_lookup.get(cid, {})
        fam = (
            (crop.get("family") or {}).get("v")
            if isinstance(crop.get("family"), dict)
            else crop.get("family")
        )
        nf = crop.get("n_fixer")
        if isinstance(nf, dict):
            nf = (nf or {}).get("v")
        n_fixer += 1 if nf else 0
        families.append(fam)
    for i in range(1, len(families)):
        if families[i] is not None and families[i] == families[i - 1]:
            family_repeat += 1
    # bare period overlap not computed here (no calendar) -> bare_slots only
    for rule in rules:
        rid = rule.get("id")
        trig = False
        if (
            (rid == "R_FAMILY_REPEAT" and family_repeat > 0)
            or (rid == "R_LEGUME_PRESENT" and n_fixer > 0)
            or (rid == "R_BARE_PERIOD" and bare_slots > 0)
        ):
            trig = True
        elif rid == "R_HIGH_WATER_SUMMER":
            trig = False  # data-driven, handled elsewhere
        if trig:
            triggered.append(rid)
            supported = rule.get("supported", False)
            if not supported:
                notes.append(rule.get("note_key", rid))
    return {
        "triggered": triggered,
        "notes": notes,
        "n_fixer_present": n_fixer,
        "family_repeat_count": family_repeat,
        "bare_slots": bare_slots,
    }
