import { connection } from "next/server";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { isLocale, type Locale } from "@/lib/i18n";
import { OnboardingClient } from "./onboarding-client";

// Signed-in page that reads per-user data on the server. `instant = false` on
// the layout covers only the layout, so this page opts out too.
export const instant = false;

export default async function OnboardingPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  await connection();
  const { locale: raw } = await params;
  const locale = (isLocale(raw) ? raw : "ar") as Locale;

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) redirect(`/${locale}/login`);

  const { data: profile } = await supabase
    .from("field_profiles")
    .select("*")
    .eq("user_id", user.id)
    .single();

  if (profile?.status === "completed") redirect(`/${locale}/dashboard`);

  return <OnboardingClient locale={locale} initialProfile={profile} />;
}
