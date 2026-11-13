"use client";

import { cn } from "@/lib/utils";
import type { Locale } from "@/lib/i18n";
import type { QuestionConfig } from "@/lib/onboarding/questions";

interface TwoNumbersProps {
    question: QuestionConfig;
    locale: Locale;
    value: { summer: number; winter: number } | "unknown" | undefined;
    onChange: (value: { summer: number; winter: number } | "unknown") => void;
    allowUnknown: boolean;
    error?: string;
    min?: number;
    max?: number;
}

export function TwoNumbers({
    question,
    locale,
    value,
    onChange,
    allowUnknown,
    error,
    min = 1,
    max = 60,
}: TwoNumbersProps) {
    const handleChange = (field: "summer" | "winter", e: React.ChangeEvent<HTMLInputElement>) => {
        const raw = e.target.value;
        if (raw === "") {
            onChange("unknown");
            return;
        }
        const num = parseInt(raw, 10);
        if (isNaN(num) || num < min || num > max) return;
        const current = value !== "unknown" && typeof value === "object" ? value : { summer: 0, winter: 0 };
        onChange({ ...current, [field]: num });
    };

    const summer = value !== "unknown" && typeof value === "object" ? value.summer : "";
    const winter = value !== "unknown" && typeof value === "object" ? value.winter : "";

    return (
        <div className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                    <label className="font-heading text-sm font-bold uppercase tracking-wide">
                        {locale === "ar" ? "فصل الصيف (أيام)" : "Summer (days)"}
                    </label>
                    <input
                        type="number"
                        min={min}
                        max={max}
                        value={summer}
                        onChange={(e) => handleChange("summer", e)}
                        placeholder={locale === "ar" ? "مثال: 7" : "e.g., 7"}
                        className={cn(
                            "w-full h-14 border-[3px] border-ink bg-paper px-4",
                            "font-heading text-xl font-bold text-center",
                            "shadow-brutal-sm",
                            "focus:outline-none focus-visible:ring-4 focus-visible:ring-ink"
                        )}
                        aria-invalid={!!error}
                    />
                </div>
                <div className="space-y-2">
                    <label className="font-heading text-sm font-bold uppercase tracking-wide">
                        {locale === "ar" ? "فصل الشتاء (أيام)" : "Winter (days)"}
                    </label>
                    <input
                        type="number"
                        min={min}
                        max={max}
                        value={winter}
                        onChange={(e) => handleChange("winter", e)}
                        placeholder={locale === "ar" ? "مثال: 14" : "e.g., 14"}
                        className={cn(
                            "w-full h-14 border-[3px] border-ink bg-paper px-4",
                            "font-heading text-xl font-bold text-center",
                            "shadow-brutal-sm",
                            "focus:outline-none focus-visible:ring-4 focus-visible:ring-ink"
                        )}
                        aria-invalid={!!error}
                    />
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