/**
 * Field Shift — Farmer Onboarding Questions Configuration
 *
 * This is the single source of truth for the wizard. Adding, removing,
 * or reordering questions here automatically updates the UI — no other
 * changes needed.
 *
 * Each question has bilingual labels (en/ar). The wizard renders purely
 * from this config.
 */

import type { Locale } from "@/lib/i18n";

export type QuestionType =
    | "single"
    | "multi"
    | "number"
    | "numberWithUnit"
    | "text"
    | "mapPin"
    | "rank"
    | "twoNumbers"
    | "soilTest"
    | "cropAndSeason";

export type Bilingual = { en: string; ar: string };

export interface QuestionOption {
    value: string;
    label: Bilingual;
    isNone?: boolean;
}

export interface QuestionConfig {
    id: string;
    section: string;
    title: Bilingual;
    help?: Bilingual;
    type: QuestionType;
    options?: QuestionOption[];
    required?: boolean;
    allowUnknown?: boolean;
    showIf?: (answers: Record<string, unknown>) => boolean;
    unitOptions?: { value: string; label: Bilingual; toHectares: number }[];
    validation?: {
        min?: number;
        max?: number;
        positive?: boolean;
    };
}

export const CROP_OPTIONS: QuestionOption[] = [
    { value: "wheat", label: { en: "Wheat", ar: "قمح" } },
    { value: "rice", label: { en: "Rice", ar: "أرز" } },
    { value: "maize", label: { en: "Maize", ar: "ذرة" } },
    { value: "cotton", label: { en: "Cotton", ar: "قطن" } },
    { value: "berseem", label: { en: "Berseem (clover)", ar: "برسيم" } },
    { value: "sugar_beet", label: { en: "Sugar beet", ar: "بنجر سكر" } },
    { value: "faba_bean", label: { en: "Faba bean", ar: "فول بلدي" } },
    { value: "onion", label: { en: "Onion", ar: "بصل" } },
    { value: "potato", label: { en: "Potato", ar: "بطاطس" } },
    { value: "tomato", label: { en: "Tomato", ar: "طماطم" } },
    { value: "other_vegetables", label: { en: "Other vegetables", ar: "خضروات أخرى" } },
    { value: "fruit_trees", label: { en: "Fruit trees", ar: "أشجار مثمرة" } },
    { value: "sorghum", label: { en: "Sorghum", ar: "ذرة رفيعة" } },
    { value: "sesame", label: { en: "Sesame", ar: "سمسم" } },
    { value: "peanut", label: { en: "Peanut", ar: "فول سوداني" } },
    { value: "fallow", label: { en: "Left empty (fallow)", ar: "متروك (بور)" } },
    { value: "other", label: { en: "Other (specify)", ar: "أخرى (حدد)" } },
];

export const SEASON_OPTIONS: QuestionOption[] = [
    { value: "winter", label: { en: "Winter (Nov–Apr)", ar: "شتاء (تشرين الثاني–أبريل)" } },
    { value: "summer", label: { en: "Summer (May–Oct)", ar: "صيف (مايو–أكتوبر)" } },
];

const SOIL_TEXTURE_OPTIONS: QuestionOption[] = [
    { value: "clay", label: { en: "Sticky and heavy (clay)", ar: "لزج وثقيل (طين)" } },
    { value: "loam", label: { en: "Smooth, holds shape (loam)", ar: "ناعم، يحتفظ بالشكل (طمي)" } },
    { value: "sandy", label: { en: "Gritty, falls apart (sandy)", ar: "خشن، يتفتت (رمل)" } },
    { value: "mixed", label: { en: "Mixed", ar: "مختلط" } },
];

const DRAINAGE_OPTIONS: QuestionOption[] = [
    { value: "hours", label: { en: "Within hours", ar: "خلال ساعات" } },
    { value: "day", label: { en: "About a day", ar: "حوالي يوم" } },
    { value: "several_days", label: { en: "Several days (stays on top)", ar: "عدة أيام (يبقى على السطح)" } },
];

const SALINITY_OPTIONS: QuestionOption[] = [
    { value: "never", label: { en: "Never", ar: "أبداً" } },
    { value: "some_spots", label: { en: "Some spots", ar: "بعض البقع" } },
    { value: "large_areas", label: { en: "Large areas", ar: "مساحات كبيرة" } },
];

