"use client";

import { cn } from "@/lib/utils";
import type { Locale } from "@/lib/i18n";
import type { QuestionConfig } from "@/lib/onboarding/questions";
import { OptionTile } from "./OptionTile";
import { getLocalizedString, getLocalizedOption } from "@/lib/onboarding/questions";

interface SingleSelectProps {
    question: QuestionConfig;
    locale: Locale;
    value: string | undefined;
    onChange: (value: string | "unknown") => void;
    allowUnknown: boolean;
    error?: string;
}

export function SingleSelect({
    question,
    locale,
    value,
    onChange,
    allowUnknown,
    error,
}: SingleSelectProps) {
    const options = question.options ?? [];

    return (
        <div
            className={cn(
                "grid gap-3",
                locale === "ar" ? "grid-cols-1" : "sm:grid-cols-2"
            )}
            role="radiogroup"
            aria-label={question.title[locale] ?? question.title.en}
            aria-invalid={!!error}
        >
            {options.map((opt) => (
                <OptionTile
                    key={opt.value}
                    option={opt}
                    locale={locale}
                    isSelected={value === opt.value}
                    onSelect={() => onChange(opt.value)}
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
                    isSelected={value === "unknown"}
                    onSelect={() => onChange("unknown")}
                    showCheck={false}
                />
            )}
        </div>
    );
}