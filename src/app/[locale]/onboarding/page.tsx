import { connection } from "next/server";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { isLocale, type Locale } from "@/lib/i18n";
import { OnboardingClient } from "./onboarding-client";

// Signed-in page that reads per-user data on the server. `instant = false` on
// the layout covers only the layout, so this page opts out too.
export const instant = false;

const UUID_RE = /^[0-9a-f-]{36}$/i;

/**
 * ?field=<id>  edit an existing field (also a finished one), starting from the first question
 * ?new=1       start a new, blank field
 * (neither)    resume an unfinished field, or go to the dashboard if every field is finished
 */
export default async function OnboardingPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ field?: string; new?: string }>;
}) {
  await connection();
  const { locale: raw } = await params;
  const query = await searchParams;
  const locale = (isLocale(raw) ? raw : "ar") as Locale;

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) redirect(`/${locale}/login`);

  if (query.new === "1") {
    return <OnboardingClient key="new" locale={locale} initialProfile={null} />;
  }

  if (query.field && UUID_RE.test(query.field)) {
    // RLS also limits this to the user's own rows.
    const { data: field } = await supabase
      .from("field_profiles")
      .select("*")
      .eq("id", query.field)
      .eq("user_id", user.id)
      .maybeSingle();
    if (!field) redirect(`/${locale}/dashboard`);
    // Reviewing a finished field: walk through every question again from the start.
    const initial = field.status === "completed" ? { ...field, current_step: 0 } : field;
    return <OnboardingClient key={field.id} locale={locale} initialProfile={initial} />;
  }

  const { data: fields } = await supabase
    .from("field_profiles")
    .select("*")
    .eq("user_id", user.id)
    .order("updated_at", { ascending: false });

  const unfinished = (fields ?? []).find((f) => f.status !== "completed");
  if (unfinished) return <OnboardingClient key={unfinished.id} locale={locale} initialProfile={unfinished} />;
  if (fields && fields.length > 0) redirect(`/${locale}/dashboard`);

  return <OnboardingClient key="new" locale={locale} initialProfile={null} />;
}
