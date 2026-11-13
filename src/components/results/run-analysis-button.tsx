"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { BrutalButton } from "@/components/brutal-button";
import type { Locale } from "@/lib/i18n";
import { getResultsStrings } from "@/lib/results/strings";
import { startAnalysis } from "./start-analysis";

export function RunAnalysisButton({
  locale,
  label,
  variant = "dark",
}: {
  locale: Locale;
  label: string;
  variant?: "primary" | "dark" | "paper";
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const t = getResultsStrings(locale);

  async function run() {
    setBusy(true);
    try {
      const id = await startAnalysis(locale);
      router.push(`/${locale}/dashboard/results/${id}`);
    } catch (err) {
      toast.error(`${t.startError} (${err instanceof Error ? err.message : "unknown"})`);
      setBusy(false);
    }
  }

  return (
    <BrutalButton variant={variant} onClick={run} disabled={busy}>
      {busy ? t.retrying : label}
    </BrutalButton>
  );
}
