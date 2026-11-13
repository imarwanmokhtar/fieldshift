"use client";

import { cn } from "@/lib/utils";
import type { Locale } from "@/lib/i18n";
import type { QuestionConfig } from "@/lib/onboarding/questions";
import { OptionTile } from "./OptionTile";
import { getLocalizedOption } from "@/lib/onboarding/questions";

interface RankSelectProps {
    question: QuestionConfig;
    locale: Locale;
    value: string[] | "unknown" | undefined;
    onChange: (value: string[] | "unknown") => void;
    allowUnknown: boolean;
    error?: string;
    maxRank?: number;
}

export function RankSelect({
    question,
    locale,
    value = [],
    onChange,
    allowUnknown,
    error,
    maxRank = 3,
}: RankSelectProps) {
    const options = question.options ?? [];
    const ranked = new Set(value);

    const handleSelect = (optValue: string) => {
        if (optValue === "unknown") {
            onChange("unknown");
            return;
        }

        const current = Array.from(ranked);
        if (current.includes(optValue)) {
            // Unrank - remove and shift others up
            const filtered = current.filter((v) => v !== optValue);
            onChange(filtered);
        } else if (current.length < maxRank) {
            // Add to end
            onChange([...current, optValue]);
        }
        // If at max, ignore (could show a toast, but keeping simple)
    };

    return (
        <div className="space-y-4">
            <p className="text-sm opacity-70">
                {locale === "ar"
                    ? `اختر حتى ${maxRank} بالترتيب (الأول = الأهم)`
                    : `Pick up to ${maxRank}, in order (1 = most important)`}
            </p>
            <div
                className="grid gap-3"
                role="list"
                aria-label={question.title[locale] ?? question.title.en}
            >
                {options.map((opt, index) => {
                    const rank = value.indexOf(opt.value) + 1;
                    const isRanked = rank > 0;
                    return (
                        <OptionTile
                            key={opt.value}
                            option={opt}
                            locale={locale}
                            isSelected={isRanked}
                            onSelect={() => handleSelect(opt.value)}
                            rank={isRanked ? rank : undefined}
                            disabled={!isRanked && value.length >= maxRank}
                        />
                    );
                })}
            </div>
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
                <p role="alert" className="text-red-600 text-sm">
                    {error}
                </p>
            )}
        </div>
    );
}