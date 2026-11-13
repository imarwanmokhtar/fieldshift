import Link from "next/link";
import { BrutalButton } from "@/components/brutal-button";
import { LanguageSwitcher } from "@/components/language-switcher";
import type { Dictionary, Locale } from "@/lib/i18n";

export function Hero({ dict, locale }: { dict: Dictionary; locale: Locale }) {
  return (
    <header className="border-b-4 border-ink bg-green-light">
      <div className="mx-auto max-w-6xl px-6">
        <nav className="flex items-center justify-between border-b-4 border-ink py-5">
          <Link
            href={`/${locale}`}
            className="font-heading text-xl font-bold uppercase tracking-tight"
          >
            Field Shift
          </Link>
          <div className="flex items-center gap-3">
            <LanguageSwitcher current={locale} />
            <Link
              href={`/${locale}/login`}
              className="font-heading text-sm font-bold uppercase tracking-wide underline decoration-[3px] underline-offset-4 hover:bg-ink hover:text-paper"
            >
              {dict.nav.login}
            </Link>
          </div>
        </nav>

        <div className="py-16 md:py-24">
          <p className="mb-6 inline-block border-2 border-ink bg-paper px-3 py-1 font-heading text-xs font-bold uppercase tracking-widest shadow-brutal-xs">
            {dict.hero.tag}
          </p>
          <h1 className="max-w-4xl font-heading text-4xl font-bold uppercase leading-[1.1] tracking-tight sm:text-6xl md:text-7xl">
            {dict.hero.title}
          </h1>
          <p className="mt-6 max-w-2xl text-lg md:text-xl">{dict.hero.subtitle}</p>
          <div className="mt-10 flex flex-wrap items-center gap-6">
            <BrutalButton href={`/${locale}/signup`}>{dict.hero.getStarted}</BrutalButton>
            <Link
              href={`/${locale}/login`}
              className="font-heading text-base font-bold uppercase tracking-wide underline decoration-[3px] underline-offset-4 hover:bg-ink hover:text-paper"
            >
              {dict.hero.login}
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}
