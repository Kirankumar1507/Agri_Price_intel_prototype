"""Bilingual UI labels for English, Kannada (KA), and Hindi (HY)."""

LANGUAGES = {
    "en": "English",
    "kn": "ಕನ್ನಡ (Kannada)",
    "hi": "हिन्दी (Hindi)"
}

STATE_DEFAULT_LANG = {
    "Karnataka": "kn",
    "Haryana": "hi"
}

LABELS = {
    "sidebar.language": {
        "en": "Language",
        "kn": "ಭಾಷೆ",
        "hi": "भाषा"
    },
    "sidebar.scope": {
        "en": "Scope",
        "kn": "ವ್ಯಾಪ್ತಿ",
        "hi": "कार्यಕ್ಷೇತ್ರ"
    },
    "sidebar.state": {
        "en": "Select State",
        "kn": "ರಾಜ್ಯವನ್ನು ಆಯ್ಕೆ ಮಾಡಿ",
        "hi": "राज्य चुनें"
    },
    "sidebar.crop": {
        "en": "Select Crop",
        "kn": "ಬೆಳೆಯನ್ನು ಆಯ್ಕೆ ಮಾಡಿ",
        "hi": "फसल चुनें"
    },
    "sidebar.location": {
        "en": "Your Location",
        "kn": "ನಿಮ್ಮ ಸ್ಥಳ",
        "hi": "आपका स्थान"
    },
    "sidebar.get_intel": {
        "en": "Get Market Intelligence",
        "kn": "ಮಾರುಕಟ್ಟೆ ಮಾಹಿತಿ ಪಡೆಯಿರಿ",
        "hi": "बाजार की जानकारी प्राप्त करें"
    },
    "hero.what": {
        "en": "What is this?",
        "kn": "ಇದು ಏನು?",
        "hi": "यह क्या है?"
    },
    "verdict.headline": {
        "en": "Recommendation",
        "kn": "ಶಿಫಾರಸು",
        "hi": "सिफारिश"
    },
    "tab.weather": {
        "en": "Weather & Climate",
        "kn": "ಹವಾಮಾನ",
        "hi": "मौसम और जलवायु"
    },
    "weather.forecast": {
        "en": "7-Day Forecast",
        "kn": "7 ದಿನಗಳ ಮುನ್ಸೂಚನೆ",
        "hi": "7-दिवसीय पूर्वानुमान"
    },
    "weather.calendar": {
        "en": "Crop Calendar",
        "kn": "ಬೆಳೆ ಕ್ಯಾಲೆಂಡರ್",
        "hi": "फसल कैलेंडर"
    },
    "tab.news": {
        "en": "News & Advisories",
        "kn": "ಸುದ್ದಿ ಮತ್ತು ಸಲಹೆಗಳು",
        "hi": "समाचार और परामर्श"
    },
    "verdict.hear": {
        "en": "🔊 Hear the recommendation",
        "kn": "🔊 ಶಿಫಾರಸನ್ನು ಕೇಳಿ",
        "hi": "🔊 सिफारिश सुनें"
    },

    # --- Verdict labels (used by _VERDICT_STYLE) + confidence ---
    "verdict.sell_now": {"en": "Sell now", "kn": "ಈಗ ಮಾರಿ", "hi": "अभी बेचें"},
    "verdict.store":    {"en": "Store", "kn": "ಸಂಗ್ರಹಿಸಿ", "hi": "भंडारण करें"},
    "verdict.travel":   {"en": "Travel", "kn": "ಪ್ರಯಾಣಿಸಿ", "hi": "यात्रा करें"},
    "verdict.wait":     {"en": "Wait", "kn": "ಕಾಯಿರಿ", "hi": "प्रतीक्षा करें"},
    "verdict.verify":   {"en": "Verify", "kn": "ಪರಿಶೀಲಿಸಿ", "hi": "सत्यापित करें"},
    "verdict.confidence": {"en": "Confidence", "kn": "ವಿಶ್ವಾಸ", "hi": "विश्वास"},

    # --- Answer / metric row ---
    "answer.title":       {"en": "Your market answer", "kn": "ನಿಮ್ಮ ಮಾರುಕಟ್ಟೆ ಉತ್ತರ", "hi": "आपका बाज़ार उत्तर"},
    "answer.best_mandi":  {"en": "Best mandi", "kn": "ಅತ್ಯುತ್ತಮ ಮಂಡಿ", "hi": "सर्वोत्तम मंडी"},
    "answer.distance":    {"en": "Distance", "kn": "ದೂರ", "hi": "दूरी"},
    "answer.modal_price": {"en": "Modal price", "kn": "ಸಾಮಾನ್ಯ ಬೆಲೆ", "hi": "मॉडल मूल्य"},
    "answer.net_price":   {"en": "Net price (after transport)", "kn": "ನಿವ್ವಳ ಬೆಲೆ (ಸಾಗಣೆ ನಂತರ)", "hi": "शुद्ध मूल्य (परिवहन के बाद)"},

    # --- Hero / landing ---
    "hero.demo_button": {"en": "Try a demo", "kn": "ಡೆಮೊ ಪ್ರಯತ್ನಿಸಿ", "hi": "डेमो आज़माएँ"},
    "hero.pitch": {
        "en": "Pick a state, crop, and village in the sidebar → get the best APMC mandi "
              "(highest net ₹/qtl after ₹5/km transport), the nearest 5 options, and the "
              "government schemes that apply — in plain language.",
        "kn": "ಬದಿಪಟ್ಟಿಯಲ್ಲಿ ರಾಜ್ಯ, ಬೆಳೆ ಮತ್ತು ಗ್ರಾಮವನ್ನು ಆಯ್ಕೆ ಮಾಡಿ → ಅತ್ಯುತ್ತಮ ಎಪಿಎಂಸಿ ಮಂಡಿ "
              "(ಪ್ರತಿ ಕಿ.ಮೀ. ₹5 ಸಾಗಣೆ ನಂತರ ಅತ್ಯಧಿಕ ನಿವ್ವಳ ₹/ಕ್ವಿಂಟಲ್), ಹತ್ತಿರದ 5 ಆಯ್ಕೆಗಳು ಮತ್ತು "
              "ಅನ್ವಯವಾಗುವ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳನ್ನು — ಸರಳ ಭಾಷೆಯಲ್ಲಿ ಪಡೆಯಿರಿ.",
        "hi": "साइडबार में राज्य, फसल और गाँव चुनें → सर्वोत्तम APMC मंडी "
              "(₹5/किमी परिवहन के बाद सर्वाधिक शुद्ध ₹/क्विंटल), निकटतम 5 विकल्प और "
              "लागू सरकारी योजनाएँ — सरल भाषा में पाएँ।",
    },
    "hero.demo_caption": {
        "en": "Or use the sidebar to pick your own state, crop, and location. "
              "Data: data.gov.in Agmarknet (daily variety-wise prices).",
        "kn": "ಅಥವಾ ಬದಿಪಟ್ಟಿಯನ್ನು ಬಳಸಿ ನಿಮ್ಮ ರಾಜ್ಯ, ಬೆಳೆ ಮತ್ತು ಸ್ಥಳವನ್ನು ಆಯ್ಕೆ ಮಾಡಿ. "
              "ಡೇಟಾ: data.gov.in ಅಗ್ಮಾರ್ಕ್‌ನೆಟ್ (ದೈನಂದಿನ ವೈವಿಧ್ಯ ಬೆಲೆಗಳು).",
        "hi": "या साइडबार से अपना राज्य, फसल और स्थान चुनें। "
              "डेटा: data.gov.in Agmarknet (दैनिक किस्म-वार मूल्य)।",
    },

    # --- Sidebar ---
    "sidebar.address_input": {"en": "Village / town", "kn": "ಗ್ರಾಮ / ಪಟ್ಟಣ", "hi": "गाँव / शहर"},
    "sidebar.search":        {"en": "Search", "kn": "ಹುಡುಕಿ", "hi": "खोजें"},
    "sidebar.searching":     {"en": "Searching…", "kn": "ಹುಡುಕಲಾಗುತ್ತಿದೆ…", "hi": "खोज रहे हैं…"},
    "sidebar.pick_one":      {"en": "Pick your location", "kn": "ನಿಮ್ಮ ಸ್ಥಳವನ್ನು ಆಯ್ಕೆ ಮಾಡಿ", "hi": "अपना स्थान चुनें"},
    "sidebar.no_matches":    {"en": "No matches — try a nearby town.", "kn": "ಫಲಿತಾಂಶವಿಲ್ಲ — ಹತ್ತಿರದ ಪಟ್ಟಣವನ್ನು ಪ್ರಯತ್ನಿಸಿ.", "hi": "कोई परिणाम नहीं — पास का शहर आज़माएँ।"},
    "sidebar.warn_no_data_key": {"en": "⚠️ DATA_GOV_API_KEY missing — showing demo data only.", "kn": "⚠️ DATA_GOV_API_KEY ಇಲ್ಲ — ಡೆಮೊ ಡೇಟಾ ಮಾತ್ರ.", "hi": "⚠️ DATA_GOV_API_KEY अनुपलब्ध — केवल डेमो डेटा।"},
    "sidebar.warn_no_ai_key":   {"en": "ℹ️ GEMINI_API_KEY missing — narratives unavailable.", "kn": "ℹ️ GEMINI_API_KEY ಇಲ್ಲ — ವಿವರಣೆಗಳು ಲಭ್ಯವಿಲ್ಲ.", "hi": "ℹ️ GEMINI_API_KEY अनुपलब्ध — विवरण उपलब्ध नहीं।"},
    "sidebar.geocoder_failed":  {"en": "Location search failed. Please try again.", "kn": "ಸ್ಥಳ ಹುಡುಕಾಟ ವಿಫಲವಾಗಿದೆ. ದಯವಿಟ್ಟು ಪುನಃ ಪ್ರಯತ್ನಿಸಿ.", "hi": "स्थान खोज विफल। कृपया पुनः प्रयास करें।"},

    # --- Compute spinner ---
    "compute.spinner": {"en": "Fetching live mandi prices & analysing market trends…", "kn": "ನೇರ ಮಂಡಿ ಬೆಲೆಗಳನ್ನು ಪಡೆದು ಮಾರುಕಟ್ಟೆ ಪ್ರವೃತ್ತಿಗಳನ್ನು ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ…", "hi": "लाइव मंडी मूल्य लाकर बाज़ार रुझान का विश्लेषण किया जा रहा है…"},

    # --- Tabs ---
    "tab.market_intel":     {"en": "Market intelligence", "kn": "ಮಾರುಕಟ್ಟೆ ಮಾಹಿತಿ", "hi": "बाज़ार जानकारी"},
    "tab.production":       {"en": "Production history", "kn": "ಉತ್ಪಾದನಾ ಇತಿಹಾಸ", "hi": "उत्पादन इतिहास"},
    "tab.about_schemes":    {"en": "Schemes · {crop}", "kn": "ಯೋಜನೆಗಳು · {crop}", "hi": "योजनाएँ · {crop}"},
    "tab.production_en_only": {"en": "Production figures are shown in English for now.", "kn": "ಉತ್ಪಾದನಾ ಅಂಕಿಅಂಶಗಳನ್ನು ಸದ್ಯಕ್ಕೆ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ತೋರಿಸಲಾಗಿದೆ.", "hi": "उत्पादन आंकड़े फ़िलहाल अंग्रेज़ी में दिखाए गए हैं।"},

    # --- Weather / climate / calendar ---
    "weather.forecast_title": {"en": "7-day weather forecast", "kn": "7 ದಿನಗಳ ಹವಾಮಾನ ಮುನ್ಸೂಚನೆ", "hi": "7-दिवसीय मौसम पूर्वानुमान"},
    "weather.calendar_title": {"en": "Crop calendar — {crop}, {state}", "kn": "ಬೆಳೆ ಕ್ಯಾಲೆಂಡರ್ — {crop}, {state}", "hi": "फसल कैलेंडर — {crop}, {state}"},
    "weather.climate_signal": {"en": "Climate signals", "kn": "ಹವಾಮಾನ ಸೂಚನೆಗಳು", "hi": "जलवायु संकेत"},
    "weather.enso": {"en": "ENSO (El Niño / La Niña)", "kn": "ಎನ್‌ಸೊ (ಎಲ್ ನಿನೊ / ಲಾ ನಿನಾ)", "hi": "ईएनएसओ (एल नीनो / ला नीना)"},
    "weather.iod":  {"en": "Indian Ocean Dipole (IOD)", "kn": "ಭಾರತೀಯ ಸಾಗರ ದ್ವಿಧ್ರುವ (IOD)", "hi": "हिंद महासागर द्विध्रुव (IOD)"},
    "weather.cal_sow":        {"en": "Sowing", "kn": "ಬಿತ್ತನೆ", "hi": "बुवाई"},
    "weather.cal_transplant": {"en": "Transplant", "kn": "ನಾಟಿ", "hi": "रोपाई"},
    "weather.cal_harvest":    {"en": "Harvest", "kn": "ಕೊಯ್ಲು", "hi": "कटाई"},
    "weather.cal_critical":   {"en": "Critical", "kn": "ನಿರ್ಣಾಯಕ", "hi": "महत्वपूर्ण"},
    "weather.location_needed": {"en": "Pick a location to see the forecast.", "kn": "ಮುನ್ಸೂಚನೆ ನೋಡಲು ಸ್ಥಳವನ್ನು ಆಯ್ಕೆ ಮಾಡಿ.", "hi": "पूर्वानुमान देखने के लिए स्थान चुनें।"},
    "weather.no_calendar":    {"en": "No crop calendar for this crop yet.", "kn": "ಈ ಬೆಳೆಗೆ ಇನ್ನೂ ಕ್ಯಾಲೆಂಡರ್ ಇಲ್ಲ.", "hi": "इस फसल के लिए अभी कैलेंडर नहीं है।"},
    "weather.unavailable":    {"en": "Weather data unavailable right now.", "kn": "ಹವಾಮಾನ ಡೇಟಾ ಸದ್ಯಕ್ಕೆ ಲಭ್ಯವಿಲ್ಲ.", "hi": "मौसम डेटा अभी उपलब्ध नहीं है।"},

    # --- Honesty guard (A4b): illustrative / sample-data notices ---
    "weather.climate_illustrative": {"en": "Illustrative only — not a live feed yet.", "kn": "ಕೇವಲ ನಿದರ್ಶನಾತ್ಮಕ — ಇನ್ನೂ ನೇರ ಮೂಲವಲ್ಲ.", "hi": "केवल उदाहरण — अभी लाइव स्रोत नहीं।"},
    "news.sample_notice": {"en": "Sample advisories — live integration coming soon.", "kn": "ಮಾದರಿ ಸಲಹೆಗಳು — ನೇರ ಸಂಯೋಜನೆ ಶೀಘ್ರದಲ್ಲೇ.", "hi": "नमूना सलाह — लाइव एकीकरण जल्द आ रहा है।"},
    "answer.msp_verify": {"en": "MSP may lag the latest CACP notification — confirm the current rate at your mandi.", "kn": "ಎಂಎಸ್‌ಪಿ ಇತ್ತೀಚಿನ CACP ಅಧಿಸೂಚನೆಗಿಂತ ಹಿಂದಿರಬಹುದು — ನಿಮ್ಮ ಮಂಡಿಯಲ್ಲಿ ಪ್ರಸ್ತುತ ದರವನ್ನು ಖಚಿತಪಡಿಸಿ.", "hi": "MSP नवीनतम CACP अधिसूचना से पीछे हो सकती है — अपनी मंडी में मौजूदा दर की पुष्टि करें।"},
}

def t(key: str, lang: str = "en", **fmt) -> str:
    """Return the translated label for `key` in `lang`.

    LABELS is a FLAT dict keyed by dotted strings (e.g. "sidebar.language"),
    so look the key up directly — do NOT split and walk it as a nested tree.
    Falls back to English, then to the raw key, so a missing translation
    degrades visibly instead of crashing.

    Optional `**fmt` values are applied via str.format (e.g. t("x", lang, crop=c)
    for a label containing "{crop}"). Formatting failures degrade to the raw
    template rather than raising.
    """
    entry = LABELS.get(key)
    if not entry:
        return key
    val = entry.get(lang) or entry.get("en") or key
    if fmt:
        try:
            return val.format(**fmt)
        except (KeyError, IndexError, ValueError):
            return val
    return val
