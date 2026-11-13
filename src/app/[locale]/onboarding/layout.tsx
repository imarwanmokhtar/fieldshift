import { redirect } from "next/navigation";
import { connection } from "next/server";
import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { isLocale, type Locale } from "@/lib/i18n";
import { LanguageSwitcher } from "@/components/language-switcher";

// Auth protection must block on the server; this segment is not prerenderable.
export const instant = false;

export default async function OnboardingLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  await connection();

  const { locale: raw } = await params;
  const locale = (isLocale(raw) ? raw : "ar") as Locale;

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect(`/${locale}/login`);
  }

  return (
    <div className="min-h-screen bg-paper">
      <header className="border-b-4 border-ink bg-green-light">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-6 py-5">
          <Link
            href={`/${locale}`}
            className="font-heading text-xl font-bold uppercase tracking-tight hover:bg-ink hover:text-paper"
          >
            Field Shift
          </Link>
          <LanguageSwitcher current={locale} />
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}
