import type { Metadata } from "next";
import { connection } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { getDictionary, isLocale, type Locale } from "@/lib/i18n";
import { BrutalButton } from "@/components/brutal-button";
import { RunAnalysisButton } from "@/components/results/run-analysis-button";
import { NewAnalysisButton } from "@/components/results/new-analysis-button";
import { cn } from "@/lib/utils";
import { CROP_OPTIONS, getQuestionById, getLocalizedOption } from "@/lib/onboarding/questions";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const dict = getDictionary(locale);
  return { title: dict.dashboard.title };
}

const UNIT_LABELS: Record<string, { en: string; ar: string }> = {
  feddan: { en: "feddan", ar: "فدان" },
  kirat: { en: "kirat", ar: "قيراط" },
  hectare: { en: "hectare", ar: "هكتار" },
};

function optionLabel(questionId: string, value: unknown, locale: Locale): string | null {
  if (typeof value !== "string" || value === "unknown") return null;
  const opt = getQuestionById(questionId)?.options?.find((o) => o.value === value);
  return opt ? getLocalizedOption(opt, locale) : value;
}

// Signed-in page that reads per-user data on the server. `instant = false` on
// the layout covers only the layout, so this page opts out too.
export const instant = false;

function fieldName(answers: Record<string, unknown>, index: number, ar: boolean): string {
  const name = answers.field_name;
  if (typeof name === "string" && name.trim() && name !== "unknown") return name.trim();
  return ar ? `حقل ${index + 1}` : `Field ${index + 1}`;
}

