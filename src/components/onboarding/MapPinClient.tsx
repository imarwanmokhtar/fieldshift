"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { MapContainer, TileLayer, Marker, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { cn } from "@/lib/utils";
import type { Locale } from "@/lib/i18n";
import type { QuestionConfig } from "@/lib/onboarding/questions";
import { BrutalButton } from "@/components/brutal-button";

// Fix Leaflet marker icon default
import L from "leaflet";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: markerIcon2x,
    iconUrl: markerIcon,
    shadowUrl: markerShadow,
});

const DEFAULT_CENTER: [number, number] = [31.0, 31.4]; // Dakahlia, Egypt
const DEFAULT_ZOOM = 13;

function MapClickHandler({ onClick }: { onClick: (e: L.LeafletMouseEvent) => void }) {
    useMapEvents({ click: onClick });
    return null;
}

interface MapPinClientProps {
    question: QuestionConfig;
    locale: Locale;
    value: { lat: number; lng: number } | "unknown" | undefined;
    onChange: (value: { lat: number; lng: number } | "unknown") => void;
    allowUnknown: boolean;
    error?: string;
}

function MapComponent({
    locale,
    value,
    onChange,
    allowUnknown,
    error,
}: MapPinClientProps) {
    const mapRef = useRef<L.Map | null>(null);
    const markerRef = useRef<L.Marker | null>(null);
    const [position, setPosition] = useState<{ lat: number; lng: number } | null>(
        value !== "unknown" && typeof value === "object" ? value : null
    );
    const [locating, setLocating] = useState(false);

    // Update marker when position changes
    useEffect(() => {
        if (markerRef.current && position) {
            markerRef.current.setLatLng([position.lat, position.lng]);
        }
    }, [position]);

    const handleMapClick = useCallback((e: L.LeafletMouseEvent) => {
        const { lat, lng } = e.latlng;
        const rounded = { lat: Math.round(lat * 100000) / 100000, lng: Math.round(lng * 100000) / 100000 };
        setPosition(rounded);
        onChange(rounded);
    }, [onChange]);

    const handleUseLocation = useCallback(async () => {
        if (!navigator.geolocation) {
            alert(locale === "ar" ? "الموقع الجغرافي غير مدعوم" : "Geolocation not supported");
            return;
        }
        setLocating(true);
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const rounded = {
                    lat: Math.round(pos.coords.latitude * 100000) / 100000,
                    lng: Math.round(pos.coords.longitude * 100000) / 100000,
                };
                setPosition(rounded);
                onChange(rounded);
                if (mapRef.current) {
                    mapRef.current.setView([rounded.lat, rounded.lng], 15);
                }
                setLocating(false);
            },
            (err) => {
                alert(locale === "ar" ? "تعذر الحصول على الموقع" : "Could not get location");
                setLocating(false);
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    }, [locale, onChange]);

    const handleManualEntry = useCallback(() => {
        const latStr = prompt(locale === "ar" ? "خط العرض (مثال: 31.12345):" : "Latitude (e.g., 31.12345):");
        const lngStr = prompt(locale === "ar" ? "خط الطول (مثال: 31.54321):" : "Longitude (e.g., 31.54321):");
        if (latStr && lngStr) {
            const lat = parseFloat(latStr);
            const lng = parseFloat(lngStr);
            if (!isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
                const rounded = { lat: Math.round(lat * 100000) / 100000, lng: Math.round(lng * 100000) / 100000 };
                setPosition(rounded);
                onChange(rounded);
                if (mapRef.current) {
                    mapRef.current.setView([rounded.lat, rounded.lng], 15);
                }
            } else {
                alert(locale === "ar" ? "إحداثيات غير صالحة" : "Invalid coordinates");
            }
        }
    }, [locale, onChange]);

    const hasPosition = position !== null;

    return (
        <div className="space-y-4">
            <MapContainer
                ref={mapRef}
                center={position ?? DEFAULT_CENTER}
                zoom={position ? 15 : DEFAULT_ZOOM}
                scrollWheelZoom={true}
                className={cn(
                    "w-full h-[350px] border-[3px] border-ink shadow-brutal",
                    "leaflet-container"
                )}
                attributionControl={false}
            >
                <MapClickHandler onClick={handleMapClick} />
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                {position && (
                    <Marker
                        ref={markerRef}
                        position={[position.lat, position.lng]}
                        draggable={true}
                        eventHandlers={{
                            dragend: (e) => {
                                const { lat, lng } = (e.target as L.Marker).getLatLng();
                                const rounded = { lat: Math.round(lat * 100000) / 100000, lng: Math.round(lng * 100000) / 100000 };
                                setPosition(rounded);
                                onChange(rounded);
                            },
                        }}
                    />
                )}
            </MapContainer>

            <div className="space-y-2" role="group" aria-label={locale === "ar" ? "أدوات الموقع" : "Location tools"}>
                <div className="flex gap-2 flex-wrap">
                    <BrutalButton
                        variant="dark"
                        onClick={handleUseLocation}
                        disabled={locating}
                        className="flex-1 min-w-[140px]"
                    >
                        {locating
                            ? locale === "ar"
                                ? "جاري التحديد..."
                                : "Locating..."
                            : locale === "ar"
                                ? "استخدم موقعي"
                                : "Use my location"}
                    </BrutalButton>
                    <BrutalButton
                        variant="paper"
                        onClick={handleManualEntry}
                        className="flex-1 min-w-[140px]"
                    >
                        {locale === "ar" ? "إحداثيات يدوية" : "Manual coords"}
                    </BrutalButton>
                </div>
                {hasPosition && (
                    <p className="font-mono text-sm text-center">
                        {locale === "ar" ? "الإحداثيات: " : "Coords: "}
                        {position!.lat.toFixed(5)}, {position!.lng.toFixed(5)}
                    </p>
                )}
            </div>

            {allowUnknown && !hasPosition && (
                <BrutalButton
                    variant="paper"
                    onClick={() => onChange("unknown")}
                    className="w-full"
                >
                    {locale === "ar" ? "لا أعرف / تخطي" : "Don't know / Skip"}
                </BrutalButton>
            )}

            {error && (
                <p role="alert" className="text-red-600 text-sm text-center">
                    {error}
                </p>
            )}
        </div>
    );
}

export { MapComponent as MapPinClient };