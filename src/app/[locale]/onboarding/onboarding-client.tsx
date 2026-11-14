"use client";

import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { OnboardingWizard } from "@/components/onboarding/OnboardingWizard";
import { startAnalysis } from "@/components/results/start-analysis";
import { getResultsStrings } from "@/lib/results/strings";
import type { Locale } from "@/lib/i18n";
import type { FieldProfile } from "@/lib/onboarding/types";

interface OnboardingClientProps {
  locale: Locale;
  initialProfile: FieldProfile | null;
}

export function OnboardingClient({ locale, initialProfile }: OnboardingClientProps) {
  const router = useRouter();

  return (
    <OnboardingWizard
      locale={locale}
      initialProfile={initialProfile}
      onComplete={async (fieldId) => {
        // Answers are saved: start the analysis of this field and go straight to the results page.
        try {
          const id = await startAnalysis(locale, fieldId);
          router.push(`/${locale}/dashboard/results/${id}`);
        } catch (err) {
          toast.error(`${getResultsStrings(locale).startError} (${err instanceof Error ? err.message : "unknown"})`);
          router.push(`/${locale}/dashboard?field=${fieldId}`);
        }
        router.refresh();
      }}
    />
  );
}
