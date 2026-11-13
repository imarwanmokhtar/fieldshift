"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import type { Dictionary, Locale } from "@/lib/i18n";
import { BrutalButton } from "@/components/brutal-button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

export function LoginForm({
  locale,
  dict,
}: {
  locale: Locale;
  dict: Dictionary;
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(false);

  const callbackError = searchParams.get("error") === "auth";

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);

    // Read values from the DOM at submit time (uncontrolled inputs), so
    // anything typed before React hydration is still captured.
    const formData = new FormData(event.currentTarget);
    const email = String(formData.get("email") ?? "");
    const password = String(formData.get("password") ?? "");

    const supabase = createClient();
    const { error } = await supabase.auth.signInWithPassword({ email, password });

    if (error) {
      toast.error(
        error.message === "Invalid login credentials"
          ? dict.auth.wrongPassword
          : error.message,
      );
      setLoading(false);
      return;
    }

    router.push(`/${locale}/onboarding`);
    router.refresh();
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {callbackError && (
        <p
          role="alert"
          className="border-[3px] border-ink bg-green-light p-4 text-base font-medium shadow-brutal-sm"
        >
          {dict.auth.authLinkError}
        </p>
      )}
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
          autoComplete="current-password"
          required
          className="h-12 rounded-none border-[3px] border-ink bg-paper text-base shadow-brutal-sm"
        />
      </div>
      <BrutalButton type="submit" variant="dark" disabled={loading} className="w-full">
        {loading ? dict.auth.loginLoading : dict.auth.loginButton}
      </BrutalButton>
      <p className="text-base">
        {dict.auth.noAccount}{" "}
        <Link
          href={`/${locale}/signup`}
          className="font-heading font-bold uppercase underline decoration-[3px] underline-offset-4 hover:bg-ink hover:text-paper"
        >
          {dict.auth.toSignup}
        </Link>
      </p>
    </form>
  );
}
