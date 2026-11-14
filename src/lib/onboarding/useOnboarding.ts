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
    // One row per field. A new field gets its id on the first save.
    const fieldIdRef = useRef<string | null>(initialProfile?.id ?? null);
    const [fieldId, setFieldId] = useState<string | null>(initialProfile?.id ?? null);
    // Editing a finished field: keep the saved answers until the farmer presses Finish.
    const editingCompleted = initialProfile?.status === "completed";

    const writeProfile = useCallback(
        async (status: "in_progress" | "completed"): Promise<string> => {
            const row = { answers: state.answers, current_step: state.currentStep, status };
            if (fieldIdRef.current) {
                const { error } = await supabase.from("field_profiles").update(row).eq("id", fieldIdRef.current);
                if (error) throw error;
                return fieldIdRef.current;
            }
            const {
                data: { user },
            } = await supabase.auth.getUser();
            if (!user) throw new Error("Not authenticated");
            const { data, error } = await supabase
                .from("field_profiles")
                .insert({ ...row, user_id: user.id })
                .select("id")
                .single();
            if (error) throw error;
            fieldIdRef.current = data.id as string;
            setFieldId(fieldIdRef.current);
            return fieldIdRef.current;
        },
        [supabase, state.answers, state.currentStep]
    );

    // Save immediately as completed (Finish button). Returns the field id, or null on error.
    const saveNow = useCallback(async (): Promise<string | null> => {
        setState((prev) => ({ ...prev, isSaving: true }));
        try {
            const id = await writeProfile("completed");
            setState((prev) => ({
                ...prev,
                isSaving: false,
                status: "completed",
                lastSaved: Date.now(),
                error: null,
            }));
            return id;
        } catch (err) {
            setState((prev) => ({
                ...prev,
                isSaving: false,
                error: err instanceof Error ? err.message : "Failed to save",
            }));
            return null;
        }
    }, [writeProfile]);

    // Save progress so the field exists (it needs an id for the satellite request).
    // A finished field being edited is not touched until Finish.
    const saveProgress = useCallback(async (): Promise<string | null> => {
        if (editingCompleted) return fieldIdRef.current;
        try {
            const id = await writeProfile("in_progress");
            setState((prev) => ({ ...prev, lastSaved: Date.now() }));
            return id;
        } catch {
            return fieldIdRef.current;
        }
    }, [editingCompleted, writeProfile]);

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

    const finish = useCallback(async () => saveNow(), [saveNow]);

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
        saveProgress,
        finish,
        fieldId,
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
