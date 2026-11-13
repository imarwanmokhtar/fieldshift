"use client";

import { cn } from "@/lib/utils";
import type { Locale } from "@/lib/i18n";
import type { QuestionConfig } from "@/lib/onboarding/questions";

interface TextInputProps {
    question: QuestionConfig;
    locale: Locale;
    value: string | undefined;
    onChange: (value: string | "unknown") => void;
    allowUnknown: boolean;
    error?: string;
    placeholder?: string;
}

export function TextInput({
    question,
    locale,
    value,
    onChange,
    allowUnknown,
    error,
    placeholder,
}: TextInputProps) {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        onChange(e.target.value || "unknown");
    };

    return (
        <div className="space-y-3">
            <input
                type="text"
                value={value === "unknown" ? "" : value ?? ""}
                onChange={handleChange}
                placeholder={placeholder ?? (locale === "ar" ? "اكتب هنا..." : "Type here...")}
                className={cn(
                    "w-full h-14 border-[3px] border-ink bg-paper px-4",
                    "font-heading text-base font-bold",
                    "shadow-brutal-sm",
                    "focus:outline-none focus-visible:ring-4 focus-visible:ring-ink",
                    locale === "ar" ? "text-right" : "text-left"
                )}
                aria-invalid={!!error}
            />
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