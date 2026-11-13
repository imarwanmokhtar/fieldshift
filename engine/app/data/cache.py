"""Tiny JSON disk cache. Keys are hashed into file names under CACHE_DIR/<namespace>/."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from ..settings import settings


def _path(namespace: str, key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]
    folder = settings.CACHE_DIR / namespace
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{digest}.json"


def get(namespace: str, key: str, max_age_s: float | None = None) -> Any | None:
    p = _path(namespace, key)
    if not p.exists():
        return None
    if max_age_s is not None and time.time() - p.stat().st_mtime > max_age_s:
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def put(namespace: str, key: str, value: Any) -> None:
    p = _path(namespace, key)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)
