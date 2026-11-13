"use client";

import { cn } from "@/lib/utils";
import type { Locale } from "@/lib/i18n";
import type { QuestionConfig, Bilingual } from "@/lib/onboarding/questions";

interface QuestionShellProps {
    question: QuestionConfig;
    locale: Locale;
    value: unknown;
    onChange: (value: unknown) => void;
    error?: string;
    isRequired: boolean;
    className?: string;
    children: React.ReactNode;
}

export function QuestionShell({
    question,
    locale,
    value,
    onChange,
    error,
    isRequired,
    className,
    children,
}: QuestionShellProps) {
    const title = question.title[locale] ?? question.title.en;
    const help = question.help?.[locale] ?? question.help?.en;

    return (
        <fieldset
            className={cn(
                "w-full max-w-2xl mx-auto",
                className
            )}
        >
            <legend className="sr-only">{title}</legend>

            <div className="space-y-4">
                <div className="space-y-1">
                    <h1
                        className={cn(
                            "font-heading text-2xl font-bold uppercase tracking-tight",
                            locale === "ar" ? "text-right" : "text-left"
                        )}
                    >
                        {title}
                        {isRequired && (
                            <span className="ml-2 text-green-dark" aria-hidden="true">
                                *
                            </span>
                        )}
                    </h1>
                    {help && (
                        <p
                            className={cn(
                                "text-base opacity-70",
                                locale === "ar" ? "text-right" : "text-left"
                            )}
                        >
                            {help}
                        </p>
                    )}
                </div>

                <div
                    className={cn(
                        "min-h-[120px]",
                        locale === "ar" ? "rtl" : "ltr"
                    )}
                    role="group"
                    aria-labelledby={`question-${question.id}-label`}
                >
                    {children}
                </div>

                {error && (
                    <div
                        role="alert"
                        aria-live="assertive"
                        className={cn(
                            "border-[3px] border-ink bg-green-light p-3 text-base font-medium shadow-brutal-sm",
                            locale === "ar" ? "text-right" : "text-left"
                        )}
                    >
                        {error}
                    </div>
                )}
            </div>
        </fieldset>
    );
}