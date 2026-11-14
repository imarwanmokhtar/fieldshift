import { Suspense } from "react";
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

// The analysis row is per-user, request-time data, so it streams in behind a
// Suspense boundary. `instant = false` on the dashboard layout opts out only
// that layout, not this nested page, so this page opts out too.
export const instant = false;

export default function ResultsPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  return (
    <Suspense fallback={<ResultsSkeleton />}>
      <ResultsContent params={params} />
    </Suspense>
  );
}

function ResultsSkeleton() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 md:px-6 md:py-16" aria-busy="true">
      <div className="h-10 w-2/3 border-[3px] border-ink bg-paper shadow-brutal animate-pulse" />
      <div className="mt-8 h-40 w-full border-[3px] border-ink bg-paper shadow-brutal animate-pulse" />
    </div>
  );
}

async function ResultsContent({
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
    .select("id,status,stage,lang,result,narrative,error,created_at,updated_at,field_id")
    .eq("id", id)
    .maybeSingle();
  if (!data) notFound();

  return <ResultsClient locale={locale} initial={data as AnalysisRow} />;
}
