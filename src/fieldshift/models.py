"""models.py — Pydantic v2 models for the Field Shift engine (Phase 1).

Names follow CLAUDE.md Part 4 (`models.py`) and the result.json contract in
Part 8.2. Every number that reaches the user carries provenance via
ValueWithProvenance / DataSource.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .data.provenance import QualityFlag, Status, ValueWithProvenance


class Location(BaseModel):
    model_config = ConfigDict(extra="forbid")
    latitude: float
    longitude: float
    name: str | None = None
    coordinates_illustrative: bool = True
    crs: str = "EPSG:4326"
    selection_date: str | None = None


class SoilField(ValueWithProvenance):
    """One field inside a soil record, with the same provenance shape."""


class Soil(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int = 1
    location_id: str
    source_type: str = "hwsd2"
    source_name: str = "FAO/IIASA HWSD v2.0"
    source_url: str = (
        "https://www.fao.org/soils-portal/data-hub/soil-maps-and-databases/"
        "harmonized-world-soil-database-v20/en/"
    )
    dataset_version: str = "2.0"
    retrieval_date: str | None = None
    spatial_representation: str = "gridded"
    spatial_resolution: str = "1 km"
    selection_note: str | None = None
    fields: dict[str, ValueWithProvenance] = Field(default_factory=dict)
    limitations: str | None = None
    farmer_test: dict[str, ValueWithProvenance] | None = None  # farmer over HWSD (DATA.md §6.5)


class Priority(StrEnum):
    REDUCE_WATER_USE = "reduce_water_use"
    SUPPORT_SOIL_HEALTH = "support_soil_health"
    IMPROVE_CLIMATE_RESILIENCE = "improve_climate_resilience"
    MAINTAIN_PRODUCTIVITY = "maintain_productivity"
    BUDGET_MARKET = "budget_market"


class Priorities(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ranked: list[Priority] = Field(default_factory=list)  # ranked best->worst
    skipped: list[Priority] = Field(default_factory=list)


class IrrigationAccess(StrEnum):
    RAINFED = "rainfed"
    LIMITED = "limited"
    FULL = "full"
    UNKNOWN = "unknown"


class FarmProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int = 1
    location: Location
    soil: Soil | None = None
    previous_crop: str | None = None  # crop_id or "fallow" or free text
    previous_crop_status: Status = Status.MISSING
    sowing_date_actual: str | None = None
    irrigation_access: IrrigationAccess = IrrigationAccess.UNKNOWN
    priorities: Priorities = Field(default_factory=Priorities)
    years_horizon: int = 1
    history_unknown: bool = False
    flags: list[QualityFlag] = Field(default_factory=list)


class StrategyKind(StrEnum):
    EXISTING = "existing"
    TEMPLATE = "template"
    CUSTOM = "custom"
    PROPOSED = "proposed"


class SequenceStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slot: str  # winter | summer
    year: int = 1
    crop_id: str


class Indicator(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    label: str
    median: float | None = None
    min: float | None = None
    max: float | None = None
    unit: str
    band: str = "Unknown"  # Good | Moderate | Poor | Unknown | Similar
    status: str = "estimated"  # estimated | observed | unknown
    definition_key: str | None = None
    dataset: str | None = None
    n_windows: int | None = None


class PriorityResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    band: str = "Unknown"
    indicators: list[str] = Field(default_factory=list)


class Overall(BaseModel):
    model_config = ConfigDict(extra="forbid")
    band: str = "Unknown"
    value: float | None = None  # kept in JSON for web app; not printed as decimal
    basis: str = ""
    suppressed: bool = False


class Comparison(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order: list[str] = Field(default_factory=list)
    too_close: list[list[str]] = Field(default_factory=list)
    order_equal_weights: list[str] = Field(default_factory=list)
    ranking_stable: bool = True
    priority_sensitivity: dict[str, Any] | None = None


class RunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int = 1
    engine_version: str = "0.1.0"
    run_id: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    disclaimer: str = "Supports, does not replace, farmer judgment and local expertise."
    profile: dict[str, Any] = Field(default_factory=dict)
    data_sources: list[dict[str, Any]] = Field(default_factory=list)
    quality_flags: list[QualityFlag] = Field(default_factory=list)
    climate_summary: dict[str, Any] = Field(default_factory=dict)
    optional_context: dict[str, Any] = Field(default_factory=dict)
    crops_used: list[dict[str, Any]] = Field(default_factory=list)
    strategies: list[Strategy] = Field(default_factory=list)
    comparison: Comparison = Field(default_factory=Comparison)
    limitations: list[str] = Field(default_factory=list)
    local_review: list[str] = Field(default_factory=list)


class Strategy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    kind: StrategyKind
    name: str
    sequence: list[SequenceStep] = Field(default_factory=list)
    indicators: list[Indicator] = Field(default_factory=list)
    priority_results: dict[str, PriorityResult] = Field(default_factory=dict)
    overall: Overall = Field(default_factory=Overall)
    confidence: str = "low"  # high | moderate | low
    flags: list[str] = Field(default_factory=list)
    why_suggested: list[str] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    information_gaps: list[str] = Field(default_factory=list)
    risks_for_local_review: list[str] = Field(default_factory=list)
    sowing_sensitivity: list[dict[str, Any]] = Field(default_factory=list)


# resolve forward ref
RunResult.model_rebuild()
Status = Status  # re-export convenience (already imported)
__all__ = [
    "Comparison",
    "FarmProfile",
    "Indicator",
    "IrrigationAccess",
    "Location",
    "Overall",
    "Priorities",
    "Priority",
    "PriorityResult",
    "QualityFlag",
    "RunResult",
    "SequenceStep",
    "Soil",
    "SoilField",
    "Strategy",
    "StrategyKind",
    "ValueWithProvenance",
]
