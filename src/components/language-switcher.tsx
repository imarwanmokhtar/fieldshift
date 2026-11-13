"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Locale } from "@/lib/i18n";

/**
 * Toggles the locale prefix of the current path: /ar/... ↔ /en/...
 * Shows the name of the *other* language.
 */
export function LanguageSwitcher({ current }: { current: Locale }) {
  const pathname = usePathname() || "";
  const other: Locale = current === "ar" ? "en" : "ar";
  const rest = pathname.replace(/^\/(ar|en)/, "") || "";
  const href = `/${other}${rest}`;

  return (
    <Link
      href={href}
      className="border-2 border-ink bg-paper px-3 py-1 font-heading text-xs font-bold uppercase shadow-brutal-xs hover:bg-ink hover:text-paper"
    >
      {current === "ar" ? "English" : "العربية"}
    </Link>
  );
}
