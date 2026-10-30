"""data/crops.py — crop_reference.yaml loader + V-CROP validator (Phase 2).

Implements DATA.md §7.4 and the provenance/wording checks from
scripts/pre_engine_crop_validate.py, but as a reusable library (no terminal I/O).
"""
from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

import yaml

STATUSES = {"verified", "extracted", "general_fact", "placeholder", "missing", "farmer"}
BANNED = ["will increase yield", "guaranteed", "best rotation", "optimal rotation",
          "optimal strategy", "you should irrigate", "proven"]
VALUE_FIELDS = {"sowing_window", "growth_duration_days", "stage_days", "kc",
                "water_requirement_mm_ref", "temperature_c", "drought_sensitivity",
                "salinity_threshold_ece_dsm", "soil_ph_range", "family", "n_fixer"}


class CropTable:
    """In-memory view of a loaded crop_reference.yaml."""

    def __init__(self, doc: dict, path: Path):
        self.doc = doc
        self.path = path
        self.schema_version = doc.get("schema_version")
        self.sources = doc.get("sources", {}) or {}
        self.slots = doc.get("slots", {}) or {}
        self.defaults = doc.get("defaults", {}) or {}
        self.drought_class_mapping = doc.get("drought_class_mapping", {}) or {}
        self.crops = doc.get("crops", []) or []

    @property
    def crop_ids(self) -> list[str]:
        return [c.get("crop_id") for c in self.crops]

    def by_id(self, cid: str) -> dict | None:
        for c in self.crops:
            if c.get("crop_id") == cid:
                return c
        return None


def load_crop_table(path: Path | str) -> CropTable:
    path = Path(path)
    with path.open(encoding="utf-8") as fh:
        doc = yaml.safe_load(fh) or {}
    return CropTable(doc, path)


def _is_value_field(obj: Any) -> bool:
    return isinstance(obj, dict) and ({"v", "src", "status"} <= set(obj.keys())
                                     or {"src", "status"} <= set(obj.keys()))