export default async function DashboardPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ field?: string }>;
}) {
  await connection();

  const { locale: raw } = await params;
  const { field: requestedField } = await searchParams;
  const locale = (isLocale(raw) ? raw : "ar") as Locale;
  const dict = getDictionary(locale);
  const ar = locale === "ar";

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  // A user can have several fields. Numbering follows creation order; the selected field
  // comes from ?field=, otherwise the most recently updated one.
  const { data: fieldRows } = await supabase
    .from("field_profiles")
    .select("*")
    .eq("user_id", user!.id)
    .order("created_at", { ascending: true });
  const fields = fieldRows ?? [];
  const mostRecent = [...fields].sort((a, b) => Date.parse(b.updated_at) - Date.parse(a.updated_at))[0];
  const profile = fields.find((f) => f.id === requestedField) ?? mostRecent ?? null;

  const { data: latest } = profile
    ? await supabase
        .from("analyses")
        .select("id,status,created_at")
        .eq("field_id", profile.id)
        .order("created_at", { ascending: false })
        .limit(1)
        .maybeSingle()
    : { data: null };

  const isCompleted = profile?.status === "completed";
  const answers = (profile?.answers ?? {}) as Record<string, unknown>;

  // Summary values, read from the real question ids (area, last_crop, priorities).
  const area = answers.area as { value?: number; unit?: string } | undefined;
  const areaText =
    area && typeof area === "object" && area.value != null
      ? `${area.value} ${UNIT_LABELS[area.unit ?? ""]?.[locale] ?? area.unit ?? ""}`
      : null;
  const last = answers.last_crop as { crop?: string; season?: string } | undefined;
  const lastCropOpt = last?.crop ? CROP_OPTIONS.find((o) => o.value === last.crop) : undefined;
  const lastCropText = lastCropOpt ? getLocalizedOption(lastCropOpt, locale) : null;
  const priorities = Array.isArray(answers.priorities) ? (answers.priorities as string[]) : [];
  const topPriorityText = optionLabel("priorities", priorities[0], locale);

  const inProgress = latest && (latest.status === "pending" || latest.status === "running");

  return (
    <div className="mx-auto max-w-6xl px-6 py-12 md:py-20">
      <h1 className="font-heading text-4xl font-bold uppercase tracking-tight md:text-5xl">
        {dict.dashboard.welcome}
        {user?.email ? <span className="block break-all text-green-dark">{user.email}</span> : null}
      </h1>

      {fields.length > 0 && (
        <nav className="mt-10 flex flex-wrap items-center gap-3" aria-label={ar ? "حقولك" : "Your fields"}>
          {fields.map((f, i) => {
            const selected = f.id === profile?.id;
            return (
              <a
                key={f.id}
                href={`/${locale}/dashboard?field=${f.id}`}
                aria-current={selected ? "page" : undefined}
                className={cn(
                  "border-[3px] border-ink px-4 py-2 font-bold shadow-brutal-xs",
                  selected ? "bg-green-dark text-paper" : "bg-paper hover:bg-green-light",
                )}
              >
                {fieldName((f.answers ?? {}) as Record<string, unknown>, i, ar)}
                {f.status !== "completed" && (
                  <span className="ms-2 text-xs font-normal opacity-80">{ar ? "(غير مكتمل)" : "(unfinished)"}</span>
                )}
              </a>
            );
          })}
          <BrutalButton href={`/${locale}/onboarding?new=1`} variant="primary">
            {ar ? "+ اضف حقل جديد" : "+ Add new field"}
          </BrutalButton>
        </nav>
      )}

      {isCompleted ? (
        <div className="mt-10 grid gap-8 md:grid-cols-2">
          <div className="border-[3px] border-ink bg-green-light p-8 text-base shadow-brutal-lg md:p-10 md:text-lg">
            <p className="font-heading text-xl font-bold uppercase md:text-2xl">
              {ar ? "إعداد المزرعة مكتمل" : "Setup complete"}
            </p>
            <div className="mt-4 space-y-2">
              {areaText && (
                <p>
                  <span className="font-bold">{ar ? "مساحة الحقل: " : "Field size: "}</span>
                  {areaText}
                </p>
              )}
              {lastCropText && (
                <p>
                  <span className="font-bold">{ar ? "آخر محصول: " : "Last crop: "}</span>
                  {lastCropText}
                </p>
              )}
              {topPriorityText && (
                <p>
                  <span className="font-bold">{ar ? "الأولوية: " : "Top priority: "}</span>
                  {topPriorityText}
                </p>
              )}
            </div>
            <a
              href={`/${locale}/onboarding?field=${profile!.id}`}
              className="mt-6 inline-block font-bold underline underline-offset-4 hover:bg-ink hover:text-paper"
            >
              {ar ? "تعديل بيانات المزرعة" : "Edit farm data"}
            </a>
          </div>

          <div className="border-[3px] border-ink bg-paper p-8 text-base shadow-brutal-lg md:p-10 md:text-lg">
            <p className="font-heading text-xl font-bold uppercase md:text-2xl">
              {ar ? "تحليل الدورة الزراعية" : "Rotation analysis"}
            </p>
            <p className="mt-3">
              {latest?.status === "done"
                ? ar
                  ? "تحليلك جاهز. قارن الدورات الزراعية المقترحة لحقلك."
                  : "Your analysis is ready. Compare the suggested rotations for your field."
                : inProgress
                  ? ar
                    ? "جارٍ تحليل حقلك الآن."
                    : "Your field is being analysed now."
                  : ar
                    ? "شغّل التحليل لمقارنة 3 دورات زراعية على الأقل باستخدام بيانات ناسا."
                    : "Run the analysis to compare at least 3 crop rotations using NASA data."}
            </p>
            <div className="mt-6 flex flex-wrap gap-4">
              {latest && (latest.status === "done" || inProgress) ? (
                <>
                  <BrutalButton href={`/${locale}/dashboard/results/${latest.id}`} variant="dark">
                    {latest.status === "done"
                      ? ar ? "عرض تحليلي" : "View my analysis"
                      : ar ? "متابعة التقدم" : "See progress"}
                  </BrutalButton>
                  {latest.status === "done" && (
                    <NewAnalysisButton locale={locale} fieldId={profile!.id} variant="paper" label={ar ? "تحليل جديد" : "New analysis"} />
                  )}
                </>
              ) : (
                <RunAnalysisButton locale={locale} fieldId={profile!.id} label={ar ? "شغّل التحليل" : "Run analysis"} />
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="mt-10 border-[3px] border-ink bg-green-light p-8 text-base shadow-brutal-lg md:p-12 md:text-lg">
          <p className="font-heading text-xl font-bold uppercase md:text-2xl">
            {ar ? "أكمل إعداد مزرعتك" : "Finish your farm setup"}
          </p>
          <p className="mt-3 max-w-2xl">
            {ar
              ? "أجب على بعض الأسئلة حول حقلك حتى نتمكن من تقديم توصيات مخصصة لتدوير المحاصيل."
              : "Answer a few questions about your field so we can provide personalized crop rotation recommendations."}
          </p>
          <div className="mt-6">
            <BrutalButton href={profile ? `/${locale}/onboarding?field=${profile.id}` : `/${locale}/onboarding?new=1`} variant="dark">
              {profile ? (ar ? "أكمل الإعداد" : "Continue setup") : ar ? "ابدأ الإعداد" : "Start setup"}
            </BrutalButton>
          </div>
        </div>
      )}
    </div>
  );
}
