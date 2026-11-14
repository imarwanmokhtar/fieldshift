"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { BrutalButton } from "@/components/brutal-button";
import type { Locale } from "@/lib/i18n";
import { getResultsStrings } from "@/lib/results/strings";
import { startAnalysis } from "./start-analysis";

/**
 * "New analysis": first asks whether to update the farm data (walk through the form
 * again) or run straight away with the data already saved for this field.
 * Uses the native <dialog> element, so focus, Esc-to-close and the backdrop are built in.
 */
export function NewAnalysisButton({
  locale,
  fieldId,
  label,
  variant = "paper",
}: {
  locale: Locale;
  fieldId: string;
  label: string;
  variant?: "primary" | "dark" | "paper";
}) {
  const router = useRouter();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [busy, setBusy] = useState(false);
  const t = getResultsStrings(locale);
  const ar = locale === "ar";

  async function runNow() {
    setBusy(true);
    try {
      const id = await startAnalysis(locale, fieldId);
      router.push(`/${locale}/dashboard/results/${id}`);
    } catch (err) {
      toast.error(`${t.startError} (${err instanceof Error ? err.message : "unknown"})`);
      setBusy(false);
    }
  }

  function updateFirst() {
    dialogRef.current?.close();
    router.push(`/${locale}/onboarding?field=${fieldId}`);
  }

  return (
    <>
      <BrutalButton variant={variant} onClick={() => dialogRef.current?.showModal()} disabled={busy}>
        {busy ? t.retrying : label}
      </BrutalButton>

      <dialog
        ref={dialogRef}
        dir={ar ? "rtl" : "ltr"}
        aria-labelledby="new-analysis-title"
        className="m-auto w-[min(92vw,34rem)] border-[3px] border-ink bg-paper p-0 text-ink shadow-brutal-lg backdrop:bg-ink/60"
        onClick={(e) => {
          if (e.target === dialogRef.current) dialogRef.current?.close(); // click on the backdrop
        }}
      >
        <div className="p-6 md:p-8">
          <h2 id="new-analysis-title" className="font-heading text-2xl font-bold uppercase">
            {ar ? "تحليل جديد" : "New analysis"}
          </h2>
          <p className="mt-3">
            {ar
              ? "هل تغيّر شيء في حقلك منذ آخر مرة (المحاصيل، المياه، التربة، الأولويات)؟"
              : "Has anything changed on your field since last time (crops, water, soil, priorities)?"}
          </p>

          <div className="mt-6 grid gap-3">
            <button
              type="button"
              onClick={runNow}
              disabled={busy}
              autoFocus
              className="border-[3px] border-ink bg-green-dark p-4 text-start text-paper shadow-brutal outline-none focus-visible:outline-solid focus-visible:outline-4 focus-visible:outline-offset-4 focus-visible:outline-ink disabled:opacity-60"
            >
              <span className="block font-heading text-lg font-bold">
                {busy ? t.retrying : ar ? "شغّل التحليل بالبيانات المحفوظة" : "Run with my saved data"}
              </span>
              <span className="mt-1 block text-sm opacity-90">
                {ar ? "لا شيء تغيّر: حلّل الحقل بإجاباتك الحالية." : "Nothing changed: analyse the field with your current answers."}
              </span>
            </button>
            <button
              type="button"
              onClick={updateFirst}
              disabled={busy}
              className="border-[3px] border-ink bg-green-light p-4 text-start shadow-brutal outline-none focus-visible:outline-solid focus-visible:outline-4 focus-visible:outline-offset-4 focus-visible:outline-ink disabled:opacity-60"
            >
              <span className="block font-heading text-lg font-bold">
                {ar ? "حدّث بيانات المزرعة أولاً" : "Update my farm data first"}
              </span>
              <span className="mt-1 block text-sm">
                {ar
                  ? "راجع الأسئلة مرة أخرى وعدّل ما تغيّر، ثم يبدأ التحليل."
                  : "Go through the questions again and change what's new; the analysis starts when you finish."}
              </span>
            </button>
          </div>

          <div className="mt-5 text-center">
            <button
              type="button"
              onClick={() => dialogRef.current?.close()}
              className="font-bold underline underline-offset-4 hover:bg-ink hover:text-paper"
            >
              {ar ? "إلغاء" : "Cancel"}
            </button>
          </div>
        </div>
      </dialog>
    </>
  );
}
