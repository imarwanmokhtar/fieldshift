"use client";

import { cn } from "@/lib/utils";
import type { Locale } from "@/lib/i18n";
import type { QuestionConfig } from "@/lib/onboarding/questions";

interface NumberInputProps {
    question: QuestionConfig;
    locale: Locale;
    value: number | string | undefined;
    onChange: (value: number | "unknown") => void;
    allowUnknown: boolean;
    error?: string;
    min?: number;
    max?: number;
    step?: number;
    placeholder?: string;
}

export function NumberInput({
    question,
    locale,
    value,
    onChange,
    allowUnknown,
    error,
    min = 0,
    max = 10000,
    step = 1,
    placeholder,
}: NumberInputProps) {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const raw = e.target.value;
        if (raw === "") {
            onChange("unknown");
            return;
        }
        const num = parseFloat(raw);
        if (isNaN(num)) return;
        if (num < min) return;
        if (num > max) return;
        onChange(num);
    };

    const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
        const raw = e.target.value;
        if (raw === "" && allowUnknown) {
            onChange("unknown");
        }
    };

    return (
        <div className="space-y-3">
            <input
                type="number"
                min={min}
                max={max}
                step={step}
                value={value === "unknown" ? "" : value}
                onChange={handleChange}
                onBlur={handleBlur}
                placeholder={placeholder ?? (locale === "ar" ? "أدخل رقماً" : "Enter a number")}
                className={cn(
                    "w-full h-14 border-[3px] border-ink bg-paper px-4",
                    "font-heading text-xl font-bold text-center",
                    "shadow-brutal-sm",
                    "focus:outline-none focus-visible:ring-4 focus-visible:ring-ink",
                    "disabled:opacity-50",
                    locale === "ar" ? "text-right" : "text-left"
                )}
                aria-invalid={!!error}
                aria-describedby={error ? `${question.id}-error` : undefined}
            />
            {allowUnknown && (
                <button
                    type="button"
                    onClick={() => onChange("unknown")}
                    className={cn(
                        "w-full border-2 border-ink bg-paper px-4 py-2",
                        "font-heading text-sm font-bold uppercase tracking-wide",
                        "shadow-brutal-xs hover:bg-ink hover:text-paper",
                        "focus:outline-none focus-visible:ring-4 focus-visible:ring-ink"
                    )}
                >
                    {locale === "ar" ? "لا أعرف / تخطي" : "Don't know / Skip"}
                </button>
            )}
            {error && (
                <p
                    id={`${question.id}-error`}
                    role="alert"
                    className="text-red-600 text-sm"
                >
                    {error}
                </p>
            )}
        </div>
    );
}