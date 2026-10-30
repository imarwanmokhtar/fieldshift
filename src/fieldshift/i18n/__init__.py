"""Small loader for user-facing English strings."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml


@lru_cache(maxsize=1)
def load_strings() -> dict[str, str]:
    path = Path(__file__).with_name("en.yaml")
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return doc.get("strings", {})


def text(key: str, **values: object) -> str:
    template = load_strings().get(key, key)
    return template.format(**values)
