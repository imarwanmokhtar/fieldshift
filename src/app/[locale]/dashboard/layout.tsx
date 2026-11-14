import { redirect } from "next/navigation";
import { connection } from "next/server";
import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { getDictionary, isLocale, type Locale } from "@/lib/i18n";
import { LanguageSwitcher } from "@/components/language-switcher";
import { LogoutButton } from "@/components/dashboard/logout-button";
import { BrandMark } from "@/components/brand-mark";

// Auth protection must block on the server; this segment is not prerenderable.
export const instant = false;

export default async function DashboardLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  // Stop the prerender attempt here: everything below (including the session
  // read, which internally compares token expiry against Date.now()) runs at
  // request time only.
  await connection();

  const { locale: raw } = await params;
  const locale = (isLocale(raw) ? raw : "ar") as Locale;
  const dict = getDictionary(locale);

  const supabase = await createClient();

  // Server-side session check with getUser() — not getSession().
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
            className="inline-flex items-center gap-3 font-heading text-xl font-bold uppercase tracking-tight hover:bg-ink hover:text-paper"
          >
            <BrandMark />
          </Link>
          <div className="flex items-center gap-3">
            <LanguageSwitcher current={locale} />
            <LogoutButton locale={locale} label={dict.dashboard.logout} loadingLabel={dict.dashboard.logoutLoading} />
          </div>
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}
