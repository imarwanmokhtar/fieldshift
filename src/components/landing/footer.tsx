import Link from "next/link";
import type { Dictionary, Locale } from "@/lib/i18n";

export function Footer({ dict, locale }: { dict: Dictionary; locale: Locale }) {
  return (
    <footer className="bg-ink text-paper">
      <div className="mx-auto max-w-6xl px-6 py-12">
        <p className="font-heading text-2xl font-bold uppercase">{dict.footer.name}</p>
        <p className="mt-3 text-sm">{dict.footer.line}</p>
        <p className="mt-6 max-w-2xl text-sm opacity-80">{dict.footer.note}</p>
        <div className="mt-8 flex gap-6 border-t-2 border-paper pt-6 text-sm">
          <Link
            href={`/${locale}/login`}
            className="uppercase underline underline-offset-4 hover:text-green-light"
          >
            {dict.footer.login}
          </Link>
          <Link
            href={`/${locale}/signup`}
            className="uppercase underline underline-offset-4 hover:text-green-light"
          >
            {dict.footer.signup}
          </Link>
        </div>
      </div>
    </footer>
  );
}