const SOIL_ISSUES_OPTIONS: QuestionOption[] = [
    { value: "hard_layer", label: { en: "Hard layer", ar: "طبقة صلبة" } },
    { value: "deep_cracks", label: { en: "Deep cracks when dry", ar: "شقوق عميقة عند الجفاف" } },
    { value: "waterlogging", label: { en: "Waterlogging", ar: "استنقاع مائي" } },
    { value: "erosion", label: { en: "Erosion by water or wind", ar: "تآكل بالماء أو الرياح" } },
    { value: "weeds", label: { en: "Weeds taking over", ar: "أعشاب تسيطر" } },
    { value: "low_fertility", label: { en: "Low fertility", ar: "خصوبة منخفضة" } },
    { value: "none", label: { en: "None", ar: "لا شيء" }, isNone: true },
];

const ORGANIC_INPUTS_OPTIONS: QuestionOption[] = [
    { value: "every_season", label: { en: "Every season", ar: "كل موسم" } },
    { value: "once_year", label: { en: "Once a year", ar: "مرة في السنة" } },
    { value: "rarely", label: { en: "Rarely", ar: "نادراً" } },
    { value: "never", label: { en: "Never", ar: "أبداً" } },
];

const SOIL_TEST_OPTIONS: QuestionOption[] = [
    { value: "no", label: { en: "No", ar: "لا" } },
    { value: "yes", label: { en: "Yes", ar: "نعم" } },
];

const WATER_SOURCE_OPTIONS: QuestionOption[] = [
    { value: "nile_canal", label: { en: "Nile canal", ar: "ترعة نيلية" } },
    { value: "groundwater_well", label: { en: "Groundwater well", ar: "بئر مياه جوفية" } },
    { value: "drainage_reuse", label: { en: "Drainage reuse", ar: "إعادة استخدام صرف" } },
    { value: "rain_only", label: { en: "Rain only", ar: "مطر فقط" } },
    { value: "other", label: { en: "Other", ar: "أخرى" } },
];

const WATER_RELIABILITY_OPTIONS: QuestionOption[] = [
    { value: "always", label: { en: "Always", ar: "دائماً" } },
    { value: "mostly", label: { en: "Mostly", ar: "غالباً" } },
    { value: "often_late", label: { en: "Often late or short", ar: "كثيراً ما تتأخر أو تنقص" } },
    { value: "rarely", label: { en: "Rarely", ar: "نادراً" } },
];

const IRRIGATION_METHOD_OPTIONS: QuestionOption[] = [
    { value: "flood", label: { en: "Flood", ar: "غمر" } },
    { value: "furrow", label: { en: "Furrow", ar: "أثلام" } },
    { value: "sprinkler", label: { en: "Sprinkler", ar: "رش" } },
    { value: "drip", label: { en: "Drip", ar: "تنقيط" } },
    { value: "pivot", label: { en: "Pivot", ar: "محوري" } },
    { value: "other", label: { en: "Other", ar: "أخرى" } },
];

const WATER_QUALITY_OPTIONS: QuestionOption[] = [
    { value: "good", label: { en: "Good", ar: "جيدة" } },
    { value: "slightly_salty", label: { en: "Slightly salty", ar: "مملحة قليلاً" } },
    { value: "salty", label: { en: "Salty", ar: "مملحة" } },
    { value: "polluted", label: { en: "Looks polluted", ar: "تبدو ملوثة" } },
];

const WATER_COST_OPTIONS: QuestionOption[] = [
    { value: "not_at_all", label: { en: "Not at all", ar: "لا على الإطلاق" } },
    { value: "somewhat", label: { en: "Somewhat", ar: "إلى حد ما" } },
    { value: "heavy", label: { en: "Heavy", ar: "ثقل" } },
    { value: "free", label: { en: "Water is free", ar: "الماء مجاني" } },
];

const BARE_PERIODS_OPTIONS: QuestionOption[] = [
    { value: "never", label: { en: "Never", ar: "أبداً" } },
    { value: "under_1_month", label: { en: "Under 1 month", ar: "أقل من شهر" } },
    { value: "1_to_3_months", label: { en: "1 to 3 months", ar: "1 إلى 3 أشهر" } },
    { value: "over_3_months", label: { en: "More than 3 months", ar: "أكثر من 3 أشهر" } },
];

const YIELD_VS_EXPECTED_OPTIONS: QuestionOption[] = [
    { value: "better", label: { en: "Better", ar: "أفضل" } },
    { value: "same", label: { en: "About the same", ar: "تقريباً نفس الشيء" } },
    { value: "worse", label: { en: "Worse", ar: "أسوأ" } },
];

