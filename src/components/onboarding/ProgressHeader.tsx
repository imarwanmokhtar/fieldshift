"use client";

import { cn } from "@/lib/utils";
import type { Locale } from "@/lib/i18n";

interface ProgressHeaderProps {
    currentStep: number;
    totalSteps: number;
    sectionLabel: string;
    locale: Locale;
    className?: string;
}

export function ProgressHeader({
    currentStep,
    totalSteps,
    sectionLabel,
    locale,
    className,
}: ProgressHeaderProps) {
    const progress = totalSteps > 0 ? (currentStep + 1) / totalSteps : 0;
    const percent = Math.round(progress * 100);
    const counter = `${String(currentStep + 1).padStart(2, "0")} / ${totalSteps}`;

    return (
        <header
            className={cn(
                "mb-8",
                locale === "ar" ? "rtl" : "ltr",
                className
            )}
            role="region"
            aria-label={locale === "ar" ? "شريط التقدم" : "Progress"}
        >
            <div
                className="font-heading text-xs font-bold uppercase tracking-widest mb-2"
                aria-live="polite"
            >
                {sectionLabel}
            </div>
            <div className="flex items-center gap-3 mb-2">
                <span className="font-mono text-sm font-bold tabular-nums">
                    {counter}
                </span>
                <div
                    role="progressbar"
                    aria-valuenow={currentStep + 1}
                    aria-valuemin={1}
                    aria-valuemax={totalSteps}
                    aria-label={
                        locale === "ar"
                            ? `التقدم: ${percent}%`
                            : `Progress: ${percent}%`
                    }
                    className="flex-1 h-4 border-[3px] border-ink bg-green-light shadow-brutal-xs overflow-hidden"
                >
                    <div
                        className="h-full bg-green-dark transition-all duration-300 ease-out motion-reduce:transition-none"
                        style={{ width: `${progress * 100}%` }}
                    />
                </div>
            </div>
        </header>
    );
}