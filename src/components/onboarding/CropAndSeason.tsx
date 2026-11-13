"use client";

import { cn } from "@/lib/utils";
import type { Locale } from "@/lib/i18n";
import type { QuestionConfig } from "@/lib/onboarding/questions";
import { OptionTile } from "./OptionTile";
import { CROP_OPTIONS, SEASON_OPTIONS, getLocalizedOption } from "@/lib/onboarding/questions";

interface CropAndSeasonProps {
    question: QuestionConfig;
    locale: Locale;
    value: { crop: string; season: string } | "unknown" | undefined;
    onChange: (value: { crop: string; season: string } | "unknown") => void;
    allowUnknown: boolean;
    error?: string;
}

export function CropAndSeason({
    question,
    locale,
    value,
    onChange,
    allowUnknown,
    error,
}: CropAndSeasonProps) {
    const currentCrop = value !== "unknown" && typeof value === "object" ? value.crop : "";
    const currentSeason = value !== "unknown" && typeof value === "object" ? value.season : "";

    const handleCropChange = (crop: string) => {
        if (crop === "unknown") {
            onChange("unknown");
            return;
        }
        onChange({ crop, season: currentSeason });
    };

    const handleSeasonChange = (season: string) => {
        onChange({ crop: currentCrop, season });
    };

    return (
        <div className="space-y-6">
            <div className="space-y-2">
                <label className="font-heading text-sm font-bold uppercase tracking-wide">
                    {locale === "ar" ? "المحصول" : "Crop"}
                </label>
                <div
                    className="grid gap-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
                    role="radiogroup"
                    aria-label={locale === "ar" ? "اختر المحصول" : "Select crop"}
                >
                    {CROP_OPTIONS.map((opt) => (
                        <OptionTile
                            key={opt.value}
                            option={opt}
                            locale={locale}
                            isSelected={currentCrop === opt.value}
                            onSelect={() => handleCropChange(opt.value)}
                        />
                    ))}
                </div>
            </div>

            <div className="space-y-2">
                <label className="font-heading text-sm font-bold uppercase tracking-wide">
                    {locale === "ar" ? "الموسم" : "Season"}
                </label>
                <p className="text-sm opacity-70">
                    {locale === "ar"
                        ? "الشتاء تقريباً من تشرين الثاني إلى أبريل، والصيف من مايو إلى أكتوبر"
                        : "Winter ≈ Nov–Apr, Summer ≈ May–Oct"}
                </p>
                <div
                    className="grid gap-3 sm:grid-cols-2"
                    role="radiogroup"
                    aria-label={locale === "ar" ? "اختر الموسم" : "Select season"}
                >
                    {SEASON_OPTIONS.map((opt) => (
                        <OptionTile
                            key={opt.value}
                            option={opt}
                            locale={locale}
                            isSelected={currentSeason === opt.value}
                            onSelect={() => handleSeasonChange(opt.value)}
                        />
                    ))}
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