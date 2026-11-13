import { Hero } from "@/components/landing/hero";
import { Problem } from "@/components/landing/problem";
import { HowItWorks } from "@/components/landing/how-it-works";
import { DataSources } from "@/components/landing/data-sources";
import { Principles } from "@/components/landing/principles";
import { Pilot } from "@/components/landing/pilot";
import { Footer } from "@/components/landing/footer";
import { getDictionary, type Locale } from "@/lib/i18n";

export default async function LandingPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const dict = getDictionary(raw);
  const locale = raw as Locale;

  return (
    <main>
      <Hero dict={dict} locale={locale} />
      <Problem dict={dict} />
      <HowItWorks dict={dict} />
      <DataSources dict={dict} />
      <Principles dict={dict} />
      <Pilot dict={dict} />
      <Footer dict={dict} locale={locale} />
    </main>
  );
}
