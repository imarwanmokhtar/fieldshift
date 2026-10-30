"""config.py — load config/app.yaml, thresholds.yaml, bands.yaml (Phase 1)."""
from __future__ import annotations

from pathlib import Path

import yaml


def find_config_dir(start: Path | None = None) -> Path:
    """Locate the config/ directory (repo root by default)."""
    if start is None:
        start = Path.cwd()
    for cand in (start, *start.parents):
        if (cand / "config" / "app.yaml").is_file():
            return cand / "config"
    # fallback: alongside the package install (dev mode)
    return Path("config")


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_app_config(config_dir: Path | None = None) -> dict:
    cd = config_dir or find_config_dir()
    return load_yaml(cd / "app.yaml")


def load_thresholds(config_dir: Path | None = None) -> dict:
    cd = config_dir or find_config_dir()
    return load_yaml(cd / "thresholds.yaml")


def load_bands(config_dir: Path | None = None) -> dict:
    cd = config_dir or find_config_dir()
    return load_yaml(cd / "bands.yaml")
