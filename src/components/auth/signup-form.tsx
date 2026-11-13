"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import type { Dictionary, Locale } from "@/lib/i18n";
import { BrutalButton } from "@/components/brutal-button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

export function SignupForm({
  locale,
  dict,
}: {
  locale: Locale;
  dict: Dictionary;
}) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [confirmationSent, setConfirmationSent] = useState(false);
  const [sentTo, setSentTo] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);

    // Read values from the DOM at submit time (uncontrolled inputs), so
    // anything typed before React hydration is still captured.
    const formData = new FormData(event.currentTarget);
    const email = String(formData.get("email") ?? "");
    const password = String(formData.get("password") ?? "");

    const supabase = createClient();
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        // Confirmation link lands on /auth/callback, which exchanges the
        // code for a session. This URL must be allow-listed in Supabase
        // URL Configuration (Authentication → URL Configuration).
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    });

    if (error) {
      toast.error(error.message);
      setLoading(false);
      return;
    }

    // Email confirmation disabled: a session comes back right away.
    if (data.session) {
      router.push(`/${locale}/onboarding`);
      router.refresh();
      setLoading(false); // cleanup if navigation is interrupted
      return;
    }

    // Email confirmation enabled: no session until the user confirms.
    setLoading(false);
    setSentTo(email);
    setConfirmationSent(true);
  }

  if (confirmationSent) {
    return (
      <div className="border-[3px] border-ink bg-paper p-6 text-base shadow-brutal">
        <p className="font-heading text-lg font-bold uppercase">
          {dict.auth.checkEmailTitle}
        </p>
        <p className="mt-2">
          {dict.auth.checkEmailBody.replace("{email}", sentTo)}
        </p>
        <Link
          href={`/${locale}/login`}
          className="mt-4 inline-block font-heading text-sm font-bold uppercase tracking-wide underline decoration-[3px] underline-offset-4 hover:bg-ink hover:text-paper"
        >
          {dict.auth.backToLogin}
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="email">{dict.auth.email}</Label>
        <Input
          id="email"
          name="email"
          type="email"
          placeholder={dict.auth.emailPlaceholder}
          autoComplete="email"
          required
          className="h-12 rounded-none border-[3px] border-ink bg-paper text-base shadow-brutal-sm"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="password">{dict.auth.password}</Label>
        <Input
          id="password"
          name="password"
          type="password"
          placeholder={dict.auth.passwordPlaceholder}
          autoComplete="new-password"
          required
          minLength={6}
          className="h-12 rounded-none border-[3px] border-ink bg-paper text-base shadow-brutal-sm"
        />
      </div>
      <BrutalButton type="submit" variant="dark" disabled={loading} className="w-full">
        {loading ? dict.auth.signupLoading : dict.auth.signupButton}
      </BrutalButton>
      <p className="text-base">
        {dict.auth.haveAccount}{" "}
        <Link
          href={`/${locale}/login`}
          className="font-heading font-bold uppercase underline decoration-[3px] underline-offset-4 hover:bg-ink hover:text-paper"
        >
          {dict.auth.toLogin}
        </Link>
      </p>
    </form>
  );
}
