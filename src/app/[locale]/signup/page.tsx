import type { Metadata } from "next";
import { AuthShell } from "@/components/auth/auth-shell";
import { SignupForm } from "@/components/auth/signup-form";
import { getDictionary, type Locale } from "@/lib/i18n";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const dict = getDictionary(locale);
  return { title: `${dict.auth.signupTitle} — Field Shift` };
}

export default async function SignupPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const dict = getDictionary(raw);

  return (
    <AuthShell
      title={dict.auth.signupTitle}
      subtitle={dict.auth.signupSubtitle}
      locale={raw as Locale}
      dict={dict}
    >
      <SignupForm locale={raw as Locale} dict={dict} />
    </AuthShell>
  );
}
