"""Phase 2 tests — crop loader + V-CROP validator + `fieldshift crops`."""
import copy
from pathlib import Path

from typer.testing import CliRunner

from fieldshift.cli import app
from fieldshift.data.crops import (
    leftovers,
    load_crop_table,
    status_counts,
    validate,
)

runner = CliRunner()


def _real_table():
    return load_crop_table(Path("FieldShift_Data/cleaned/crop_reference.yaml"))


def test_real_crop_table_loads_and_validates():
    t = _real_table()
    assert t.schema_version == 2
    assert len(t.crops) == 9
    errs, _ = validate(t.doc)
    assert errs == [], errs


def test_status_counts_has_missing_and_placeholder():
    t = _real_table()
    sc = status_counts(t.doc)
    # berseem leaves 4 missing + 1 placeholder (duration)
    assert sc.get("status:missing", 0) >= 4
    assert sc.get("status:placeholder", 0) >= 1


def test_leftovers_lists_berseem_items():
    t = _real_table()
    L = leftovers(t.doc)
    assert any("berseem" in x for x in L)
    assert len(L) >= 5


def test_validator_catches_injected_errors(tmp_path):
    t = _real_table()
    doc = copy.deepcopy(t.doc)
    # 1) stage sum mismatch
    w = doc["crops"][0]  # wheat
    w["stage_days"]["v"] = {"ini": 20, "dev": 50, "mid": 60, "late": 30}
    w["growth_duration_days"]["v"] = 999
    # 2) bad Kc
    w["kc"]["v"]["mid"] = 2.5
    # 3) missing src on a non-null value
    w["sowing_window"]["src"] = "NOPE"
    # 4) banned phrase in a note
    w["note"] = "this will increase yield guaranteed"
    errs, _ = validate(doc)
    joined = "\n".join(errs)
    assert "stage sum" in joined
    assert "out of 0-2" in joined
    assert "not in sources" in joined
    assert "banned phrase" in joined


def test_validator_catches_bad_sowing_window():
    t = _real_table()
    doc = copy.deepcopy(t.doc)
    doc["crops"][1]["sowing_window"]["v"] = {"start": "13-40", "end": "02-30"}
    errs, _ = validate(doc)
    assert any("sowing_window" in e for e in errs)


def test_validator_catches_negative_salinity():
    t = _real_table()
    doc = copy.deepcopy(t.doc)
    doc["crops"][0]["salinity_threshold_ece_dsm"]["v"] = -1
    errs, _ = validate(doc)
    assert any("salinity" in e for e in errs)


def test_crops_command_renders():
    result = runner.invoke(app, ["crops", "--status"])
    assert result.exit_code == 0, result.output
    assert "validation: 0 errors" in result.output
    assert "fill-in checklist" in result.output
    assert "berseem" in result.output


def test_crops_command_missing_file(tmp_path):
    result = runner.invoke(app, ["--data-dir", str(tmp_path), "crops"])
    assert result.exit_code == 1
    assert "init-data" in result.output
