"""JSON result writer."""

from __future__ import annotations

import json
from pathlib import Path


def write_json(result, path: Path | str) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = result.model_dump(mode="json")
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return target
