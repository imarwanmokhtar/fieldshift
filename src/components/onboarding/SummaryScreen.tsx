"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";
import type { Locale } from "@/lib/i18n";
import {
    ONBOARDING_QUESTIONS,
    QUESTIONS_BY_SECTION,
    getLocalizedString,
    getLocalizedOption,
} from "@/lib/onboarding/questions";
import { BrutalButton } from "@/components/brutal-button";

interface SummaryScreenProps {
    locale: Locale;
    answers: Record<string, unknown>;
    onEdit: (questionId: string) => void;
    onFinish: () => void;
    /** Saving and starting the analysis: the button shows a spinner and is disabled. */
    busy?: boolean;
    error?: string;
}

function SpinningDots() {
    return (
        <span className="inline-flex items-center gap-1" aria-hidden>
            {[0, 150, 300].map((delay) => (
                <span
                    key={delay}
                    className="size-2 rounded-full bg-current animate-bounce motion-reduce:animate-none"
                    style={{ animationDelay: `${delay}ms` }}
                />
            ))}
        </span>
    );
}

function formatAnswer(
    question: (typeof ONBOARDING_QUESTIONS)[number],
    value: unknown,
    locale: Locale
): string {
    if (value === "unknown" || value === undefined || value === null) {
        return locale === "ar" ? "تم التخطي" : "Skipped";
    }

    switch (question.type) {
        case "mapPin":
            if (typeof value === "object" && value !== null && "lat" in value) {
                return `${(value as any).lat.toFixed(5)}, ${(value as any).lng.toFixed(5)}`;
            }
            return locale === "ar" ? "غير محدد" : "Not set";

        case "numberWithUnit":
            if (typeof value === "object" && value !== null && "value" in value) {
                const v = value as any;
                return `${v.value} ${v.unit} (≈ ${v.hectares.toFixed(3)} ha)`;
            }
            return locale === "ar" ? "غير محدد" : "Not set";

        case "twoNumbers":
            if (typeof value === "object" && value !== null && "summer" in value) {
                const v = value as any;
                return `${locale === "ar" ? "صيف" : "Summer"}: ${v.summer}, ${locale === "ar" ? "شتاء" : "Winter"}: ${v.winter}`;
            }
            return locale === "ar" ? "غير محدد" : "Not set";

        case "cropAndSeason":
            if (typeof value === "object" && value !== null && "crop" in value) {
                const v = value as any;
                const cropOpt = question.options?.find((o) => o.value === v.crop);
                const seasonOpt = question.options?.find((o) => o.value === v.season);
                const typed = v.crop === "other" && typeof (v as { other?: unknown }).other === "string" ? ((v as { other?: string }).other ?? "").trim() : "";
                const cropText = typed || (cropOpt ? getLocalizedOption(cropOpt, locale) : v.crop);
                return `${cropText} — ${seasonOpt ? getLocalizedOption(seasonOpt, locale) : v.season}`;
            }
            return locale === "ar" ? "غير محدد" : "Not set";

        case "rank":
            if (Array.isArray(value)) {
                return value
                    .map((v, i) => {
                        const opt = question.options?.find((o) => o.value === v);
                        return `${i + 1}. ${opt ? getLocalizedOption(opt, locale) : v}`;
                    })
                    .join(" › ");
            }
            return locale === "ar" ? "غير محدد" : "Not set";

        case "multi":
            if (Array.isArray(value)) {
                if (value.includes("none")) {
                    return locale === "ar" ? "لا شيء" : "None";
                }
                return value
                    .map((v) => {
                        const opt = question.options?.find((o) => o.value === v);
                        return opt ? getLocalizedOption(opt, locale) : v;
                    })
                    .join(", ");
            }
            return locale === "ar" ? "غير محدد" : "Not set";

        case "soilTest":
            if (typeof value === "object" && value !== null && "hasTest" in value) {
                const v = value as any;
                if (!v.hasTest) return locale === "ar" ? "لا" : "No";
                const details = [];
                if (v.ph !== undefined) details.push(`pH: ${v.ph}`);
                if (v.ec !== undefined) details.push(`EC: ${v.ec}`);
                if (v.organicMatter !== undefined) details.push(`OM: ${v.organicMatter}%`);
                if (v.n !== undefined) details.push(`N: ${v.n}`);
                if (v.p !== undefined) details.push(`P: ${v.p}`);
                if (v.k !== undefined) details.push(`K: ${v.k}`);
                return details.length ? details.join(", ") : (locale === "ar" ? "نعم (بدون تفاصيل)" : "Yes (no details)");
            }
            return locale === "ar" ? "لا" : "No";

        case "single":
            if (question.options) {
                const opt = question.options.find((o) => o.value === value);
                return opt ? getLocalizedOption(opt, locale) : String(value);
            }
            return String(value);

        default:
            return String(value);
    }
}

