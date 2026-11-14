/**
 * Onboarding answer types derived from question config
 */

import type { QuestionConfig, QuestionOption } from "./questions";

export type AnswerValue =
    | string
    | string[]
    | number
    | { lat: number; lng: number }
    | { value: number; unit: string; hectares: number }
    | { summer: number; winter: number }
    | { crop: string; season: string }
    | { hasTest: boolean; ph?: number; ec?: number; organicMatter?: number; n?: number; p?: number; k?: number }
    | string[] // rank (ordered)
    | { include: string[]; exclude: string[] };

export interface FieldProfile {
    id: string;
    user_id: string;
    answers: Record<string, AnswerValue>;
    current_step: number;
    status: "in_progress" | "completed";
    created_at: string;
    updated_at: string;
}

export type OnboardingAnswers = Record<string, AnswerValue>;

export interface OnboardingState {
    answers: OnboardingAnswers;
    currentStep: number;
    status: "in_progress" | "completed";
    isSaving: boolean;
    lastSaved: number | null;
    error: string | null;
}

export interface UseOnboardingReturn extends OnboardingState {
    goNext: () => void;
    goBack: () => void;
    goToStep: (step: number) => void;
    updateAnswer: (id: string, value: AnswerValue) => void;
    saveNow: () => Promise<string | null>;
    saveProgress: () => Promise<string | null>;
    finish: () => Promise<string | null>;
    fieldId: string | null;
    isFirstStep: boolean;
    isLastStep: boolean;
    currentQuestion: QuestionConfig;
    progress: number;
    canGoNext: boolean;
}

// Default empty answers object with "unknown" for skippable questions
export function createEmptyAnswers(): OnboardingAnswers {
    return {};
}

export function isAnswerUnknown(value: unknown): boolean {
    return value === "unknown";
}

export function normalizeAnswerForStorage(value: AnswerValue): AnswerValue {
    return value;
}