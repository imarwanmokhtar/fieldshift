"""Phase 3 tests — wizard runs scripted, saves profile, non-TTY exits 2."""

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from fieldshift.cli import app

runner = CliRunner()


def test_demo_runs_and_saves_profile(tmp_path):
    data_dir = tmp_path / "FieldShift_Data"
    shutil.copytree(Path("FieldShift_Data"), data_dir)
    result = runner.invoke(app, ["--data-dir", str(data_dir), "demo"])
    assert result.exit_code == 0, result.output
    profiles = list((tmp_path / "runs").glob("*/profile.json"))
    assert profiles, "demo should save a profile.json"
    data = json.loads(profiles[0].read_text(encoding="utf-8"))
    assert "answers" in data
    assert data["chosen_priorities"]
    assert (profiles[0].parent / "result.json").is_file()
    assert (profiles[0].parent / "report.md").is_file()


def test_scripted_run_via_answers_file(tmp_path):
    # build a minimal answers file
    import json as _j

    answers = {
        "start": "new",
        "loc_mode": "pilot",
        "coords_real": False,
        "loc_name": None,
        "prev_crop": "wheat",
        "prev_season": "winter",
        "has_earlier": False,
        "irrigation": "canal",
        "water_avail": "moderate",
        "soil_test": False,
        "area": None,
        "prio_rank": [
            "reduce_water_use",
            "support_soil_health",
            "improve_climate_resilience",
            "maintain_productivity",
            "__stop__",
        ],
        "budget_market": "none",
        "data_mode": "offline",
        "period": "2020-2025",
        "horizon": 1,
        "strat_source": "templates",
        "existing_edit": True,
        "existing_other_crop": "maize",
        "templates": ["faba_maize", "wheat_sorghum"],
        "review": "save",
    }
    ans_file = tmp_path / "answers.json"
    ans_file.write_text(_j.dumps(answers), encoding="utf-8")
    # need a data dir with crop table; use init-data first
    runner.invoke(app, ["--data-dir", str(tmp_path), "init-data"])
    result = runner.invoke(app, ["--data-dir", str(tmp_path), "--answers", str(ans_file)])
    assert result.exit_code == 0, result.output
    profiles = list((tmp_path.parent / "runs").glob("*/profile.json"))
    assert profiles


def test_non_tty_exits_2():
    # CliRunner is not a TTY, invoking default command should exit 2
    result = runner.invoke(app, [])
    assert result.exit_code == 2
