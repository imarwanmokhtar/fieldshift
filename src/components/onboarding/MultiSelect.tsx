"use client";

import { cn } from "@/lib/utils";
import type { Locale } from "@/lib/i18n";
import type { QuestionConfig } from "@/lib/onboarding/questions";
import { OptionTile } from "./OptionTile";
import { getLocalizedOption } from "@/lib/onboarding/questions";

interface MultiSelectProps {
    question: QuestionConfig;
    locale: Locale;
    value: string[] | undefined;
    onChange: (value: string[] | "unknown") => void;
    allowUnknown: boolean;
    error?: string;
}

export function MultiSelect({
    question,
    locale,
    value = [],
    onChange,
    allowUnknown,
    error,
}: MultiSelectProps) {
    const options = question.options ?? [];
    const selected = new Set(value);
    const hasNoneSelected = selected.has("none");

    const handleToggle = (optValue: string) => {
        if (optValue === "unknown") {
            onChange("unknown");
            return;
        }

        if (optValue === "none") {
            // Selecting "None" clears all others
            onChange(["none"]);
            return;
        }

        const newSelected = new Set(selected);
        if (newSelected.has(optValue)) {
            newSelected.delete(optValue);
        } else {
            newSelected.add(optValue);
            // Selecting any option clears "None"
            newSelected.delete("none");
        }
        onChange(Array.from(newSelected));
    };

    return (
        <div
            className={cn(
                "grid gap-3",
                locale === "ar" ? "grid-cols-1" : "sm:grid-cols-2"
            )}
            role="group"
            aria-label={question.title[locale] ?? question.title.en}
            aria-invalid={!!error}
        >
            {options.map((opt) => (
                <OptionTile
                    key={opt.value}
                    option={opt}
                    locale={locale}
                    isSelected={selected.has(opt.value)}
                    onSelect={() => handleToggle(opt.value)}
                    disabled={hasNoneSelected && opt.value !== "none"}
                />
            ))}
            {allowUnknown && (
                <OptionTile
                    option={{
                        value: "unknown",
                        label: {
                            en: "Don't know / Skip",
                            ar: "لا أعرف / تخطي",
                        },
                    }}
                    locale={locale}
                    isSelected={(value as unknown) === "unknown"}
                    onSelect={() => onChange("unknown")}
                    showCheck={false}
                />
            )}
        </div>
    );
}