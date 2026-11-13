"use client";

import dynamic from "next/dynamic";
import { useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import type { Locale } from "@/lib/i18n";
import type { QuestionConfig } from "@/lib/onboarding/questions";
import { BrutalButton } from "@/components/brutal-button";

// Dynamically import Leaflet to avoid SSR issues
const MapPinClient = dynamic(
    () => import("./MapPinClient").then((mod) => mod.MapPinClient),
    { ssr: false, loading: () => <MapPinSkeleton /> }
);

function MapPinSkeleton() {
    return (
        <div className="w-full h-[300px] border-[3px] border-ink bg-paper shadow-brutal animate-pulse" />
    );
}

interface MapPinProps {
    question: QuestionConfig;
    locale: Locale;
    value: { lat: number; lng: number } | "unknown" | undefined;
    onChange: (value: { lat: number; lng: number } | "unknown") => void;
    allowUnknown: boolean;
    error?: string;
}

export function MapPin({
    question,
    locale,
    value,
    onChange,
    allowUnknown,
    error,
}: MapPinProps) {
    return (
        <MapPinClient
            question={question}
            locale={locale}
            value={value}
            onChange={onChange}
            allowUnknown={allowUnknown}
            error={error}
        />
    );
}