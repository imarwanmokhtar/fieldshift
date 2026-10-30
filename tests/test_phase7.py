"""Phase 7 reports, wording, and profile-run integration."""

import json
import shutil
from pathlib import Path

import yaml
from typer.testing import CliRunner

from fieldshift.cli import app

runner = CliRunner()
BANNED = (
    "will increase yield",
    "guaranteed",
    "best rotation",
    "optimal rotation",
    "optimal strategy",
    "you should irrigate",
    "proven",
)


def _data(tmp_path):
    target = tmp_path / "FieldShift_Data"
    shutil.copytree(Path("FieldShift_Data"), target)
    return target


def test_profile_run_writes_result_and_markdown(tmp_path):
    data_dir = _data(tmp_path)
    profile = tmp_path / "profile.json"
    profile.write_text(
        json.dumps(
            {
                "answers": {
                    "loc_mode": "pilot",
                    "coords_real": False,
                    "prev_crop": "wheat",
                    "prev_season": "winter",
                    "existing_edit": True,
                    "existing_other_crop": "maize",
                    "irrigation": "canal",
                    "water_avail": "moderate",
                    "horizon": 1,
                    "period": "2020-2025",
                    "strat_source": "templates",
                    "templates": ["faba_maize", "wheat_sorghum"],
                    "prio_rank_list": ["reduce_water_use", "support_soil_health"],
                },
                "flags": [],
                "chosen_priorities": ["reduce_water_use", "support_soil_health"],
            }
        ),
        encoding="utf-8",
    )
    result = runner.invoke(
        app, ["--data-dir", str(data_dir), "run", "--profile", str(profile), "--offline"]
    )
    assert result.exit_code == 0, result.output
    output = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    report = (tmp_path / "report.md").read_text(encoding="utf-8").lower()
    assert output["schema_version"] == 1
    assert len(output["strategies"]) == 3
    assert all(len(s["why_suggested"]) and "evidence" in s for s in output["strategies"])
    assert "check these locally with an agronomist or extension officer." in report
    assert not any(phrase in report for phrase in BANNED)
    assert (tmp_path / "run.log").is_file()


def test_i18n_has_no_banned_wording():
    strings = yaml.safe_load(Path("src/fieldshift/i18n/en.yaml").read_text(encoding="utf-8"))[
        "strings"
    ]
    values = " ".join(str(value).lower() for value in strings.values())
    assert not any(phrase in values for phrase in BANNED)


def test_run_offline_reports_missing_climate(tmp_path):
    data_dir = tmp_path / "FieldShift_Data"
    (data_dir / "cleaned").mkdir(parents=True)
    shutil.copy(
        Path("FieldShift_Data/cleaned/crop_reference.yaml"),
        data_dir / "cleaned/crop_reference.yaml",
    )
    profile = tmp_path / "profile.json"
    profile.write_text(json.dumps({"answers": {"loc_mode": "pilot"}}), encoding="utf-8")
    result = runner.invoke(
        app, ["--data-dir", str(data_dir), "run", "--profile", str(profile), "--offline"]
    )
    assert result.exit_code == 1
    assert "unavailable offline" in result.output
