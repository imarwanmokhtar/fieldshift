"""Pydantic models: farmer profile, features, strategies, evidence pack, narrative."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Lang = Literal["en", "ar"]
Season = Literal["winter", "summer"]
Confidence = Literal["high", "medium", "low"]

CRITERIA = ["water", "heat", "soil", "income", "cost", "risk", "forage"]

FEDDAN_HA = 0.42  # 1 feddan = 4200 m2


# ---------------------------------------------------------------- profile

class CropSeason(BaseModel):
    crop: str
    season: Season | None = None


class SoilTest(BaseModel):
    has_test: bool = False
    ph: float | None = None
    ec: float | None = None
    organic_matter: float | None = None
    n: float | None = None
    p: float | None = None
    k: float | None = None


class FarmProfile(BaseModel):
    """Onboarding answers, parsed. None means the farmer skipped or answered "unknown"."""

    lat: float
    lng: float
    area_ha: float
    area_value: float | None = None
    area_unit: str | None = None
    field_name: str | None = None
    soil_texture: str | None = None
    drainage: str | None = None
    salinity: str | None = None
    soil_issues: list[str] = Field(default_factory=list)
    organic_inputs: str | None = None
    soil_test: SoilTest | None = None
    water_source: list[str] = Field(default_factory=list)
    water_reliability: str | None = None
    irrigation_method: str | None = None
    irrigation_interval_summer: float | None = None
    irrigation_interval_winter: float | None = None
    water_quality: str | None = None
    water_cost: str | None = None
    last_crop: CropSeason | None = None
    prev_crop: CropSeason | None = None
    bare_periods: str | None = None
    pest_issues: list[str] = Field(default_factory=list)
    fertilizer_level: str | None = None
    priorities: list[str] = Field(default_factory=list)
    risk_tolerance: str | None = None
    equipment: list[str] = Field(default_factory=list)
    horizon: str | None = None
    unknown_answers: list[str] = Field(default_factory=list)

    @property
    def area_feddan(self) -> float:
        return self.area_ha / FEDDAN_HA


# ---------------------------------------------------------------- facts

class Fact(BaseModel):
    """One statement. `code` + `params` let us render it in any language without an LLM."""

    code: str
    params: dict[str, Any] = Field(default_factory=dict)
    text: str = ""     # English rendering, for the LLM and the UI
    text_ar: str = ""  # Arabic rendering, for the UI


# ---------------------------------------------------------------- strategies

class Slot(BaseModel):
    year: int
    season: Season
    crop: str


class CropMetrics(BaseModel):
    crop: str
    season: Season
    etc_mm: float                # crop water use over the season (mm)
    irrigation_mm: float         # net irrigation need after effective rain (mm)
    gross_m3_per_feddan: float   # water to apply, after irrigation losses
    heat_days: float             # mean hot days per year in the sensitive stage
    gdd: float                   # growing degree days over the season


class Strategy(BaseModel):
    id: str
    kind: Literal["current", "practice", "soil", "water", "income", "fodder", "balanced", "custom"]
    name: str
    name_ar: str
    sequence: list[str]          # e.g. ["wheat (winter)", "rice (summer)", ...]
    slots: list[Slot]
    scores: dict[str, int]       # criteria + "overall", 0-100
    metrics: dict[str, float]
    evidence: list[Fact]
    benefits: list[Fact]
    gaps: list[Fact]
    risks: list[Fact]
    confidence: Confidence
    confidence_score: int
    changes_from_current: int
    practices: list[str] = Field(default_factory=list)   # practice ids (practice options only)


# ---------------------------------------------------------------- pack

class DataQuality(BaseModel):
    unknown_answers: list[str]
    layers_used: list[str]
    layers_mocked: list[str]
    layers_unavailable: list[str]
    notes: list[Fact]


class EvidencePack(BaseModel):
    version: str = "1"
    field: dict[str, Any]
    farmer_priorities: list[str]
    weights: dict[str, float]
    scenario: dict[str, float]
    data_quality: DataQuality
    observations: dict[str, Any]
    strategies: list[Strategy]
    recommended_id: str


# ---------------------------------------------------------------- narrative

class StrategyText(BaseModel):
    id: str
    summary: str
    why: str
    evidence: list[str]
    benefits: list[str]
    gaps: list[str]
    risks: list[str]


class Narrative(BaseModel):
    overview: str
    strategies: list[StrategyText]
    reminder: str


class NarrativeOut(Narrative):
    lang: Lang
    source: Literal["llm", "template"]
    fallback_reason: str | None = None   # why the LLM text was not used (for debugging)
