"use client";

import { cn } from "@/lib/utils";
import type { Locale } from "@/lib/i18n";
import type { QuestionConfig } from "@/lib/onboarding/questions";
import { OptionTile } from "./OptionTile";
import { getLocalizedOption } from "@/lib/onboarding/questions";

interface SoilTestProps {
    question: QuestionConfig;
    locale: Locale;
    value:
        | {
              hasTest: boolean;
              ph?: number;
              ec?: number;
              organicMatter?: number;
              n?: number;
              p?: number;
              k?: number;
          }
        | "unknown"
        | undefined;
    onChange: (value:
        | {
              hasTest: boolean;
              ph?: number;
              ec?: number;
              organicMatter?: number;
              n?: number;
              p?: number;
              k?: number;
          }
        | "unknown") => void;
    allowUnknown: boolean;
    error?: string;
}

export function SoilTest({
    question,
    locale,
    value,
    onChange,
    allowUnknown,
    error,
}: SoilTestProps) {
    const hasTest = value !== "unknown" && typeof value === "object" ? value.hasTest : false;
    const testData = value !== "unknown" && typeof value === "object" ? value : {};

    const handleYesNo = (has: boolean) => {
        if (!has) {
            onChange({ hasTest: false });
        } else {
            onChange({ hasTest: true, ...testData });
        }
    };

    const handleFieldChange = (
        field: "ph" | "ec" | "organicMatter" | "n" | "p" | "k",
        e: React.ChangeEvent<HTMLInputElement>
    ) => {
        const raw = e.target.value;
        const num = raw === "" ? undefined : parseFloat(raw);
        if (num !== undefined && isNaN(num)) return;
        onChange({ hasTest: true, ...testData, [field]: num });
    };

    return (
        <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2" role="radiogroup" aria-label={question.title[locale] ?? question.title.en}>
                <OptionTile
                    option={{
                        value: "yes",
                        label: { en: "Yes", ar: "نعم" },
                    }}
                    locale={locale}
                    isSelected={hasTest}
                    onSelect={() => handleYesNo(true)}
                />
                <OptionTile
                    option={{
                        value: "no",
                        label: { en: "No", ar: "لا" },
                    }}
                    locale={locale}
                    isSelected={!hasTest && value !== "unknown" && value !== undefined}
                    onSelect={() => handleYesNo(false)}
                />
            </div>

            {hasTest && (
                <div className="space-y-3 border-t-2 border-ink pt-4">
                    <h3 className="font-heading text-lg font-bold uppercase">
                        {locale === "ar" ? "تفاصيل التحليل (اختياري)" : "Test details (optional)"}
                    </h3>
                    <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
                        {[
                            { key: "ph", label: { en: "pH", ar: "الـ pH" }, step: 0.1, min: 0, max: 14 },
                            { key: "ec", label: { en: "Salinity (EC)", ar: "الملوحة (EC)" }, step: 0.1, min: 0, max: 10 },
                            { key: "organicMatter", label: { en: "Organic matter %", ar: "المادة العضوية %" }, step: 0.1, min: 0, max: 20 },
                            { key: "n", label: { en: "Nitrogen (N)", ar: "النيتروجين (N)" }, step: 1, min: 0, max: 500 },
                            { key: "p", label: { en: "Phosphorus (P)", ar: "الفوسفور (P)" }, step: 1, min: 0, max: 500 },
                            { key: "k", label: { en: "Potassium (K)", ar: "البوتاسيوم (K)" }, step: 1, min: 0, max: 500 },
                        ].map(({ key, label, step, min, max }) => (
                            <div key={key} className="space-y-1">
                                <label className="font-heading text-sm font-bold uppercase tracking-wide">
                                    {label[locale] ?? label.en}
                                </label>
                                <input
                                    type="number"
                                    step={step}
                                    min={min}
                                    max={max}
                                    value={testData[key as keyof typeof testData] ?? ""}
                                    onChange={(e) => handleFieldChange(key as "ph" | "ec" | "organicMatter" | "n" | "p" | "k", e)}
                                    placeholder={locale === "ar" ? "اختياري" : "Optional"}
                                    className={cn(
                                        "w-full h-12 border-[3px] border-ink bg-paper px-3",
                                        "font-heading text-base font-bold text-center",
                                        "shadow-brutal-sm",
                                        "focus:outline-none focus-visible:ring-4 focus-visible:ring-ink"
                                    )}
                                />
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {allowUnknown && !hasTest && (
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