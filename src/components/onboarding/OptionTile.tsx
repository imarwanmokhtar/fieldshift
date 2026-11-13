"use client";

import { cn } from "@/lib/utils";
import type { Locale } from "@/lib/i18n";
import type { QuestionOption, Bilingual } from "@/lib/onboarding/questions";

interface OptionTileProps {
    option: QuestionOption;
    locale: Locale;
    isSelected: boolean;
    onSelect: () => void;
    disabled?: boolean;
    rank?: number; // for rank type
    showCheck?: boolean;
    className?: string;
}

export function OptionTile({
    option,
    locale,
    isSelected,
    onSelect,
    disabled,
    rank,
    showCheck = true,
    className,
}: OptionTileProps) {
    const label = option.label[locale] ?? option.label.en;

    return (
        <button
            type="button"
            onClick={onSelect}
            disabled={disabled}
            className={cn(
                "relative group w-full min-h-[64px] border-[3px] border-ink px-4 py-3",
                "font-heading text-base font-bold uppercase tracking-wide",
                "shadow-brutal transition-all duration-150",
                "active:translate-x-[3px] active:translate-y-[3px] active:shadow-none",
                "motion-reduce:transition-none",
                "disabled:pointer-events-none disabled:opacity-50",
                "focus:outline-none focus-visible:ring-4 focus-visible:ring-ink",
                isSelected
                    ? "bg-green-dark text-paper shadow-[6px_6px_0_0_#0a0a0a]"
                    : "bg-green-light text-ink shadow-[6px_6px_0_0_#0a0a0a] hover:shadow-[8px_8px_0_0_#0a0a0a]",
                locale === "ar" ? "text-right" : "text-left",
                className
            )}
            aria-pressed={isSelected}
        >
            {rank && (
                <span
                    className={cn(
                        "absolute -top-3 -right-3 w-8 h-8 rounded-[2px] border-[2px] border-ink flex items-center justify-center text-xs font-bold",
                        isSelected
                            ? "bg-paper text-ink"
                            : "bg-green-light text-ink"
                    )}
                    aria-hidden="true"
                >
                    {rank}
                </span>
            )}
            <span className="relative z-10 flex items-center gap-3">
                {showCheck && isSelected && (
                    <svg
                        className="w-6 h-6 flex-shrink-0"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="3"
                        aria-hidden="true"
                    >
                        <polyline points="20 6 9 17 4 12" />
                    </svg>
                )}
                <span>{label}</span>
            </span>
        </button>
    );
}