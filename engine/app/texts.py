"""English and Arabic templates for every fact the engine can state.

The engine stores facts as (code, params). This module renders them in either
language. It is used for the English text sent to the LLM and for the
template fallback when the LLM is unavailable.
"""

from __future__ import annotations

from typing import Any

from .features import CROPS
from .schemas import Fact

SEASONS = {"winter": {"en": "winter", "ar": "الشتاء"}, "summer": {"en": "summer", "ar": "الصيف"}}
FALLOW = {"en": "empty (fallow)", "ar": "أرض متروكة (بور)"}

PRIORITY_NAMES = {
    "save_water": {"en": "saving water", "ar": "توفير المياه"},
    "higher_income": {"en": "higher income", "ar": "دخل أعلى"},
    "better_soil": {"en": "better soil", "ar": "تربة أفضل"},
    "lower_costs": {"en": "lower costs", "ar": "تكاليف أقل"},
    "lower_risk": {"en": "lower risk", "ar": "مخاطر أقل"},
    "fodder": {"en": "fodder for animals", "ar": "علف للحيوانات"},
}

QUESTION_NAMES = {
    "soil_texture": {"en": "soil type", "ar": "نوع التربة"},
    "drainage": {"en": "drainage", "ar": "صرف التربة"},
    "salinity": {"en": "salt problems", "ar": "مشاكل الملوحة"},
    "soil_issues": {"en": "soil problems", "ar": "مشاكل التربة"},
    "organic_inputs": {"en": "manure use", "ar": "استخدام السماد البلدي"},
    "soil_test": {"en": "soil test", "ar": "تحليل التربة"},
    "water_source": {"en": "water source", "ar": "مصدر المياه"},
    "water_reliability": {"en": "water reliability", "ar": "انتظام وصول المياه"},
    "irrigation_method": {"en": "irrigation method", "ar": "طريقة الري"},
    "irrigation_interval": {"en": "days between irrigations", "ar": "الأيام بين الريات"},
    "water_quality": {"en": "water quality", "ar": "جودة المياه"},
    "water_cost": {"en": "water cost", "ar": "تكلفة المياه"},
    "last_crop": {"en": "last crop", "ar": "آخر محصول"},
    "prev_crop": {"en": "crop before that", "ar": "المحصول السابق"},
    "bare_periods": {"en": "empty periods", "ar": "فترات ترك الأرض"},
    "pest_issues": {"en": "pest problems", "ar": "مشاكل الآفات"},
    "fertilizer_level": {"en": "fertilizer use", "ar": "استخدام الأسمدة"},
    "risk_tolerance": {"en": "openness to new crops", "ar": "الاستعداد لمحاصيل جديدة"},
    "equipment": {"en": "equipment", "ar": "المعدات"},
    "horizon": {"en": "planning horizon", "ar": "مدة التخطيط"},
    "priorities": {"en": "priorities", "ar": "الأولويات"},
}

TEXTURES = {"clay": {"en": "clay", "ar": "طينية"}, "loam": {"en": "loamy", "ar": "طميية"},
            "sandy": {"en": "sandy", "ar": "رملية"}, "mixed": {"en": "mixed", "ar": "مختلطة"}}

STRATEGY_NAMES = {
    "current": {"en": "Your current rotation", "ar": "دورتك الحالية"},
    "practice": {"en": "Same crops, better practices", "ar": "نفس المحاصيل بممارسات أفضل"},
    "soil": {"en": "Soil-building rotation", "ar": "دورة لتحسين التربة"},
    "water": {"en": "Water-saving rotation", "ar": "دورة لتوفير المياه"},
    "income": {"en": "Income-focused rotation", "ar": "دورة لزيادة الدخل"},
    "fodder": {"en": "Fodder-focused rotation", "ar": "دورة للأعلاف"},
    "balanced": {"en": "Best match for your priorities", "ar": "الأنسب لأولوياتك"},
    "custom": {"en": "Your chosen crop", "ar": "المحصول الذي اخترته"},
}