def validate(doc: dict) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Empty errors == valid."""
    errors: list[str] = []
    warns: list[str] = []
    if doc.get("schema_version") != 2:
        errors.append("schema_version != 2")
    sources = doc.get("sources", {}) or {}
    crops = doc.get("crops", []) or []

    status_counts_placeholder = 0
    slot_counts: dict[str, int] = {}

    for c in crops:
        cid = c.get("crop_id", "?")
        # provenance on every value-bearing field
        for fld, obj in c.items():
            if (
                fld in ("crop_id", "note", "names", "category", "usual_slot")
                or not _is_value_field(obj)
            ):
                continue
            st = obj.get("status")
            if st not in STATUSES:
                errors.append(f"{cid}.{fld}: bad status {st!r}")
            src = obj.get("src")
            if src is not None and src not in sources:
                errors.append(f"{cid}.{fld}: src {src!r} not in sources")
            if obj.get("v") is not None and src is None:
                errors.append(f"{cid}.{fld}: non-null value without src")
            if st in ("placeholder", "missing"):
                status_counts_placeholder += 1

        # sowing window validity
        win = c.get("sowing_window")
        if cid != "fallow" and isinstance(win, dict) and win.get("v"):
            try:
                mm, dd = win["v"]["start"].split("-")
                datetime.date(2000, int(mm), int(dd))
                mm2, dd2 = win["v"]["end"].split("-")
                datetime.date(2000, int(mm2), int(dd2))
                slot = c.get("usual_slot")
                if slot in ("winter", "summer") and win.get("status") in ("extracted", "verified"):
                    slot_counts[slot] = slot_counts.get(slot, 0) + 1
            except (ValueError, TypeError, AttributeError) as e:
                errors.append(f"{cid}.sowing_window: {e}")

        # duration vs stages
        dur = c.get("growth_duration_days") or {}
        stages = c.get("stage_days") or {}
        if isinstance(dur.get("v"), (int, float)) and isinstance(stages.get("v"), dict):
            tot = sum(stages["v"].values())
            if tot != dur["v"]:
                errors.append(f"{cid}: stage sum {tot} != growth_duration_days {dur['v']}")
        elif cid != "fallow" and stages.get("v") is None:
            if stages.get("status") not in ("missing", "placeholder"):
                errors.append(f"{cid}.stage_days null but status not missing")

        # Kc
        kcv = (c.get("kc") or {}).get("v")
        if isinstance(kcv, dict):
            for k, x in kcv.items():
                if not isinstance(x, (int, float)) or not (0 <= x <= 2):
                    errors.append(f"{cid}.kc.{k} = {x} out of 0-2")

        # salinity
        sal = (c.get("salinity_threshold_ece_dsm") or {}).get("v")
        if sal is not None and (not isinstance(sal, (int, float)) or sal < 0):
            errors.append(f"{cid}.salinity negative or non-numeric")

        # water
        wr = (c.get("water_requirement_mm_ref") or {}).get("v")
        if isinstance(wr, dict) and wr.get("min", 0) > wr.get("max", 0):
            errors.append(f"{cid}.water min>max")

        # temperature
        tv = (c.get("temperature_c") or {}).get("v") or {}
        if isinstance(tv, dict):
            if (
                tv.get("topmn") is not None
                and tv.get("topmx") is not None
                and tv["topmn"] > tv["topmx"]
            ):
                errors.append(f"{cid}.temperature topmn>topmx")
            if (
                tv.get("tmin") is not None
                and tv.get("tmax") is not None
                and tv["tmin"] > tv["tmax"]
            ):
                errors.append(f"{cid}.temperature tmin>tmax")

        # pH
        phv = (c.get("soil_ph_range") or {}).get("v") or {}
        if isinstance(phv, dict) and phv.get("ph_min") is not None:
            if not (0 <= phv["ph_min"] <= phv["ph_max"] <= 14):
                errors.append(f"{cid}.ph range")
            if (
                phv.get("ph_opt_min", phv["ph_min"]) < phv["ph_min"]
                or phv.get("ph_opt_max", phv["ph_max"]) > phv["ph_max"]
            ):
                errors.append(f"{cid}.ph optimal outside absolute")

        # drought enum
        dv = (c.get("drought_sensitivity") or {}).get("v")
        if dv is not None and dv not in ("low", "medium", "high"):
            errors.append(f"{cid}.drought bad class {dv!r}")

        # banned wording in any string of the crop entry
        dumped = yaml.safe_dump(c, allow_unicode=True).lower()
        for b in BANNED:
            if b in dumped:
                errors.append(f"{cid}: banned phrase {b!r}")

    for s in ("winter", "summer"):
        if slot_counts.get(s, 0) < 1:
            errors.append(f"no extracted sowing window in slot {s}")

    return errors, warns


def status_counts(doc_or_table) -> dict[str, int]:
    doc = doc_or_table.doc if isinstance(doc_or_table, CropTable) else doc_or_table
    counts: dict[str, int] = {}
    for c in doc.get("crops", []):
        for fld, obj in c.items():
            if isinstance(obj, dict) and _is_value_field(obj):
                st = obj.get("status")
                if st:
                    counts[f"status:{st}"] = counts.get(f"status:{st}", 0) + 1
                if obj.get("v") is None and st in ("placeholder", "missing"):
                    counts[f"{st}:{fld}"] = counts.get(f"{st}:{fld}", 0) + 1
    return counts


def leftovers(doc_or_table) -> list[str]:
    """§7.5 fill-in checklist: placeholder/missing values needing a human/citation."""
    doc = doc_or_table.doc if isinstance(doc_or_table, CropTable) else doc_or_table
    out: list[str] = []
    for c in doc.get("crops", []):
        cid = c.get("crop_id")
        for fld, obj in c.items():
            if isinstance(obj, dict) and _is_value_field(obj):
                st = obj.get("status")
                if st in ("placeholder", "missing") and obj.get("v") is None:
                    out.append(f"{cid}.{fld} ({st})")
                elif st == "placeholder":
                    out.append(f"{cid}.{fld} (placeholder)")
    # de-dupe preserving order
    seen = set()
    uniq = []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


def fields_for_crop(crop: dict) -> list[tuple[str, str]]:
    """Return (field, badge-word) pairs for the crops×fields table."""
    out = []
    for fld, obj in crop.items():
        if fld in ("crop_id", "note", "names", "category", "usual_slot"):
            continue
        if not _is_value_field(obj):
            continue
        st = obj.get("status", "missing")
        badge_word = {
            "verified": "verified", "extracted": "extracted", "general_fact": "general",
            "placeholder": "placeholder", "missing": "missing", "farmer": "farmer",
        }.get(st, st)
        out.append((fld, badge_word))
    return out
