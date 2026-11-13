import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { connection } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { isLocale, type Locale } from "@/lib/i18n";
import { getResultsStrings } from "@/lib/results/strings";
import type { AnalysisRow } from "@/lib/results/types";
import { ResultsClient } from "@/components/results/results-client";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = getResultsStrings((isLocale(locale) ? locale : "ar") as Locale);
  return { title: `${t.pageTitle} — Field Shift` };
}

export default async function ResultsPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  await connection();
  const { locale: raw, id } = await params;
  const locale = (isLocale(raw) ? raw : "ar") as Locale;

  if (!/^[0-9a-f-]{36}$/i.test(id)) notFound();

  const supabase = await createClient();
  // RLS limits this to the signed-in user's own rows.
  const { data } = await supabase
    .from("analyses")
    .select("id,status,stage,lang,result,narrative,error,created_at")
    .eq("id", id)
    .maybeSingle();
  if (!data) notFound();

  return <ResultsClient locale={locale} initial={data as AnalysisRow} />;
}
