/** Shapes of the engine output stored in `analyses.result` and `analyses.narrative`. */

export type Criterion = "water" | "heat" | "soil" | "income" | "cost" | "risk" | "forage";

export interface Fact {
  code: string;
  params: Record<string, unknown>;
  text: string;
  text_ar?: string;
}

export interface Slot {
  year: number;
  season: "winter" | "summer";
  crop: string;
}

export interface Strategy {
  id: string;
  kind: "current" | "practice" | "soil" | "water" | "income" | "fodder" | "balanced" | "custom";
  name: string;
  name_ar: string;
  sequence: string[];
  slots: Slot[];
  scores: Record<Criterion | "overall", number>;
  metrics: Record<string, number>;
  evidence: Fact[];
  benefits: Fact[];
  gaps: Fact[];
  risks: Fact[];
  confidence: "high" | "medium" | "low";
  confidence_score: number;
  changes_from_current: number;
  /** Water-saving practice ids (practice options only), e.g. "laser_leveling". */
  practices?: string[];
}

export interface EvidencePack {
  field: { lat: number; lng: number; area_feddan: number; area_ha: number; current_rotation: string[] };
  farmer_priorities: string[];
  weights: Record<Criterion, number>;
  data_quality: {
    unknown_answers: string[];
    layers_used: string[];
    layers_mocked: string[];
    layers_unavailable: string[];
    notes: Fact[];
  };
  observations: {
    climate_source: "nasa_power" | "fallback_climatology";
    hot_days_per_year?: { mean: number; trend_per_year: number };
    rain_mm_per_year?: number;
    reference_et0_mm_per_year?: number;
    [key: string]: unknown;
  };
  strategies: Strategy[];
  recommended_id: string;
}

export interface StrategyText {
  id: string;
  summary: string;
  why: string;
  evidence: string[];
  benefits: string[];
  gaps: string[];
  risks: string[];
}

export interface Narrative {
  overview: string;
  strategies: StrategyText[];
  reminder: string;
  lang: "ar" | "en";
  source: "llm" | "template";
  fallback_reason?: string | null;
}

export type AnalysisStatus = "pending" | "running" | "done" | "failed";

export interface AnalysisRow {
  id: string;
  status: AnalysisStatus;
  stage: string | null;
  lang: "ar" | "en";
  result: EvidencePack | null;
  narrative: Narrative | null;
  error: string | null;
  created_at: string;
  updated_at?: string;
  field_id?: string | null;
}
