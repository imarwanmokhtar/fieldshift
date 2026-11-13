import Link from "next/link";
import { LanguageSwitcher } from "@/components/language-switcher";
import type { Dictionary, Locale } from "@/lib/i18n";

/**
 * Shared brutalist frame for the /login and /signup pages.
 * Works down to 360px width.
 */
export function AuthShell({
  title,
  subtitle,
  locale,
  dict,
  children,
}: {
  title: string;
  subtitle: string;
  locale: Locale;
  dict: Dictionary;
  children: React.ReactNode;
}) {
  return (
    <main className="flex min-h-screen flex-col bg-green-light">
      <header className="border-b-4 border-ink">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-6 py-5">
          <Link
            href={`/${locale}`}
            className="font-heading text-xl font-bold uppercase tracking-tight hover:bg-ink hover:text-paper"
          >
            Field Shift
          </Link>
          <div className="flex items-center gap-3">
            <LanguageSwitcher current={locale} />
            <span className="hidden font-heading text-xs font-bold uppercase tracking-widest sm:inline">
              NASA Space Apps 2026
            </span>
          </div>
        </div>
      </header>

      <div className="flex flex-1 items-start justify-center px-6 py-10 md:items-center md:py-16">
        <div className="w-full max-w-md border-[3px] border-ink bg-paper p-6 shadow-brutal-lg md:p-10">
          <h1 className="font-heading text-3xl font-bold uppercase tracking-tight">
            {title}
          </h1>
          <p className="mt-2 mb-8 text-base">{subtitle}</p>
          {children}
        </div>
      </div>
    </main>
  );
}
