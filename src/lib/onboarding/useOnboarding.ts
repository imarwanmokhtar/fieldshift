"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { createClient } from "@/lib/supabase/client";
import type {
    AnswerValue,
    OnboardingAnswers,
    OnboardingState,
    UseOnboardingReturn,
    FieldProfile,
} from "./types";
import {
    ONBOARDING_QUESTIONS,
    TOTAL_QUESTIONS,
    getQuestionById,
} from "./questions";

export function useOnboarding(
    locale: "ar" | "en",
    initialProfile?: FieldProfile | null
): UseOnboardingReturn {
    const supabase = createClient();

    const [state, setState] = useState<OnboardingState>({
        answers: initialProfile?.answers ?? {},
        currentStep: initialProfile?.current_step ?? 0,
        status: initialProfile?.status ?? "in_progress",
        isSaving: false,
        lastSaved: null,
        error: null,
    });

    const isMountedRef = useRef(true);

    // Save immediately (used for Finish button)
    const saveNow = useCallback(async () => {
        setState((prev) => ({ ...prev, isSaving: true }));

        try {
            const {
                data: { user },
            } = await supabase.auth.getUser();
            if (!user) throw new Error("Not authenticated");

            const { error } = await supabase.from("field_profiles").upsert(
                {
                    user_id: user.id,
                    answers: state.answers,
                    current_step: state.currentStep,
                    status: "completed",
                    updated_at: new Date().toISOString(),
                },
                { onConflict: "user_id" }
            );

            if (error) throw error;

            setState((prev) => ({
                ...prev,
                isSaving: false,
                status: "completed",
                lastSaved: Date.now(),
                error: null,
            }));
        } catch (err) {
            setState((prev) => ({
                ...prev,
                isSaving: false,
                error: err instanceof Error ? err.message : "Failed to save",
            }));
        }
    }, [supabase, state.answers, state.currentStep]);

    // Update a single answer
    const updateAnswer = useCallback((id: string, value: AnswerValue) => {
        setState((prev) => {
            const newAnswers = { ...prev.answers, [id]: value };
            return { ...prev, answers: newAnswers, error: null };
        });
    }, []);

    // Navigation
    const goNext = useCallback(() => {
        setState((prev) => {
            const question = ONBOARDING_QUESTIONS[prev.currentStep];
            if (question?.required && !prev.answers[question.id]) {
                return prev; // Can't advance
            }
            const nextStep = Math.min(prev.currentStep + 1, TOTAL_QUESTIONS);
            return { ...prev, currentStep: nextStep };
        });
    }, []);

    const goBack = useCallback(() => {
        setState((prev) => {
            const nextStep = Math.max(prev.currentStep - 1, 0);
            return { ...prev, currentStep: nextStep };
        });
    }, []);

    const goToStep = useCallback((step: number) => {
        const clamped = Math.max(0, Math.min(step, TOTAL_QUESTIONS));
        setState((prev) => {
            return { ...prev, currentStep: clamped };
        });
    }, []);

    const finish = useCallback(async () => {
        await saveNow();
    }, [saveNow]);

    // Cleanup
    useEffect(() => {
        isMountedRef.current = true;
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    const currentQuestion =
        state.currentStep < TOTAL_QUESTIONS
            ? ONBOARDING_QUESTIONS[state.currentStep]
            : null;

    const progress =
        TOTAL_QUESTIONS > 0 ? (state.currentStep + 1) / TOTAL_QUESTIONS : 0;

    const canGoNext =
        currentQuestion != null &&
        (!currentQuestion.required || !!state.answers[currentQuestion.id]);

    return {
        ...state,
        goNext,
        goBack,
        goToStep,
        updateAnswer,
        saveNow,
        finish,
        isFirstStep: state.currentStep === 0,
        isLastStep: state.currentStep >= TOTAL_QUESTIONS - 1,
        currentQuestion: currentQuestion!,
        progress,
        canGoNext,
    };
}

// Server-side helper to fetch profile
export async function getFieldProfile(
    supabase: ReturnType<typeof createClient>
): Promise<FieldProfile | null> {
    const {
        data: { user },
    } = await supabase.auth.getUser();
    if (!user) return null;

    const { data, error } = await supabase
        .from("field_profiles")
        .select("*")
        .eq("user_id", user.id)
        .single();

    if (error && error.code !== "PGRST116") {
        // PGRST116 = no rows returned
        throw error;
    }
    return data;
}
