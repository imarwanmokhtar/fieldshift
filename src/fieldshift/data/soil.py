"""data/soil.py — soil record loader + farmer-test merge (Phase 5)."""
from __future__ import annotations

import json
from pathlib import Path


def load_soil(path: Path | str) -> dict:
    path = Path(path)
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def soil_path(data_dir: Path | str, locid: str) -> Path:
    return Path(data_dir) / "cleaned" / f"soil_{locid}.json"


def merge_farmer_test(record: dict, farmer_test: dict | None) -> dict:
    """Apply precedence: farmer test overrides HWSD for the fields it contains
    (DATA.md §6.5). Returns a new record (does not mutate input)."""
    out = json.loads(json.dumps(record)) if record else {}
    out.setdefault("fields", {})
    if not farmer_test:
        return out
    ft = farmer_test.get("fields", farmer_test)
    for name, val in (ft or {}).items():
        # farmer value shape: {"v":..., "unit":..., "status":"farmer"} or raw scalar
        if isinstance(val, dict):
            obj = dict(val)
            obj["status"] = "farmer"
            obj.setdefault("src", "FARMER_SOIL_TEST")
            out["fields"][name] = obj
        else:
            out["fields"][name] = {"v": val, "unit": None, "src": "FARMER_SOIL_TEST",
                                   "status": "farmer"}
    # mark farmer test on record
    out["farmer_test"] = farmer_test
    return out


def soil_status(record: dict) -> str:
    """Return 'unknown' if no field has a non-missing value, else 'partial'/'known'."""
    fields = (record or {}).get("fields", {}) or {}
    has_value = any(isinstance(v, dict) and v.get("v") is not None for v in fields.values())
    if not has_value:
        return "unknown"
    # if any farmer-tested field present -> farmer
    if any(isinstance(v, dict) and v.get("status") == "farmer" for v in fields.values()):
        return "farmer"
    return "regional"


def soil_flags(record: dict) -> list[str]:
    flags: list[str] = []
    if soil_status(record) == "unknown":
        flags.append("soil_unknown")
    fields = (record or {}).get("fields", {}) or {}
    ec = fields.get("soil_ec_dsm")
    ec_val = ec.get("v") if isinstance(ec, dict) else None
    if ec_val is None:
        flags.append("salinity_unassessed")
    return flags


def field_value(record: dict, name: str):
    fields = (record or {}).get("fields", {}) or {}
    obj = fields.get(name)
    if isinstance(obj, dict):
        return obj.get("v")
    return obj