const PEST_ISSUES_OPTIONS: QuestionOption[] = [
    { value: "insects", label: { en: "Insects", ar: "حشرات" } },
    { value: "fungal_disease", label: { en: "Fungal disease", ar: "أمراض فطرية" } },
    { value: "weeds", label: { en: "Weeds", ar: "أعشاب ضارة" } },
    { value: "nematodes", label: { en: "Nematodes", ar: "نيماتودا" } },
    { value: "birds_rodents", label: { en: "Birds or rodents", ar: "طيور أو قوارض" } },
    { value: "none", label: { en: "None", ar: "لا شيء" }, isNone: true },
];

const FERTILIZER_LEVEL_OPTIONS: QuestionOption[] = [
    { value: "none", label: { en: "None", ar: "لا شيء" } },
    { value: "low", label: { en: "Low", ar: "منخفض" } },
    { value: "medium", label: { en: "Medium", ar: "متوسط" } },
    { value: "high", label: { en: "High", ar: "عالي" } },
];

const PRIORITIES_OPTIONS: QuestionOption[] = [
    { value: "save_water", label: { en: "Save water", ar: "توفير الماء" } },
    { value: "higher_income", label: { en: "Higher income", ar: "دخل أعلى" } },
    { value: "better_soil", label: { en: "Better soil", ar: "تربة أفضل" } },
    { value: "lower_costs", label: { en: "Lower costs", ar: "تكاليف أقل" } },
    { value: "lower_risk", label: { en: "Lower risk", ar: "مخاطر أقل" } },
    { value: "fodder", label: { en: "Fodder for animals", ar: "علف للحيوانات" } },
];

const LIVESTOCK_OPTIONS: QuestionOption[] = [
    { value: "no", label: { en: "No", ar: "لا" } },
    { value: "cattle_buffalo", label: { en: "Cattle or buffalo", ar: "أبقار أو جاموس" } },
    { value: "sheep_goats", label: { en: "Sheep or goats", ar: "أغنام أو ماعز" } },
    { value: "poultry", label: { en: "Poultry", ar: "دواجن" } },
];

const MARKET_OPTIONS: QuestionOption[] = [
    { value: "government", label: { en: "Government procurement", ar: "توريد حكومي" } },
    { value: "cooperative", label: { en: "Cooperative", ar: "جمعية تعاونية" } },
    { value: "trader", label: { en: "Trader", ar: "تاجر" } },
    { value: "local_market", label: { en: "Local market", ar: "سوق محلي" } },
    { value: "contract", label: { en: "Contract", ar: "عقد" } },
    { value: "own_use", label: { en: "Own use only", ar: "استخدام شخصي فقط" } },
];

const RISK_TOLERANCE_OPTIONS: QuestionOption[] = [
    { value: "stick_to_known", label: { en: "Stick to what I know", ar: "أبقى على ما أعرفه" } },
    { value: "small_trial", label: { en: "Small trial first", ar: "تجربة صغيرة أولاً" } },
    { value: "ready_to_change", label: { en: "Ready to change", ar: "مستعد للتغيير" } },
];

const EQUIPMENT_OPTIONS: QuestionOption[] = [
    { value: "tractor", label: { en: "Tractor", ar: "جرار" } },
    { value: "planter", label: { en: "Planter", ar: "آلة زراعة" } },
    { value: "harvester", label: { en: "Harvester", ar: "آلة حصاد" } },
    { value: "sprayer", label: { en: "Sprayer", ar: "آلة رش" } },
    { value: "pump", label: { en: "Pump", ar: "مضخة" } },
    { value: "hand_labor", label: { en: "Hand labor only", ar: "يدوية فقط" } },
];

const HORIZON_OPTIONS: QuestionOption[] = [
    { value: "next_season", label: { en: "Next season only", ar: "الموسم القادم فقط" } },
    { value: "2_to_3_years", label: { en: "2 to 3 years", ar: "2 إلى 3 سنوات" } },
    { value: "5_plus_years", label: { en: "5+ years", ar: "5+ سنوات" } },
];

const AREA_UNITS = [
    { value: "feddan", label: { en: "Feddan", ar: "فدان" }, toHectares: 0.42 },
    { value: "kirat", label: { en: "Kirat", ar: "قيراط" }, toHectares: 0.0175 },
    { value: "hectare", label: { en: "Hectare", ar: "هكتار" }, toHectares: 1 },
];

