"use client";

import { useRouter } from "next/navigation";
import { OnboardingWizard } from "@/components/onboarding/OnboardingWizard";
import type { Locale } from "@/lib/i18n";
import type { FieldProfile } from "@/lib/onboarding/types";

interface OnboardingClientProps {
  locale: Locale;
  initialProfile: FieldProfile | null;
}

export function OnboardingClient({
  locale,
  initialProfile,
}: OnboardingClientProps) {
  const router = useRouter();

  return (
    <OnboardingWizard
      locale={locale}
      onComplete={() => {
        router.push(`/${locale}/dashboard`);
        router.refresh();
      }}
    />
  );
}
