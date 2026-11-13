import type { Locale } from "@/lib/i18n";

const en = {
  pageTitle: "Your rotation options",
  back: "Back to dashboard",
  stages: {
    pending: "Getting started…",
    reading_data: "Reading NASA climate and satellite data…",
    comparing: "Comparing rotation strategies…",
    writing: "Writing your summary…",
  } as Record<string, string>,
  slow: "This is taking longer than usual. You can leave this page and come back later.",
  failedTitle: "The analysis could not be completed",
  retry: "Try again",
  retrying: "Starting…",
  recommended: "Best match",
  overall: "Overall score",
  confidence: { high: "High confidence", medium: "Medium confidence", low: "Low confidence" },
  criteria: {
    water: "Water saving",
    soil: "Soil health",
    income: "Income",
    heat: "Heat safety",
    cost: "Low cost",
    risk: "Low risk",
    forage: "Fodder",
  },
  sections: {
    why: "Why it was suggested",
    evidence: "Evidence",
    benefits: "Benefits",
    gaps: "Information gaps",
    risks: "Risks to review locally",
  },
  year: "Year",
  seasons: { winter: "Winter", summer: "Summer" },
  waterPerYear: "m³ water / feddan / year",
  dataNotes: "About the data",
  climateFallback: "NASA climate data could not be loaded for this run. Results use approximate averages.",
  templateNote: "Summary written from templates (AI explanation not enabled).",
  startError: "Could not start the analysis. Please try again in a minute.",
  fallow: "Empty (fallow)",
};

const ar: typeof en = {
  pageTitle: "خيارات الدورة الزراعية لك",
  back: "العودة إلى لوحة التحكم",
  stages: {
    pending: "جارٍ البدء…",
    reading_data: "جارٍ قراءة بيانات المناخ والأقمار الصناعية من ناسا…",
    comparing: "جارٍ مقارنة الدورات الزراعية…",
    writing: "جارٍ كتابة الملخص…",
  },
  slow: "يستغرق هذا وقتاً أطول من المعتاد. يمكنك مغادرة الصفحة والعودة لاحقاً.",
  failedTitle: "تعذر إكمال التحليل",
  retry: "حاول مرة أخرى",
  retrying: "جارٍ البدء…",
  recommended: "الأنسب لك",
  overall: "الدرجة الكلية",
  confidence: { high: "ثقة عالية", medium: "ثقة متوسطة", low: "ثقة منخفضة" },
  criteria: {
    water: "توفير المياه",
    soil: "صحة التربة",
    income: "الدخل",
    heat: "الأمان من الحرارة",
    cost: "تكلفة أقل",
    risk: "مخاطر أقل",
    forage: "العلف",
  },
  sections: {
    why: "لماذا تم اقتراحها",
    evidence: "الأدلة",
    benefits: "الفوائد",
    gaps: "معلومات ناقصة",
    risks: "مخاطر تحتاج مراجعة محلية",
  },
  year: "السنة",
  seasons: { winter: "شتوي", summer: "صيفي" },
  waterPerYear: "م³ مياه / فدان / سنة",
  dataNotes: "عن البيانات",
  climateFallback: "تعذر تحميل بيانات المناخ من ناسا في هذا التحليل، لذلك استُخدمت متوسطات تقريبية.",
  templateNote: "تمت كتابة الملخص من نماذج جاهزة (شرح الذكاء الاصطناعي غير مفعّل).",
  startError: "تعذر بدء التحليل. يرجى المحاولة بعد دقيقة.",
  fallow: "أرض متروكة (بور)",
};

export function getResultsStrings(locale: Locale) {
  return locale === "ar" ? ar : en;
}

export type ResultsStrings = typeof en;
