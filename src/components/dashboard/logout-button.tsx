"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { BrutalButton } from "@/components/brutal-button";
import type { Locale } from "@/lib/i18n";

export function LogoutButton({
  locale,
  label,
  loadingLabel,
}: {
  locale: Locale;
  label: string;
  loadingLabel: string;
}) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function handleLogout() {
    setLoading(true);
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push(`/${locale}`);
    router.refresh();
  }

  return (
    <BrutalButton variant="paper" onClick={handleLogout} disabled={loading}>
      {loading ? loadingLabel : label}
    </BrutalButton>
  );
}
