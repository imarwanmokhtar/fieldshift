export const locales = ["ar", "en"] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = "ar";

export function isLocale(value: string): value is Locale {
  return (locales as readonly string[]).includes(value);
}

const en = {
  nav: { login: "Log in", switchLabel: "العربية" },
  hero: {
    tag: "NASA Space Apps Challenge 2026",
    title: "Choose your next crop with evidence, not guesswork.",
    subtitle:
      "A decision-support tool that turns NASA Earth observations into clear crop-rotation options for farmers.",
    getStarted: "Get started",
    login: "Log in",
  },
  problem: {
    title: "The problem",
    items: [
      "Temperatures are shifting and rainfall is less predictable.",
      "Water is getting scarcer and soils are losing health.",
      "A crop that helps soil in one place can use too much water, bring disease, miss the market or fall outside the season somewhere else.",
    ],
    whatTitle: "What Field Shift does",
    cards: [
      {
        title: "Compares at least three rotation strategies",
        body: "Including the rotation you already use, so you can see the trade-offs side by side.",
      },
      {
        title: "Shows the reasoning for each strategy",
        body: "Why it was suggested, what evidence supports it, expected benefits, information gaps, and risks that need local review.",
      },
      {
        title: "Lets you set your own priorities",
        body: "Saving water, adding income, improving soil structure — you decide what matters most for your farm.",
      },
    ],
  },
  how: {
    title: "How it works",
    stepLabel: "Step",
    steps: [
      {
        title: "Observe",
        body: "Satellite and climate data describe local conditions over many years.",
      },
      {
        title: "Compare",
        body: "Rotation strategies are scored against heat, water, soil and market priorities.",
      },
      {
        title: "Decide",
        body: "The farmer reviews clear explanations, with risks and uncertainty stated, and makes the final call.",
      },
    ],
  },
  data: {
    title: "Data behind it",
    note: "Satellite data is coarse in places and does not replace ground measurements. Each result states its uncertainty.",
    explain:
      "NDVI measures how green and dense vegetation is. Evapotranspiration is the water a crop loses to the air — a direct input for irrigation planning.",
    sources: [
      { name: "Landsat, MODIS/VIIRS, Sentinel-2", body: "Crop vigor (NDVI), bare-field periods, seasonal change." },
      { name: "NASA POWER and ERA5", body: "Temperature, radiation, humidity, frost and heat risk, water demand." },
      { name: "GPM / IMERG", body: "Rainfall and extreme-storm patterns." },
      { name: "SMAP", body: "Soil moisture trends." },
      { name: "ECOSTRESS", body: "Land-surface temperature and evapotranspiration." },
      { name: "GRACE / GRACE-FO", body: "Long-term water storage trends." },
      { name: "FAO GAEZ", body: "Crop suitability by climate and soil." },
    ],
  },
  principles: {
    title: "Principles",
    items: [
      "Supports farmer judgment. It never replaces it.",
      "Every recommendation shows its reasoning.",
      "Gaps and risks are stated openly.",
      "Local agricultural experts should review before decisions are made.",
    ],
  },
  pilot: {
    label: "Pilot region",
    name: "Dakahlia, Egypt",
    body: "Dakahlia sits in the Nile Delta, one of Egypt's most productive agricultural governorates. Intensive rotation cycles, rising heat and pressure on water make it exactly the kind of place where rotation decisions deserve better evidence.",
  },
  footer: {
    name: "Field Shift",
    line: "NASA Space Apps Challenge 2026 · Built by the Field Shift team",
    note: "NASA does not endorse this project. Field Shift uses data and concepts from NASA Earth observation missions and Space Agency Partner resources; participants follow the data use terms of each source.",
    login: "Log in",
    signup: "Sign up",
  },
  auth: {
    loginTitle: "Log in",
    loginSubtitle: "Welcome back. Log in to reach your dashboard.",
    signupTitle: "Create your account",
    signupSubtitle: "Just an email and a password. Farm and field details come later.",
    email: "Email",
    emailPlaceholder: "you@example.com",
    password: "Password",
    passwordPlaceholder: "At least 6 characters",
    loginButton: "Log in",
    loginLoading: "Logging in…",
    signupButton: "Create account",
    signupLoading: "Creating account…",
    haveAccount: "Already have an account?",
    toLogin: "Log in",
    noAccount: "New to Field Shift?",
    toSignup: "Create an account",
    wrongPassword: "Wrong email or password. Please try again.",
    authLinkError: "That sign-in link is invalid or expired. Log in again below.",
    checkEmailTitle: "Check your email",
    checkEmailBody: "We sent a confirmation link to {email}. Click it to finish creating your account.",
    backToLogin: "Back to log in",
  },
  dashboard: {
    welcome: "Welcome",
    emptyTitle: "Your dashboard is empty",
    emptyBody:
      "Farm and field tools are coming soon. In the next phase you'll add your fields, set your priorities and compare rotation strategies backed by NASA Earth observations.",
    logout: "Log out",
    logoutLoading: "Logging out…",
    title: "Dashboard — Field Shift",
  },
  meta: {
    title: "Field Shift — Choose your next crop with evidence",
    description:
      "Decision support for crop rotation, powered by NASA Earth observations. Built for the NASA Space Apps Challenge 2026. Pilot region: Dakahlia, Egypt.",
  },
};

