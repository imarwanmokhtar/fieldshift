"""data/provenance.py — DataSource, StatusBadge, QualityFlag, retrieval-log writer.

Phase 1 deliverable. Centralises provenance types so models, UI and analysis
all reference one definition (CLAUDE.md Part 0 rule 4).
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel


class Status(StrEnum):
    """Value-status enum from DATA.md §0.2."""
    VERIFIED = "verified"
    EXTRACTED = "extracted"
    GENERAL_FACT = "general_fact"
    PLACEHOLDER = "placeholder"
    MISSING = "missing"
    FARMER = "farmer"


STATUS_BADGES = {
    Status.VERIFIED: "✔ verified",
    Status.EXTRACTED: "● extracted",
    Status.GENERAL_FACT: "○ general",
    Status.PLACEHOLDER: "▲ placeholder",
    Status.MISSING: "✖ missing",
    Status.FARMER: "◆ farmer",
}


class Severity(StrEnum):
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class QualityFlag(BaseModel):
    code: str
    text_key: str
    severity: Severity = Severity.WARN


class DataSource(BaseModel):
    id: str
    name: str
    url: str
    version: str | None = None
    retrieved: str | None = None
    period: str | None = None
    resolution: str | None = None
    spatial_type: str | None = None
    units: dict[str, str] | None = None
    missing_value_rule: str | None = None
    status: Status = Status.MISSING


class ValueWithProvenance(BaseModel):
    """One value inside a crop table or soil record."""
    v: object = None
    unit: str | None = None
    src: str | None = None
    status: Status = Status.MISSING
    note: str | None = None


def append_retrieval_log(log_path: Path, *, source_id: str, action: str, url: str,
                         http_status: int | None = None, bytes_: int | None = None,
                         file: str | None = None, sha256: str | None = None,
                         note: str | None = None) -> None:
    """Append one JSON line to metadata/retrieval_log.jsonl."""
    entry = {
        "ts": datetime.now(UTC).astimezone().isoformat(timespec="seconds"),
        "source_id": source_id,
        "action": action,
        "url": url,
    }
    if http_status is not None:
        entry["http_status"] = http_status
    if bytes_ is not None:
        entry["bytes"] = bytes_
    if file is not None:
        entry["file"] = file
    if sha256 is not None:
        entry["sha256"] = sha256
    if note is not None:
        entry["note"] = note
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
