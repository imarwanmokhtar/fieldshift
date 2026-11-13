import type { Metadata } from "next";
import { connection } from "next/server";
import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { getDictionary, isLocale, type Locale } from "@/lib/i18n";
import { BrutalButton } from "@/components/brutal-button";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const dict = getDictionary(locale);
  return { title: dict.dashboard.title };
}

export default async function DashboardPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  await connection();

  const { locale: raw } = await params;
  const locale = (isLocale(raw) ? raw : "ar") as Locale;
  const dict = getDictionary(locale);

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const { data: profile } = await supabase
    .from("field_profiles")
    .select("*")
    .eq("user_id", user!.id)
    .single();

  const isCompleted = profile?.status === "completed";

  return (
    <div className="mx-auto max-w-6xl px-6 py-12 md:py-20">
      <h1 className="font-heading text-4xl font-bold uppercase tracking-tight md:text-5xl">
        {dict.dashboard.welcome}
        {user?.email ? (
          <span className="block break-all text-green-dark">{user.email}</span>
        ) : null}
      </h1>

      {isCompleted ? (
        <div className="mt-10 border-[3px] border-ink bg-green-light p-8 text-base shadow-brutal-lg md:p-12 md:text-lg">
          <p className="font-heading text-xl font-bold uppercase md:text-2xl">
            {locale === "ar" ? "إعداد المزرعة مكتمل" : "Setup complete"}
          </p>
          <div className="mt-4 space-y-2">
            {profile.answers?.fieldSize && (
              <p>
                <span className="font-bold">
                  {locale === "ar" ? "مساحة الحقل: " : "Field size: "}
                </span>
                {typeof profile.answers.fieldSize === "object" &&
                "value" in (profile.answers.fieldSize as Record<string, unknown>)
                  ? `${(profile.answers.fieldSize as { value: number; unit: string }).value} ${(profile.answers.fieldSize as { value: number; unit: string }).unit}`
                  : String(profile.answers.fieldSize)}
              </p>
            )}
            {profile.answers?.lastCrop && (
              <p>
                <span className="font-bold">
                  {locale === "ar" ? "آخر محصول: " : "Last crop: "}
                </span>
                {String(profile.answers.lastCrop)}
              </p>
            )}
            {profile.answers?.topPriority && (
              <p>
                <span className="font-bold">
                  {locale === "ar" ? "الأولوية: " : "Top priority: "}
                </span>
                {Array.isArray(profile.answers.topPriority)
                  ? (profile.answers.topPriority as string[])[0]
                  : String(profile.answers.topPriority)}
              </p>
            )}
          </div>
        </div>
      ) : (
        <div className="mt-10 border-[3px] border-ink bg-green-light p-8 text-base shadow-brutal-lg md:p-12 md:text-lg">
          <p className="font-heading text-xl font-bold uppercase md:text-2xl">
            {locale === "ar"
              ? "أكمل إعداد مزرعتك"
              : "Finish your farm setup"}
          </p>
          <p className="mt-3 max-w-2xl">
            {locale === "ar"
              ? "أجب على بعض الأسئلة حول حقلك حتى نتمكن من تقديم توصيات مخصصة لتدوير المحاصيل."
              : "Answer a few questions about your field so we can provide personalized crop rotation recommendations."}
          </p>
          <div className="mt-6">
            <BrutalButton href={`/${locale}/onboarding`} variant="dark">
              {locale === "ar" ? "ابدأ الإعداد" : "Start setup"}
            </BrutalButton>
          </div>
        </div>
      )}
    </div>
  );
}