export function SummaryScreen({
    locale,
    answers,
    onEdit,
    onFinish,
    busy = false,
    error,
}: SummaryScreenProps) {
    return (
        <div className="w-full max-w-3xl mx-auto space-y-8">
            <header className="border-b-4 border-ink pb-6">
                <h1 className="font-heading text-3xl font-bold uppercase tracking-tight">
                    {locale === "ar" ? "ملخص الإجابات" : "Answer Summary"}
                </h1>
                <p className="mt-2 text-base opacity-70">
                    {locale === "ar"
                        ? "راجع إجاباتك، ثم احفظ وانتقل إلى لوحة التحكم"
                        : "Review your answers, then save and go to the dashboard"}
                </p>
            </header>

            <section className="space-y-6">
                {Object.entries(QUESTIONS_BY_SECTION).map(([section, questions]) => (
                    <div key={section} className="border-[3px] border-ink bg-green-light p-6 shadow-brutal">
                        <h2 className="font-heading text-xl font-bold uppercase mb-4">
                            {section}
                        </h2>
                        <dl className="space-y-3">
                            {questions.map((q) => {
                                const value = answers[q.id];
                                const formatted = formatAnswer(q, value, locale);
                                const isUnknown = value === "unknown" || value === undefined || value === null;
                                return (
                                    <div
                                        key={q.id}
                                        className={cn(
                                            "flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 p-3 border-2 border-ink bg-paper shadow-brutal-xs",
                                            isUnknown && "opacity-60"
                                        )}
                                    >
                                        <dt className="font-heading text-base font-bold flex-1">
                                            {getLocalizedString(q.title, locale)}
                                        </dt>
                                        <dd className={cn(
                                            "font-mono text-sm whitespace-pre-wrap flex-1",
                                            locale === "ar" ? "text-right" : "text-left",
                                            isUnknown ? "opacity-50" : ""
                                        )}>
                                            {formatted}
                                        </dd>
                                        <button
                                            type="button"
                                            onClick={() => onEdit(q.id)}
                                            className={cn(
                                                "self-start border-2 border-ink bg-green-light px-3 py-1",
                                                "font-heading text-xs font-bold uppercase tracking-wide",
                                                "shadow-brutal-xs hover:bg-ink hover:text-paper",
                                                "focus:outline-none focus-visible:ring-4 focus-visible:ring-ink"
                                            )}
                                            aria-label={
                                                locale === "ar"
                                                    ? `تعديل: ${getLocalizedString(q.title, locale)}`
                                                    : `Edit: ${getLocalizedString(q.title, locale)}`
                                            }
                                        >
                                            {locale === "ar" ? "تعديل" : "Edit"}
                                        </button>
                                    </div>
                                );
                            })}
                        </dl>
                    </div>
                ))}
            </section>

            <footer className="border-t-4 border-ink pt-6">
                {error && (
                    <p role="alert" className="mb-4 border-[3px] border-ink bg-paper p-3 font-bold text-red-700">
                        {locale === "ar" ? "تعذر الحفظ: " : "Could not save: "}
                        {error}
                    </p>
                )}
                <BrutalButton
                    variant="dark"
                    onClick={onFinish}
                    disabled={busy}
                    className="w-full"
                >
                    {busy ? (
                        <span className="inline-flex items-center gap-3" aria-live="polite">
                            <SpinningDots />
                            {locale === "ar" ? "جارٍ الحفظ…" : "Saving…"}
                        </span>
                    ) : locale === "ar" ? (
                        "حفظ وتشغيل التحليل"
                    ) : (
                        "Save and run the analysis"
                    )}
                </BrutalButton>
            </footer>
        </div>
    );
}