import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Space_Grotesk, Archivo, Cairo, Geist_Mono } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import { getDictionary, isLocale, locales } from "@/lib/i18n";
import "@/app/globals.css";

const spaceGrotesk = Space_Grotesk({
  variable: "--font-title-latin",
  subsets: ["latin"],
});

const archivo = Archivo({
  variable: "--font-body-latin",
  subsets: ["latin"],
});

const cairo = Cairo({
  variable: "--font-arabic",
  subsets: ["arabic", "latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const dict = getDictionary(locale);
  return { title: dict.meta.title, description: dict.meta.description };
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) {
    notFound();
  }

  return (
    <html
      lang={locale}
      dir={locale === "ar" ? "rtl" : "ltr"}
      className={`${spaceGrotesk.variable} ${archivo.variable} ${cairo.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-paper text-ink">
        {children}
        <Toaster position="bottom-right" />
      </body>
    </html>
  );
}
