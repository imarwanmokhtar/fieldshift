import { connection } from "next/server";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { isLocale, type Locale } from "@/lib/i18n";
import { OnboardingClient } from "./onboarding-client";

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
