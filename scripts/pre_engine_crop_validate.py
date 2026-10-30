#!/usr/bin/env python3
"""Pre-engine helper: validate FieldShift_Data/cleaned/crop_reference.yaml (seed v2).

INTERIM script written during the pre-engine data sprint (before the
fieldshift engine exists). Implements DATA.md §7.4:
  * stage days must sum to growth_duration_days (when stage_days present)
  * sowing windows must be valid MM-DD dates
  * Kc values within 0-2
  * salinity threshold >= 0
  * at least one crop per slot
  * every non-null value must have src (resolvable in sources:) and status
      (§0.2 enum)
Extra checks: pH/temperature ranges sane, water min<=max, no banned wording
phrases (CLAUDE.md Part 8.4) inside notes, and a leftover-fill report per §7.5.
Exit code 1 on any error.
"""
from __future__ import annotations

import datetime
import sys

import yaml

PATH = "FieldShift_Data/cleaned/crop_reference.yaml"
STATUSES = {"verified", "extracted", "general_fact", "placeholder", "missing", "farmer"}
BANNED = ["will increase yield", "guaranteed", "best rotation",
          "optimal rotation", "optimal strategy", "you should irrigate",
          "proven"]
VALID_FIELDS = {"crop_id", "names", "category", "family", "n_fixer",
                "usual_slot", "sowing_window", "growth_duration_days",
                "stage_days", "kc", "water_requirement_mm_ref",
                "temperature_c", "drought_sensitivity",
                "salinity_threshold_ece_dsm", "soil_ph_range", "note"}

def value_fields(node: dict):
    """Yield (field, obj) for every {v, src, status}-style field of a crop."""
    for k, v in node.items():
        if k in ("crop_id", "note", "names", "category") or not isinstance(v, dict):
            continue
        if {"v", "src", "status"} <= set(v.keys()) or {"src", "status"} <= set(v.keys()):
            yield k, v

def main() -> int:
    errors, warns = [], []
    with open(PATH, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    print("=" * 64)
    print("V-CROP VALIDATION REPORT —", PATH)
    print("=" * 64)
    if doc.get("schema_version") != 2:
        errors.append("schema_version != 2")
    sources = doc.get("sources", {})

    crops = doc.get("crops", [])
    ids = [c.get("crop_id") for c in crops]
    if "fallow" not in ids:
        warnmsg = "no fallow entry"
        warns.append(warnmsg)
    by_slot: dict[str, int] = {}
    status_counts: dict[str, int] = {}

    for c in crops:
        cid = c.get("crop_id", "?")
        for fld in c:
            if fld not in VALID_FIELDS:
                errors.append(f"{cid}: unexpected field {fld}")
        # provenance of every value-bearing field
        for fld, obj in value_fields(c):
            st = obj.get("status")
            if st not in STATUSES:
                errors.append(f"{cid}.{fld}: bad status {st!r}")
            if st not in ("missing", "farmer") or obj.get("v") is not None:
                src = obj.get("src")
                if src not in sources:
                    errors.append(f"{cid}.{fld}: src {src!r} not in sources:")
            if st in ("placeholder", "missing"):
                status_counts[f"{st}:{fld}"] = status_counts.get(f"{st}:{fld}", 0) + 1
            status_counts[f"status:{st}"] = status_counts.get(f"status:{st}", 0) + 1
        # sowing window
        win = c.get("sowing_window")
        if cid != "fallow" and isinstance(win, dict) and win.get("v"):
            try:
                mm, dd = win["v"]["start"].split("-")
                datetime.date(2000, int(mm), int(dd))
                mm2, dd2 = win["v"]["end"].split("-")
                datetime.date(2000, int(mm2), int(dd2))
                slot = c.get("usual_slot")
                if slot in by_slot and win.get("status") in ("extracted", "verified"):
                    by_slot[slot] += 1
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
                if not (0 <= x <= 2):
                    errors.append(f"{cid}.kc.{k} = {x} out of 0-2")
        # salinity
        sal = (c.get("salinity_threshold_ece_dsm") or {}).get("v")
        if sal is not None and sal < 0:
            errors.append(f"{cid}.salinity negative")
        # water
        wr = (c.get("water_requirement_mm_ref") or {}).get("v")
        if isinstance(wr, dict) and wr["min"] > wr["max"]:
            errors.append(f"{cid}.water min>max")
        # temperature
        tv = (c.get("temperature_c") or {}).get("v") or {}
        if isinstance(tv, dict):
            if None not in (tv.get("topmn"), tv.get("topmx")) and tv["topmn"] > tv["topmx"]:
                errors.append(f"{cid}.temperature topmn>topmx")
            if None not in (tv.get("tmin"), tv.get("tmax")) and tv["tmin"] > tv["tmax"]:
                errors.append(f"{cid}.temperature tmin>tmax")
        # pH
        phv = (c.get("soil_ph_range") or {}).get("v") or {}
        if isinstance(phv, dict) and phv.get("ph_min") is not None:
            if not (0 <= phv["ph_min"] <= phv["ph_max"] <= 14):
                errors.append(f"{cid}.ph range")
            if phv["ph_opt_min"] < phv["ph_min"] or phv["ph_opt_max"] > phv["ph_max"]:
                errors.append(f"{cid}.ph optimal outside absolute")
        # drought enum
        dv = (c.get("drought_sensitivity") or {}).get("v")
        if dv is not None and dv not in ("low", "medium", "high"):
            errors.append(f"{cid}.drought bad class {dv!r}")
        # banned wording in any string
        for line in yaml.safe_dump(c, allow_unicode=True).splitlines():
            low = line.lower()
            for b in BANNED:
                if b in low:
                    errors.append(f"{cid}: banned phrase {b!r} in notes")
        if c.get("usual_slot") in ("winter", "summer"):
            pass

    # at least one crop per slot (count extracted/verified windows)
    slot_counts = {}
    for c in crops:
        s = c.get("usual_slot")
        if s in ("winter", "summer"):
            win = (c.get("sowing_window") or {})
            if win.get("v") and win.get("status") in ("extracted", "verified"):
                slot_counts[s] = slot_counts.get(s, 0) + 1
    for s in ("winter", "summer"):
        if slot_counts.get(s, 0) < 1:
            errors.append(f"no extracted sowing window in slot {s}")

    print(f"crops: {len(crops)}  ids: {ids}")
    print("windows per slot (extracted/verified):", slot_counts)
    print("status breakdown:")
    for k in sorted(status_counts):
        if not k.startswith("status:"):
            print(f"   {k}: {status_counts[k]}")
    remaining = [k for k in sorted(status_counts) if k.startswith(('placeholder', 'missing'))]
    print("\n§7.5 leftovers still requiring a human/citation:")
    for k in remaining:
        print(f"   {k}")
    print("\nERRORS:", errors if errors else "none")
    print("WARNS :", warns if warns else "none")
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
