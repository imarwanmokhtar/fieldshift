import type { Locale } from "@/lib/i18n";

/** Asks our own server route to start an analysis of one field. Returns the analysis id. */
export async function startAnalysis(lang: Locale, fieldId?: string | null): Promise<string> {
  const res = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lang, field_id: fieldId ?? undefined }),
  });
  const data = (await res.json().catch(() => ({}))) as { id?: string; error?: string };
  if (!res.ok || !data.id) throw new Error(data.error ?? `HTTP ${res.status}`);
  return data.id;
}
