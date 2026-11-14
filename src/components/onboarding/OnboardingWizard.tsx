"use client";

import { useState, useCallback, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { Locale } from "@/lib/i18n";
import {
    ONBOARDING_QUESTIONS,
    TOTAL_QUESTIONS,
    getLocalizedString,
} from "@/lib/onboarding/questions";
import type { AnswerValue, FieldProfile } from "@/lib/onboarding/types";
import { useOnboarding } from "@/lib/onboarding/useOnboarding";
import { ProgressHeader } from "./ProgressHeader";
import { QuestionShell } from "./QuestionShell";
import { SingleSelect } from "./SingleSelect";
import { MultiSelect } from "./MultiSelect";
import { NumberInput } from "./NumberInput";
import { NumberWithUnit } from "./NumberWithUnit";
import { TextInput } from "./TextInput";
import { TwoNumbers } from "./TwoNumbers";
import { CropAndSeason } from "./CropAndSeason";
import { RankSelect } from "./RankSelect";
import { SoilTest } from "./SoilTest";
import { MapPin } from "./MapPin";
import { SummaryScreen } from "./SummaryScreen";
import { BrutalButton } from "@/components/brutal-button";

interface OnboardingWizardProps {
    locale: Locale;
    initialProfile?: FieldProfile | null;
    onComplete: () => void | Promise<void>;
}

export function OnboardingWizard({ locale, initialProfile, onComplete }: OnboardingWizardProps) {
    const {
        answers,
        currentStep,
        status,
        isSaving,
        lastSaved,
        error,
        goNext,
        goBack,
        goToStep,
        updateAnswer,
        saveNow,
        finish,
        isFirstStep,
        isLastStep,
        currentQuestion,
        progress,
        canGoNext,
    } = useOnboarding(locale, initialProfile);

    const [showSummary, setShowSummary] = useState(false);
    const [direction, setDirection] = useState<"forward" | "backward">("forward");

    // Validate required fields
    const validateStep = useCallback((step: number) => {
        if (step >= TOTAL_QUESTIONS) return true;
        const q = ONBOARDING_QUESTIONS[step];
        if (q.required && !answers[q.id]) {
            return false;
        }
        return true;
    }, [answers]);

    const handleNext = useCallback(() => {
        if (!canGoNext) return;
        setDirection("forward");
        goNext();
    }, [canGoNext, goNext]);

    const handleBack = useCallback(() => {
        setDirection("backward");
        goBack();
    }, [goBack]);

    const handleFinish = useCallback(async () => {
        await finish();
        setShowSummary(false);
        await onComplete();
    }, [finish, onComplete]);

    const handleEdit = useCallback((questionId: string) => {
        const idx = ONBOARDING_QUESTIONS.findIndex((q) => q.id === questionId);
        if (idx >= 0) {
            setShowSummary(false);
            goToStep(idx);
        }
    }, [goToStep]);

    // Show summary when on the last step and user clicks Next/Finish
    const shouldShowSummary = currentStep >= TOTAL_QUESTIONS;
    const onQuestion = !shouldShowSummary && !showSummary;

    // Enter = Next (or Finish on the last question). Enter keeps its own meaning on
    // links and on controls marked data-enter-native (Back, Skip). On answer tiles it
    // also means Next, so it never un-ticks a choice; Space still selects a tile.
    // Backspace = Back, except while typing in a field (there it deletes text).
    // Arrow up/down = move between answer tiles (Space selects the focused tile).
    useEffect(() => {
        if (!onQuestion) return;
        function onKeyDown(e: KeyboardEvent) {
            if (e.repeat || e.isComposing || e.shiftKey || e.altKey || e.ctrlKey || e.metaKey) return;
            const target = e.target as HTMLElement | null;
            if (e.key === "ArrowDown" || e.key === "ArrowUp") {
                if (target?.closest("input, textarea, select, [contenteditable]:not([contenteditable='false'])")) return;
                const tiles = Array.from(document.querySelectorAll<HTMLButtonElement>("[data-option-tile]:not(:disabled)"));
                if (tiles.length === 0) return;
                e.preventDefault(); // move between answers instead of scrolling the page
                const at = tiles.indexOf(document.activeElement as HTMLButtonElement);
                const step = e.key === "ArrowDown" ? 1 : -1;
                const next = at === -1
                    ? (step === 1 ? 0 : tiles.length - 1)
                    : (at + step + tiles.length) % tiles.length;
                tiles[next].focus();
                tiles[next].scrollIntoView({ block: "nearest" });
                return;
            }
            if (e.key === "Backspace") {
                if (target?.closest("input, textarea, select, [contenteditable]:not([contenteditable='false'])")) return;
                e.preventDefault();
                if (!isFirstStep) handleBack();
                return;
            }
            if (e.key !== "Enter") return;
            if (target?.closest("a, textarea, [data-enter-native]")) return;
            e.preventDefault();
            if (!canGoNext || isSaving) return;
            if (isLastStep) setShowSummary(true);
            else handleNext();
        }
        // Capture phase: runs before any element can handle or stop the key.
        window.addEventListener("keydown", onKeyDown, true);
        return () => window.removeEventListener("keydown", onKeyDown, true);
    }, [onQuestion, canGoNext, isSaving, isLastStep, isFirstStep, handleNext, handleBack]);

    return (
        <div className="min-h-screen bg-paper">
            <div className="mx-auto max-w-3xl px-4 py-6 md:py-10">
                {onQuestion && (
                    <>
                        <ProgressHeader
                            currentStep={currentStep}
                            totalSteps={TOTAL_QUESTIONS}
                            sectionLabel={currentQuestion.section}
                            locale={locale}
                        />

                        <AnimatePresence mode="wait">
                            <motion.div
                                key={currentQuestion.id}
                                initial={{ x: direction === "forward" ? 300 : -300, opacity: 0 }}
                                animate={{ x: 0, opacity: 1 }}
                                exit={{ x: direction === "forward" ? -300 : 300, opacity: 0 }}
                                transition={{ duration: 0.22, ease: "easeOut" }}
                                style={{ willChange: "transform, opacity" }}
                            >
                                <QuestionShell
                                    question={currentQuestion}
                                    locale={locale}
                                    value={answers[currentQuestion.id]}
                                    onChange={(val) => updateAnswer(currentQuestion.id, val as AnswerValue)}
                                    error={error ?? undefined}
                                    isRequired={currentQuestion.required ?? false}
                                >
                                    {(() => {
                                        switch (currentQuestion.type) {
                                            case "single":
                                                return (
                                                    <SingleSelect
                                                        question={currentQuestion}
                                                        locale={locale}
                                                        value={answers[currentQuestion.id] as string | undefined}
                                                        onChange={(val) => updateAnswer(currentQuestion.id, val as AnswerValue)}
                                                        allowUnknown={false /* the small "Don't know / Skip" link below handles skipping */}
                                                    />
                                                );
                                            case "multi":
                                                return (
                                                    <MultiSelect
                                                        question={currentQuestion}
                                                        locale={locale}
                                                        value={answers[currentQuestion.id] as string[] | undefined}
                                                        onChange={(val) => updateAnswer(currentQuestion.id, val as AnswerValue)}
                                                        allowUnknown={false /* the small "Don't know / Skip" link below handles skipping */}
                                                    />
                                                );
                                            case "number":
                                                return (
                                                    <NumberInput
                                                        question={currentQuestion}
                                                        locale={locale}
                                                        value={answers[currentQuestion.id] as number | string | undefined}
                                                        onChange={(val) => updateAnswer(currentQuestion.id, val as AnswerValue)}
                                                        allowUnknown={false /* the small "Don't know / Skip" link below handles skipping */}
                                                    />
                                                );
                                            case "numberWithUnit":
                                                return (
                                                    <NumberWithUnit
                                                        question={currentQuestion}
                                                        locale={locale}
                                                        value={answers[currentQuestion.id] as any}
                                                        onChange={(val) => updateAnswer(currentQuestion.id, val as AnswerValue)}
                                                        allowUnknown={false /* the small "Don't know / Skip" link below handles skipping */}
                                                    />
                                                );
                                            case "text":
                                                return (
                                                    <TextInput
                                                        question={currentQuestion}
                                                        locale={locale}
                                                        value={answers[currentQuestion.id] as string | undefined}
                                                        onChange={(val) => updateAnswer(currentQuestion.id, val as AnswerValue)}
                                                        allowUnknown={false /* the small "Don't know / Skip" link below handles skipping */}
                                                    />
                                                );
                                            case "twoNumbers":
                                                return (
                                                    <TwoNumbers
                                                        question={currentQuestion}
                                                        locale={locale}
                                                        value={answers[currentQuestion.id] as any}
                                                        onChange={(val) => updateAnswer(currentQuestion.id, val as AnswerValue)}
                                                        allowUnknown={false /* the small "Don't know / Skip" link below handles skipping */}
                                                    />
                                                );
                                            case "cropAndSeason":
                                                return (
                                                    <CropAndSeason
                                                        question={currentQuestion}
                                                        locale={locale}
                                                        value={answers[currentQuestion.id] as any}
                                                        onChange={(val) => updateAnswer(currentQuestion.id, val as AnswerValue)}
                                                        allowUnknown={false /* the small "Don't know / Skip" link below handles skipping */}
                                                    />
                                                );
                                            case "rank":
                                                return (
                                                    <RankSelect
                                                        question={currentQuestion}
                                                        locale={locale}
                                                        value={answers[currentQuestion.id] as string[] | undefined}
                                                        onChange={(val) => updateAnswer(currentQuestion.id, val as AnswerValue)}
                                                        allowUnknown={false /* the small "Don't know / Skip" link below handles skipping */}
                                                    />
                                                );
                                            case "soilTest":
                                                return (
                                                    <SoilTest
                                                        question={currentQuestion}
                                                        locale={locale}
                                                        value={answers[currentQuestion.id] as any}
                                                        onChange={(val) => updateAnswer(currentQuestion.id, val as AnswerValue)}
                                                        allowUnknown={false /* the small "Don't know / Skip" link below handles skipping */}
                                                    />
                                                );
                                            case "mapPin":
                                                return (
                                                    <MapPin
                                                        question={currentQuestion}
                                                        locale={locale}
                                                        value={answers[currentQuestion.id] as any}
                                                        onChange={(val) => updateAnswer(currentQuestion.id, val as AnswerValue)}
                                                        allowUnknown={false /* the small "Don't know / Skip" link below handles skipping */}
                                                    />
                                                );
                                            default:
                                                return null;
                                        }
                                    })()}
                                </QuestionShell>
                            </motion.div>
                        </AnimatePresence>

                        {/* Action Bar */}
                        <div className="mt-8 flex gap-3">
                            <div data-enter-native className="flex flex-1">
                                <BrutalButton
                                    variant="paper"
                                    onClick={handleBack}
                                    disabled={isFirstStep}
                                    className="flex-1"
                                >
                                    {locale === "ar" ? "رجوع" : "Back"}
                                </BrutalButton>
                            </div>
                            {isLastStep ? (
                                <BrutalButton
                                    variant="dark"
                                    onClick={() => setShowSummary(true)}
                                    disabled={!canGoNext || isSaving}
                                    className="flex-1"
                                >
                                    {locale === "ar" ? "إنهاء" : "Finish"}
                                </BrutalButton>
                            ) : (
                                <BrutalButton
                                    variant="dark"
                                    onClick={handleNext}
                                    disabled={!canGoNext || isSaving}
                                    className="flex-1"
                                >
                                    {locale === "ar" ? "التالي" : "Next"}
                                </BrutalButton>
                            )}
                        </div>

                        {/* Keyboard shortcuts (handled by the keydown effect above) */}
                        <p className="mt-3 hidden text-center font-mono text-xs opacity-60 sm:block" data-kb-hint>
                            {locale === "ar"
                                ? "↑ ↓ تنقل بين الخيارات · Space اختيار · Enter ↵ التالي · Backspace ⌫ رجوع"
                                : "↑ ↓ move · Space select · Enter ↵ Next · Backspace ⌫ Back"}
                        </p>

                        {/* Skip button for optional questions */}
                        {(currentQuestion.allowUnknown ?? true) && !currentQuestion.required && (
                            <div className="mt-4 text-center">
                                <button
                                    type="button"
                                    data-enter-native
                                    onClick={() => {
                                        updateAnswer(currentQuestion.id, "unknown");
                                        handleNext();
                                    }}
                                    className={cn(
                                        "inline-block font-heading text-sm font-bold uppercase tracking-wide",
                                        "underline decoration-[2px] underline-offset-2",
                                        "hover:bg-ink hover:text-paper",
                                        "focus:outline-none focus-visible:ring-4 focus-visible:ring-ink"
                                    )}
                                >
                                    {locale === "ar" ? "لا أعرف / تخطي" : "Don't know / Skip"}
                                </button>
                            </div>
                        )}

                        {/* Save status indicator */}
                        {lastSaved && (
                            <p className="mt-4 text-center text-xs opacity-60 font-mono">
                                {locale === "ar"
                                    ? `تم الحفظ: ${new Date(lastSaved).toLocaleTimeString(locale)}`
                                    : `Saved: ${new Date(lastSaved).toLocaleTimeString(locale)}`}
                            </p>
                        )}
                        {isSaving && (
                            <p className="mt-4 text-center text-xs opacity-60 font-mono animate-pulse">
                                {locale === "ar" ? "جاري الحفظ..." : "Saving..."}
                            </p>
                        )}
                        {error && (
                            <p className="mt-4 text-center text-sm text-red-600" role="alert">
                                {error}
                            </p>
                        )}
                    </>
                )}

                {(shouldShowSummary || showSummary) && (
                    <SummaryScreen
                        locale={locale}
                        answers={answers}
                        onEdit={handleEdit}
                        onFinish={handleFinish}
                    />
                )}
            </div>
        </div>
    );
}