export const ONBOARDING_QUESTIONS: readonly QuestionConfig[] = [
    { id: "pin", section: "A. YOUR FIELD", title: { en: "Drop a pin on your field", ar: "ضع علامة على حقلك" }, help: { en: "Click the map, use your location, or type coordinates", ar: "اضغط على الخريطة، استخدم موقعك، أو اكتب الإحداثيات" }, type: "mapPin", required: true, allowUnknown: false },
    { id: "field_name", section: "A. YOUR FIELD", title: { en: "What do you call this field?", ar: "ماذا تسمي هذا الحقل؟" }, help: { en: "Optional name for your reference", ar: "اسم اختياري للرجوع إليه" }, type: "text", required: false, allowUnknown: true },
    { id: "area", section: "A. YOUR FIELD", title: { en: "How big is this field?", ar: "ما حجم هذا الحقل؟" }, help: { en: "Number plus unit (feddan, kirat, or hectare)", ar: "رقم مع وحدة (فدان، قيراط، أو هكتار)" }, type: "numberWithUnit", unitOptions: AREA_UNITS, required: true, allowUnknown: false, validation: { min: 0.01, positive: true } },

    { id: "soil_texture", section: "B. YOUR SOIL", title: { en: "When wet, how does the soil feel?", ar: "عندما تكون رطبة، كيف تشعر التربة؟" }, type: "single", options: SOIL_TEXTURE_OPTIONS, allowUnknown: true },
    { id: "drainage", section: "B. YOUR SOIL", title: { en: "After irrigation, how fast does the water sink in?", ar: "بعد الري، ما سرعة تسرب الماء؟" }, type: "single", options: DRAINAGE_OPTIONS, allowUnknown: true },
    { id: "salinity", section: "B. YOUR SOIL", title: { en: "Do you see white salt crust or patchy, poor growth?", ar: "هل ترى قشرة ملح بيضاء أو نمو ضعيف متقطع؟" }, type: "single", options: SALINITY_OPTIONS, allowUnknown: true },
    { id: "soil_issues", section: "B. YOUR SOIL", title: { en: "Which soil problems have you seen?", ar: "أي مشاكل تربة رأيتها؟" }, type: "multi", options: SOIL_ISSUES_OPTIONS, allowUnknown: true },
    { id: "organic_inputs", section: "B. YOUR SOIL", title: { en: "Do you add manure or compost?", ar: "هل تضيف سماداً بلدياً أو كومبوست؟" }, type: "single", options: ORGANIC_INPUTS_OPTIONS, allowUnknown: true },
    { id: "soil_test", section: "B. YOUR SOIL", title: { en: "Do you have a soil test result?", ar: "هل لديك نتيجة تحليل تربة؟" }, type: "soilTest", options: SOIL_TEST_OPTIONS, allowUnknown: true },

    { id: "water_source", section: "C. YOUR WATER", title: { en: "Where does your irrigation water come from?", ar: "من أين يأتي ماء ريّك؟" }, type: "multi", options: WATER_SOURCE_OPTIONS, allowUnknown: true },
    { id: "water_reliability", section: "C. YOUR WATER", title: { en: "Does water arrive when your crop needs it?", ar: "هل يأتي الماء عندما يحتاجه محصولك؟" }, type: "single", options: WATER_RELIABILITY_OPTIONS, allowUnknown: true },
    { id: "irrigation_method", section: "C. YOUR WATER", title: { en: "How do you irrigate?", ar: "كيف تروي؟" }, type: "single", options: IRRIGATION_METHOD_OPTIONS, allowUnknown: true },
    { id: "irrigation_interval", section: "C. YOUR WATER", title: { en: "How many days between irrigations?", ar: "كم يوماً بين كل رية؟" }, help: { en: "Summer and winter intervals (1–60 days)", ar: "فاصلتا الصيف والشتاء (1–60 يوماً)" }, type: "twoNumbers", validation: { min: 1, max: 60 }, allowUnknown: true },
    { id: "water_quality", section: "C. YOUR WATER", title: { en: "How is your irrigation water quality?", ar: "كيف هي جودة ماء الري؟" }, type: "single", options: WATER_QUALITY_OPTIONS, allowUnknown: true },
    { id: "water_cost", section: "C. YOUR WATER", title: { en: "Is the cost of water or pumping a heavy burden?", ar: "هل تكلفة الماء أو الضخ عبء ثقيل؟" }, type: "single", options: WATER_COST_OPTIONS, allowUnknown: true },

    { id: "last_crop", section: "D. FIELD HISTORY", title: { en: "What did you grow most recently?", ar: "ماذا زرعت مؤخراً؟" }, help: { en: "Crop plus season (Winter ≈ Nov–Apr, Summer ≈ May–Oct)", ar: "المحصول مع الموسم (شتاء ≈ تشرين الثاني–أبريل، صيف ≈ مايو–أكتوبر)" }, type: "cropAndSeason", options: [...CROP_OPTIONS, ...SEASON_OPTIONS], allowUnknown: true },
    { id: "prev_crop", section: "D. FIELD HISTORY", title: { en: "And what did you grow before that?", ar: "وماذا زرعت قبل ذلك؟" }, help: { en: "Crop plus season (Winter ≈ Nov–Apr, Summer ≈ May–Oct)", ar: "المحصول مع الموسم (شتاء ≈ تشرين الثاني–أبريل، صيف ≈ مايو–أكتوبر)" }, type: "cropAndSeason", options: [...CROP_OPTIONS, ...SEASON_OPTIONS], allowUnknown: true },
    { id: "bare_periods", section: "D. FIELD HISTORY", title: { en: "How long is the field usually empty between crops?", ar: "كم مدة بقاء الحقل فارغاً بين المحاصيل؟" }, type: "single", options: BARE_PERIODS_OPTIONS, allowUnknown: true },
    { id: "yield_vs_expected", section: "D. FIELD HISTORY", title: { en: "How were your last yields compared with neighbors or past years?", ar: "كيف كانت محاصيلك الأخيرة مقارنة بالجيران أو السنوات السابقة؟" }, type: "single", options: YIELD_VS_EXPECTED_OPTIONS, allowUnknown: true },
    { id: "pest_issues", section: "D. FIELD HISTORY", title: { en: "Which problems have you had?", ar: "أي مشاكل واجهتها؟" }, type: "multi", options: PEST_ISSUES_OPTIONS, allowUnknown: true },
    { id: "fertilizer_level", section: "D. FIELD HISTORY", title: { en: "How much chemical fertilizer do you use?", ar: "كم كمية السماد الكيماوي التي تستخدمها؟" }, type: "single", options: FERTILIZER_LEVEL_OPTIONS, allowUnknown: true },

    { id: "priorities", section: "E. YOUR GOALS", title: { en: "What matters most to you? Pick up to 3, in order", ar: "ما الأهم بالنسبة لك؟ اختر حتى 3، بالترتيب" }, type: "rank", options: PRIORITIES_OPTIONS, required: true, allowUnknown: false },
    { id: "livestock", section: "E. YOUR GOALS", title: { en: "Do you keep animals that need fodder?", ar: "هل تربي حيوانات تحتاج علفاً؟" }, type: "single", options: LIVESTOCK_OPTIONS, allowUnknown: true },
    { id: "market", section: "E. YOUR GOALS", title: { en: "Where do you usually sell?", ar: "أين تبيع عادةً؟" }, type: "multi", options: MARKET_OPTIONS, allowUnknown: true },
    { id: "risk_tolerance", section: "E. YOUR GOALS", title: { en: "Would you try a new crop?", ar: "هل ستجرب محصولاً جديداً؟" }, type: "single", options: RISK_TOLERANCE_OPTIONS, allowUnknown: true },
    { id: "equipment", section: "E. YOUR GOALS", title: { en: "What do you have available?", ar: "ما المتاح لديك؟" }, type: "multi", options: EQUIPMENT_OPTIONS, allowUnknown: true },
    { id: "crop_filter", section: "E. YOUR GOALS", title: { en: "Any crops you definitely want, or definitely not?", ar: "أي محاصيل تريدها بالتأكيد، أو لا تريدها بالتأكيد؟" }, help: { en: "Select include and/or exclude from the crop list", ar: "اختر تضمن و/أو استبعاد من قائمة المحاصيل" }, type: "multi", options: CROP_OPTIONS, allowUnknown: true },
    { id: "horizon", section: "E. YOUR GOALS", title: { en: "How far ahead are you planning?", ar: "إلى أي مدى تخطط للأمام؟" }, type: "single", options: HORIZON_OPTIONS, allowUnknown: true },
] as const;

export const QUESTIONS_BY_SECTION = ONBOARDING_QUESTIONS.reduce(
    (acc, q) => {
        if (!acc[q.section]) acc[q.section] = [];
        acc[q.section].push(q);
        return acc;
    },
    {} as Record<string, QuestionConfig[]>
);

export const TOTAL_QUESTIONS = ONBOARDING_QUESTIONS.length;

export function getQuestionById(id: string): QuestionConfig | undefined {
    return ONBOARDING_QUESTIONS.find((q) => q.id === id);
}

export function getQuestionIndex(id: string): number {
    return ONBOARDING_QUESTIONS.findIndex((q) => q.id === id);
}

export function getLocalizedString(bilingual: Bilingual, locale: Locale): string {
    return bilingual[locale] ?? bilingual.en;
}

export function getLocalizedOption(option: QuestionOption, locale: Locale): string {
    return option.label[locale] ?? option.label.en;
}