T: dict[str, dict[str, str]] = {
    # evidence
    "water_total": {"en": "This rotation needs about {m3} m³ of irrigation water per feddan per year.",
                    "ar": "تحتاج هذه الدورة إلى حوالي {m3} متر مكعب من مياه الري للفدان في السنة."},
    "water_less": {"en": "That is about {pct}% less water than your current rotation.",
                   "ar": "أي أقل بحوالي {pct}% من مياه دورتك الحالية."},
    "water_more": {"en": "That is about {pct}% more water than your current rotation.",
                   "ar": "أي أكثر بحوالي {pct}% من مياه دورتك الحالية."},
    "crop_water": {"en": "{crop} needs about {m3} m³ of water per feddan in {season}.",
                   "ar": "يحتاج {crop} إلى حوالي {m3} متر مكعب من المياه للفدان في {season}."},
    "heat_days": {"en": "{crop} faces about {days} days a year above {thr}°C at its most sensitive stage.",
                  "ar": "يتعرض {crop} لحوالي {days} يوماً في السنة فوق {thr} درجة مئوية في أكثر مراحله حساسية."},
    "bare_days": {"en": "The field stays empty about {days} days a year.",
                  "ar": "تبقى الأرض فارغة حوالي {days} يوماً في السنة."},
    "n_fixing": {"en": "{crop} adds nitrogen to the soil from the air.",
                 "ar": "يضيف {crop} النيتروجين إلى التربة من الهواء."},
    "gaez": {"en": "Estimated suitability of {crop} for this area: {score} out of 100.",
             "ar": "مدى ملاءمة {crop} لهذه المنطقة تقديرياً: {score} من 100."},
    "practice_laser_leveling": {
        "en": "Laser land levelling: fields levelled this way are reported to use about {low}–{high}% less irrigation water. We count only {low}%.",
        "ar": "تسوية الأرض بالليزر: تشير التقارير إلى أن الحقول المسواة بهذه الطريقة تستهلك مياه ري أقل بحوالي {low}–{high}%. احتسبنا {low}% فقط."},
    "practice_raised_beds": {
        "en": "Raised-bed wheat: planting wheat on beds is reported to use about {low}–{high}% less irrigation water. We count only {low}%.",
        "ar": "زراعة القمح على مصاطب: تشير التقارير إلى أنها تستهلك مياه ري أقل بحوالي {low}–{high}%. احتسبنا {low}% فقط."},
    "practice_awd_rice": {
        "en": "Alternate wetting and drying for rice: letting the field dry briefly between floodings is reported to use about {low}–{high}% less water. We count only {low}%.",
        "ar": "الري بالتبادل للأرز: ترك الحقل يجف قليلاً بين الريات يستهلك مياهاً أقل بحوالي {low}–{high}% حسب التقارير. احتسبنا {low}% فقط."},
    "pest_break": {"en": "{crop} after {prev} breaks the pest and disease cycle.",
                   "ar": "زراعة {crop} بعد {prev} تكسر دورة الآفات والأمراض."},
    "ndvi_bare": {"en": "Satellite images show the field bare about {days} days a year.",
                  "ar": "تُظهر صور الأقمار الصناعية أن الأرض تبقى فارغة حوالي {days} يوماً في السنة."},
    # benefits
    "familiar": {"en": "You already know how to grow these crops.",
                 "ar": "أنت تعرف بالفعل كيف تزرع هذه المحاصيل."},
    "govt_buyer": {"en": "{crop} has a government or contract buyer.",
                   "ar": "يوجد مشترٍ حكومي أو بعقد لمحصول {crop}."},
    "saves_water": {"en": "Saves about {m3} m³ of water per feddan per year compared with your current rotation.",
                    "ar": "يوفر حوالي {m3} متر مكعب من المياه للفدان في السنة مقارنة بدورتك الحالية."},
    "builds_soil": {"en": "Adds nitrogen and organic matter, so the soil gets richer over time.",
                    "ar": "يضيف النيتروجين والمادة العضوية فتتحسن التربة مع الوقت."},
    "forage": {"en": "{crop} gives fodder for animals.", "ar": "يوفر {crop} علفاً للحيوانات."},
    "more_income": {"en": "Higher expected income than your current rotation (rough estimate).",
                    "ar": "دخل متوقع أعلى من دورتك الحالية (تقدير تقريبي)."},
    "fewer_bare_days": {"en": "Leaves the field empty about {days} fewer days a year.",
                        "ar": "تقل أيام ترك الأرض فارغة بحوالي {days} يوماً في السنة."},
    "lower_cost": {"en": "Lower input costs, mainly less fertilizer.",
                   "ar": "تكاليف مدخلات أقل، خاصة الأسمدة."},
    "less_heat": {"en": "Fewer days of heat stress than your current rotation.",
                  "ar": "أيام إجهاد حراري أقل من دورتك الحالية."},
    # gaps
    "practice_values_unverified": {"en": "Water savings from these practices are general reported ranges, not measured on your field yet.",
                                   "ar": "توفير المياه من هذه الممارسات نطاقات عامة منشورة، ولم يُقس في حقلك بعد."},
    "practice_awd_rice_skipped_salt": {"en": "Alternate wetting and drying for rice was left out because you reported salt: letting the field dry can bring salt up.",
                                       "ar": "لم نقترح الري بالتبادل للأرز لأنك ذكرت وجود ملوحة: جفاف الحقل قد يرفع الأملاح إلى السطح."},
    "unknown_answers": {"en": "Some answers were skipped: {items}.", "ar": "بعض الأسئلة لم تتم الإجابة عنها: {items}."},
    "no_soil_test": {"en": "There is no soil test, so soil nutrients are estimated.",
                     "ar": "لا يوجد تحليل للتربة، لذلك تم تقدير عناصر التربة."},
    "crop_values_unverified": {"en": "Crop values are general estimates for the Nile Delta and have not been checked locally yet.",
                               "ar": "قيم المحاصيل تقديرات عامة لدلتا النيل ولم يتم التحقق منها محلياً بعد."},
    "income_rough": {"en": "Income is a rough comparison, not a price forecast.",
                     "ar": "الدخل مقارنة تقريبية وليس توقعاً للأسعار."},
    "climate_fallback": {"en": "NASA climate data could not be loaded, so approximate climate averages were used.",
                         "ar": "تعذر تحميل بيانات المناخ من ناسا، لذلك استُخدمت متوسطات مناخية تقريبية."},
    "ndvi_unavailable": {"en": "Satellite crop images (NDVI) were not used for this field yet.",
                         "ar": "لم تُستخدم صور الأقمار الصناعية للمحاصيل (مؤشر الخضرة) لهذا الحقل بعد."},
    "ndvi_mismatch": {"en": "Satellite images show no {season} crop last season, but you reported {crop}.",
                      "ar": "لا تُظهر صور الأقمار الصناعية محصولاً في {season} الموسم الماضي، لكنك ذكرت {crop}."},
    "history_assumed": {"en": "Your crop history was not given, so we assumed the common local rotation: {crops}.",
                        "ar": "لم تُذكر المحاصيل السابقة، لذلك افترضنا الدورة الشائعة في المنطقة: {crops}."},
    "history_unsupported": {"en": "Your last crop ({crop}) is not in our crop table, so your current rotation is partly assumed.",
                            "ar": "آخر محصول لك ({crop}) غير موجود في جدول المحاصيل لدينا، لذلك تم افتراض جزء من دورتك الحالية."},
    # risks
    "salt_sensitive": {"en": "{crop} is sensitive to salt, and you reported salt problems.",
                       "ar": "{crop} حساس للملوحة، وقد ذكرت وجود مشاكل ملوحة."},
    "water_unreliable": {"en": "{crop} needs a lot of water, and your water does not always arrive on time.",
                         "ar": "يحتاج {crop} إلى مياه كثيرة، ومياهك لا تصل دائماً في موعدها."},
    "heat_rising": {"en": "Very hot days (above 35°C) are rising by about {per_decade} days every 10 years here.",
                    "ar": "الأيام شديدة الحرارة (فوق 35 درجة) تزداد هنا بحوالي {per_decade} يوماً كل 10 سنوات."},
    "heat_exposure": {"en": "{crop} may be hurt by heat: about {days} hot days a year at its sensitive stage.",
                      "ar": "قد يتضرر {crop} من الحرارة: حوالي {days} يوماً حاراً في السنة في مرحلته الحساسة."},
    "rice_regulated": {"en": "Rice is only allowed in approved areas; check that your field is in one.",
                       "ar": "زراعة الأرز مسموحة فقط في المناطق المحددة؛ تأكد أن حقلك ضمنها."},
    "new_crop": {"en": "{crop} would be new for you; try it on part of the field first.",
                 "ar": "{crop} سيكون محصولاً جديداً عليك؛ جربه في جزء من الحقل أولاً."},
    "price_swings": {"en": "{crop} prices change a lot from year to year.",
                     "ar": "أسعار {crop} تتغير كثيراً من سنة لأخرى."},
    "tight_transition": {"en": "Very little time between harvesting {crop_a} and planting {crop_b}.",
                         "ar": "الوقت قصير جداً بين حصاد {crop_a} وزراعة {crop_b}."},
    "waterlogging": {"en": "{crop} does not like waterlogged soil, and your field drains slowly.",
                     "ar": "{crop} لا يتحمل تشبع التربة بالمياه، وصرف حقلك بطيء."},
    "soil_fit_poor": {"en": "{crop} does not grow well in {texture} soil.",
                      "ar": "{crop} لا ينمو جيداً في التربة ال{texture}."},
    "monoculture": {"en": "Growing {crop} every {season} lets pests and diseases build up.",
                    "ar": "زراعة {crop} في كل {season} تسمح بتراكم الآفات والأمراض."},
    "needs_machinery": {"en": "{crop} usually needs machinery, and you reported hand labor only.",
                        "ar": "يحتاج {crop} عادة إلى آلات، وقد ذكرت أنك تعتمد على العمل اليدوي فقط."},
    "cereal_after_cereal": {"en": "Several cereals in a row can tire the soil and carry over pests.",
                            "ar": "زراعة الحبوب وراء بعضها قد تُجهد التربة وتنقل الآفات."},
    "practice_laser_leveling_service": {"en": "Laser levelling needs a tractor and a laser unit, usually hired as a service.",
                                        "ar": "تسوية الأرض بالليزر تحتاج إلى جرار وجهاز ليزر، وعادة تُستأجر كخدمة."},
    "practice_raised_beds_service": {"en": "Raised beds need a bed-forming planter, which you may need to hire.",
                                     "ar": "زراعة المصاطب تحتاج إلى آلة تشكيل مصاطب، وقد تحتاج إلى استئجارها."},
    "practice_awd_rice_care": {"en": "With alternate wetting and drying, keep the field flooded during flowering, and check the water level before each irrigation.",
                               "ar": "عند الري بالتبادل، حافظ على غمر الحقل وقت التزهير، وافحص مستوى المياه قبل كل رية."},
    # data quality notes
    "note_climate_resolution": {"en": "Climate data covers an area of about 50 km, so it describes the local climate, not your exact field.",
                                "ar": "بيانات المناخ تغطي مساحة حوالي 50 كم، لذا فهي تصف مناخ المنطقة وليس حقلك بالتحديد."},
    "note_fallback_heat": {"en": "Approximate averages smooth out heat waves, so heat risk may be underestimated.",
                           "ar": "المتوسطات التقريبية لا تُظهر موجات الحر، لذلك قد يكون خطر الحرارة أعلى مما يظهر."},
    "note_interpolated": {"en": "About {pct}% of the satellite record was filled in because of clouds.",
                          "ar": "حوالي {pct}% من سجل الأقمار الصناعية تم استكماله بسبب السحب."},
    "note_mock_layers": {"en": "Some layers are demo values, not real measurements: {layers}.",
                         "ar": "بعض الطبقات قيم تجريبية وليست قياسات حقيقية: {layers}."},
    "note_scenario": {"en": "Scenario: {temp}°C hotter and {rain}% of normal rainfall.",
                      "ar": "سيناريو: أعلى حرارة بمقدار {temp} درجة ومطر بنسبة {rain}% من المعتاد."},
    # narrative scaffolding
    "overview": {"en": "We compared {n} crop rotations for your {area} feddan field, using NASA climate data and your answers. The best match for your priorities ({priorities}) is: {best}.",
                 "ar": "قارنّا {n} دورات زراعية لحقلك ومساحته {area} فدان، باستخدام بيانات المناخ من ناسا وإجاباتك. الأنسب لأولوياتك ({priorities}) هي: {best}."},
    "overview_fallback_climate": {"en": "We compared {n} crop rotations for your {area} feddan field, using approximate climate averages and your answers. The best match for your priorities ({priorities}) is: {best}.",
                                  "ar": "قارنّا {n} دورات زراعية لحقلك ومساحته {area} فدان، باستخدام متوسطات مناخية تقريبية وإجاباتك. الأنسب لأولوياتك ({priorities}) هي: {best}."},
    "summary": {"en": "{name}: {sequence}. Overall score {overall} out of 100, confidence {confidence}.",
                "ar": "{name}: {sequence}. الدرجة الكلية {overall} من 100، ودرجة الثقة {confidence}."},
    "why_current": {"en": "This is what you grow now. We use it as the starting point for comparison.",
                    "ar": "هذا ما تزرعه الآن، ونستخدمه كنقطة بداية للمقارنة."},
    "why_practice": {"en": "Suggested because it keeps the crops you know and saves water by changing how they are grown.",
                     "ar": "مقترحة لأنها تحافظ على المحاصيل التي تعرفها وتوفر المياه بتغيير طريقة زراعتها."},
    "why_soil": {"en": "Suggested because it improves the soil the most.", "ar": "مقترحة لأنها تحسن التربة أكثر من غيرها."},
    "why_water": {"en": "Suggested because it uses the least water.", "ar": "مقترحة لأنها تستهلك أقل كمية من المياه."},
    "why_income": {"en": "Suggested because it has the highest expected income.", "ar": "مقترحة لأن دخلها المتوقع هو الأعلى."},
    "why_fodder": {"en": "Suggested because it gives the most fodder for animals.", "ar": "مقترحة لأنها توفر أكبر كمية من العلف."},
    "why_balanced": {"en": "Suggested because it scores best on the priorities you chose.", "ar": "مقترحة لأنها تحقق أعلى درجة في الأولويات التي اخترتها."},
    "why_custom": {"en": "This is the crop you chose, scored the same way as the other options.", "ar": "هذا هو المحصول الذي اخترته، وتم تقييمه بنفس طريقة الخيارات الأخرى."},
    "reminder": {"en": "These options support your own judgment. Please review them with a local agricultural expert before deciding.",
                 "ar": "هذه الخيارات تساعدك في اتخاذ قرارك ولا تحل محله. يرجى مراجعتها مع مهندس زراعي محلي قبل اتخاذ القرار."},
}

