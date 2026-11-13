"use client";

import { cn } from "@/lib/utils";
import type { Locale } from "@/lib/i18n";
import type { QuestionConfig } from "@/lib/onboarding/questions";
import { getLocalizedOption } from "@/lib/onboarding/questions";

interface NumberWithUnitProps {
    question: QuestionConfig;
    locale: Locale;
    value: { value: number; unit: string; hectares: number } | "unknown" | undefined;
    onChange: (value: { value: number; unit: string; hectares: number } | "unknown") => void;
    allowUnknown: boolean;
    error?: string;
}

export function NumberWithUnit({
    question,
    locale,
    value,
    onChange,
    allowUnknown,
    error,
}: NumberWithUnitProps) {
    const unitOptions = question.unitOptions ?? [];

    const handleNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const raw = e.target.value;
        if (raw === "") {
            onChange("unknown");
            return;
        }
        const num = parseFloat(raw);
        if (isNaN(num) || num <= 0) return;
        const currentUnit = value !== "unknown" && typeof value === "object" ? value.unit : unitOptions[0]?.value ?? "feddan";
        const unitOpt = unitOptions.find((u) => u.value === currentUnit);
        const hectares = num * (unitOpt?.toHectares ?? 1);
        onChange({ value: num, unit: currentUnit, hectares });
    };

    const handleUnitChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const newUnit = e.target.value;
        const currentValue = value !== "unknown" && typeof value === "object" ? value.value : 0;
        const unitOpt = unitOptions.find((u) => u.value === newUnit);
        const hectares = currentValue * (unitOpt?.toHectares ?? 1);
        onChange({ value: currentValue, unit: newUnit, hectares });
    };

    const currentValue = value !== "unknown" && typeof value === "object" ? value.value : "";
    const currentUnit = value !== "unknown" && typeof value === "object" ? value.unit : unitOptions[0]?.value ?? "feddan";

    return (
        <div className="space-y-4">
            <div className="flex gap-3">
                <div className="flex-1">
                    <label className="sr-only">
                        {locale === "ar" ? "القيمة" : "Value"}
                    </label>
                    <input
                        type="number"
                        min="0.01"
                        step="0.01"
                        value={currentValue}
                        onChange={handleNumberChange}
                        placeholder={locale === "ar" ? "المساحة" : "Area"}
                        className={cn(
                            "w-full h-14 border-[3px] border-ink bg-paper px-4",
                            "font-heading text-xl font-bold text-center",
                            "shadow-brutal-sm",
                            "focus:outline-none focus-visible:ring-4 focus-visible:ring-ink"
                        )}
                        aria-invalid={!!error}
                    />
                </div>
                <div className="w-[140px] flex-shrink-0">
                    <label className="sr-only">
                        {locale === "ar" ? "الوحدة" : "Unit"}
                    </label>
                    <select
                        value={currentUnit}
                        onChange={handleUnitChange}
                        className={cn(
                            "w-full h-14 border-[3px] border-ink bg-paper px-3",
                            "font-heading text-base font-bold",
                            "shadow-brutal-sm appearance-none",
                            "focus:outline-none focus-visible:ring-4 focus-visible:ring-ink",
                            locale === "ar" ? "text-right" : "text-left"
                        )}
                    >
                        {unitOptions.map((u) => (
                            <option key={u.value} value={u.value}>
                                {getLocalizedOption(u, locale)}
                            </option>
                        ))}
                    </select>
                </div>
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