export type Dictionary = typeof en;

const ar: Dictionary = {
  nav: { login: "تسجيل الدخول", switchLabel: "English" },
  hero: {
    tag: "NASA Space Apps Challenge 2026",
    title: "اختر محصولك القادم بالأدلة، لا بالتخمين.",
    subtitle:
      "أداة دعم قرارات تحوّل رصدات NASA للأرض إلى خيارات واضحة لتدوير المحاصيل في متناول المزارعين.",
    getStarted: "ابدأ الآن",
    login: "تسجيل الدخول",
  },
  problem: {
    title: "المشكلة",
    items: [
      "درجات الحرارة تتغيّر والأمطار صارت أقل قابلية للتنبؤ.",
      "المياه تزداد شحًّا والتربة تفقد صحتها.",
      "المحصول الذي ينفع التربة في مكان ما قد يستهلك ماءً زائدًا أو يجلب الأمراض أو يخفق في السوق أو يقع خارج الموسم في مكان آخر.",
    ],
    whatTitle: "ماذا يفعل Field Shift",
    cards: [
      {
        title: "يقارن ثلاث استراتيجيات تدوير على الأقل",
        body: "منها التدوير الذي تستخدمه بالفعل، لترى المقايضات جنبًا إلى جنب.",
      },
      {
        title: "يوضح الأسباب وراء كل استراتيجية",
        body: "لماذا قُترحت، وما الأدلة التي تسندها، والفوائد المتوقعة، والفجوات المعلوماتية، والمخاطر التي تحتاج مراجعة محلية.",
      },
      {
        title: "يترك لك تحديد أولوياتك",
        body: "توفير المياه، زيادة الدخل، تحسين بنية التربة — أنت من يقرر ما يهمّ مزرعتك.",
      },
    ],
  },
  how: {
    title: "كيف يعمل",
    stepLabel: "الخطوة",
    steps: [
      {
        title: "لاحِظ",
        body: "بيانات الأقمار الصناعية والمناخ تصف الظروف المحلية عبر سنوات عديدة.",
      },
      {
        title: "قارِن",
        body: "تُقيَّم استراتيجيات التدوير وفق أولويات الحرارة والماء والتربة والسوق.",
      },
      {
        title: "قرِّر",
        body: "يراجع المزارع شروحات واضحة مع بيان المخاطر وعدم اليقين، ويتخذ القرار النهائي.",
      },
    ],
  },
  data: {
    title: "البيانات خلفه",
    note: "بيانات الأقمار الصناعية تقريبية في بعض الأماكن ولا تُغني عن القياسات الأرضية. كل نتيجة توضح درجة عدم اليقين فيها.",
    explain:
      "يقيس NDVI مدى خضرة الغطاء النباتي وكثافته. والنتح هو الماء الذي يفقده المحصول إلى الهواء — مدخل مباشر لتخطيط الري.",
    sources: [
      { name: "Landsat · MODIS/VIIRS · Sentinel-2", body: "نشاط المحصول (NDVI)، فترات بقاء الحقل جرداءً، والتغيّر الموسمي." },
      { name: "NASA POWER وERA5", body: "الحرارة، الإشعاع الشمسي، الرطوبة، خطر الصقيع والحرارة الشديدة، والاحتياج المائي." },
      { name: "GPM / IMERG", body: "أنماط الأمطار والعواصف الشديدة." },
      { name: "SMAP", body: "اتجاهات رطوبة التربة." },
      { name: "ECOSTRESS", body: "حرارة سطح الأرض والنتح." },
      { name: "GRACE / GRACE-FO", body: "اتجاهات مخزون المياه على المدى الطويل." },
      { name: "FAO GAEZ", body: "مدى ملاءمة المحاصيل حسب المناخ والتربة." },
    ],
  },
  principles: {
    title: "المبادئ",
    items: [
      "يدعم حكم المزارع ولا يستبدله أبدًا.",
      "كل توصية توضح أسبابها.",
      "الفجوات والمخاطر تُذكر بصراحة.",
      "ينبغي أن يراجع الخبراء الزراعيون المحليون قبل اتخاذ القرار.",
    ],
  },
  pilot: {
    label: "المنطقة التجريبية",
    name: "الدقهلية، مصر",
    body: "تقع الدقهلية في دلتا النيل، وهي من أكثر محافظات مصر إنتاجًا زراعيًا. فدورات التدوير المكثفة وارتفاع الحرارة والضغط على المياه تجعلها من النوع من الأماكن الذي تستحق فيه قرارات تدوير المحاصيل أدلةً أفضل.",
  },
  footer: {
    name: "Field Shift",
    line: "تحدي NASA Space Apps 2026 · بُني بواسطة فريق Field Shift",
    note: "NASA لا تؤيد هذا المشروع. يستخدم Field Shift بيانات ومفاهيم من مهمات رصد الأرض التابعة لـ NASA وموارد شركاء وكالات الفضاء، ويلتزم المشاركون بشروط استخدام البيانات لكل مصدر.",
    login: "تسجيل الدخول",
    signup: "إنشاء حساب",
  },
  auth: {
    loginTitle: "تسجيل الدخول",
    loginSubtitle: "أهلًا بعودتك. سجّل الدخول للوصول إلى لوحتك.",
    signupTitle: "أنشئ حسابك",
    signupSubtitle: "بريد إلكتروني وكلمة مرور فقط. تفاصيل المزرعة والحقول تأتي لاحقًا.",
    email: "البريد الإلكتروني",
    emailPlaceholder: "you@example.com",
    password: "كلمة المرور",
    passwordPlaceholder: "6 أحرف على الأقل",
    loginButton: "تسجيل الدخول",
    loginLoading: "جارٍ تسجيل الدخول…",
    signupButton: "إنشاء حساب",
    signupLoading: "جارٍ إنشاء الحساب…",
    haveAccount: "لديك حساب بالفعل؟",
    toLogin: "سجّل الدخول",
    noAccount: "أول مرة على Field Shift؟",
    toSignup: "أنشئ حسابًا",
    wrongPassword: "البريد الإلكتروني أو كلمة المرور غير صحيحة. حاول مرة أخرى.",
    authLinkError: "رابط الدخول غير صالح أو منتهي الصلاحية. سجّل الدخول مرة أخرى.",
    checkEmailTitle: "تحقق من بريدك",
    checkEmailBody: "أرسلنا رابط تأكيد إلى {email}. انقر عليه لإنهاء إنشاء حسابك.",
    backToLogin: "العودة إلى تسجيل الدخول",
  },
  dashboard: {
    welcome: "أهلًا بك",
    emptyTitle: "لوحتك فارغة",
    emptyBody:
      "أدوات المزرعة والحقول قادمة قريبًا. في المرحلة التالية ستضيف حقولك وتحدّد أولوياتك وتقارن استراتيجيات التدوير المدعومة برصدات NASA للأرض.",
    logout: "تسجيل الخروج",
    logoutLoading: "جارٍ تسجيل الخروج…",
    title: "لوحة التحكم — Field Shift",
  },
  meta: {
    title: "Field Shift — اختر محصولك القادم بالأدلة",
    description:
      "دعم القرارات لتدوير المحاصيل مدعوم برصدات NASA للأرض. بُني لتحدي NASA Space Apps 2026. المنطقة التجريبية: الدقهلية، مصر.",
  },
};

const dictionaries: Record<Locale, Dictionary> = { ar, en };

export function getDictionary(locale: string): Dictionary {
  return isLocale(locale) ? dictionaries[locale] : dictionaries[defaultLocale];
}