CONFIDENCE_NAMES = {"high": {"en": "high", "ar": "عالية"}, "medium": {"en": "medium", "ar": "متوسطة"},
                    "low": {"en": "low", "ar": "منخفضة"}}


def crop_name(crop_id: str, lang: str) -> str:
    if crop_id == "fallow":
        return FALLOW[lang]
    c = CROPS.get(crop_id)
    if not c:
        return crop_id.replace("_", " ")
    return c["name_ar"] if lang == "ar" else c["name_en"]


def _localize(key: str, value: Any, lang: str) -> Any:
    if key.startswith("crop") or key == "prev":
        return crop_name(str(value), lang)
    if key == "season":
        return SEASONS.get(value, {}).get(lang, value)
    if key == "texture":
        return TEXTURES.get(value, {}).get(lang, value)
    if key == "items" and isinstance(value, list):
        sep = "، " if lang == "ar" else ", "
        return sep.join(QUESTION_NAMES.get(v, {}).get(lang, v) for v in value)
    if key == "priorities" and isinstance(value, list):
        sep = "، " if lang == "ar" else ", "
        return sep.join(PRIORITY_NAMES.get(v, {}).get(lang, v) for v in value)
    if key == "crops" and isinstance(value, list):
        return (" ثم " if lang == "ar" else " then ").join(crop_name(c, lang) for c in value)
    if key == "layers" and isinstance(value, list):
        return ", ".join(value)
    if isinstance(value, float):
        return f"{value:g}"
    return value


def render(code: str, params: dict[str, Any] | None = None, lang: str = "en") -> str:
    tpl = T[code][lang]
    p = {k: _localize(k, v, lang) for k, v in (params or {}).items()}
    return tpl.format(**p)


def fact(code: str, **params: Any) -> Fact:
    return Fact(code=code, params=params, text=render(code, params, "en"), text_ar=render(code, params, "ar"))


def sequence_text(slots: list[tuple[str, str]], lang: str) -> str:
    parts = [f"{crop_name(c, lang)} ({SEASONS[s][lang]})" for s, c in slots]
    return (" ← " if lang == "ar" else " → ").join(parts)
