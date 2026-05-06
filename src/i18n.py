"""Tiny translation table for high-frequency UI labels.

Scope: only labels that appear repeatedly + the verdict vocabulary. The longer
LLM-generated content (market overview, scheme rewrites, headline) is translated
at the model layer by passing `language=` into `_chat()` in agent.py.

Languages: en (English), kn (Kannada — for Karnataka), hi (Hindi — for Haryana).

Default language is en. UI exposes a sidebar toggle; analyze_market() and the
LLM helpers receive the chosen code.

Untranslated keys fall back to English silently.
"""
from __future__ import annotations

LANGUAGES = {
    "en": "English",
    "kn": "ಕನ್ನಡ",
    "hi": "हिन्दी",
}

# Suggest local language by default given the selected state. Sticky once
# the user overrides.
STATE_DEFAULT_LANG = {
    "Karnataka": "kn",
    "Haryana": "hi",
}

# Flat dict: LABELS[key][lang_code] → string. Missing → English fallback.
LABELS: dict[str, dict[str, str]] = {
    # Sidebar
    "sidebar.scope": {
        "en": "Scope", "kn": "ಆಯ್ಕೆ", "hi": "विकल्प",
    },
    "sidebar.state": {
        "en": "State", "kn": "ರಾಜ್ಯ", "hi": "राज्य",
    },
    "sidebar.crop": {
        "en": "Crop", "kn": "ಬೆಳೆ", "hi": "फसल",
    },
    "sidebar.location": {
        "en": "Your location", "kn": "ನಿಮ್ಮ ಸ್ಥಳ", "hi": "आपका स्थान",
    },
    "sidebar.address_input": {
        "en": "Search address / village / landmark",
        "kn": "ವಿಳಾಸ / ಗ್ರಾಮ / ಗುರುತು ಹುಡುಕಿ",
        "hi": "पता / गाँव / निशानी खोजें",
    },
    "sidebar.search": {
        "en": "Search", "kn": "ಹುಡುಕಿ", "hi": "खोजें",
    },
    "sidebar.searching": {
        "en": "Looking up address...",
        "kn": "ವಿಳಾಸವನ್ನು ಹುಡುಕಲಾಗುತ್ತಿದೆ...",
        "hi": "पता खोजा जा रहा है...",
    },
    "sidebar.pick_one": {
        "en": "Pick one:", "kn": "ಒಂದನ್ನು ಆಯ್ಕೆಮಾಡಿ:", "hi": "एक चुनें:",
    },
    "sidebar.no_matches": {
        "en": "No matches.", "kn": "ಯಾವುದೇ ಹೊಂದಾಣಿಕೆ ಇಲ್ಲ.", "hi": "कोई मेल नहीं।",
    },
    "sidebar.get_intel": {
        "en": "Get market intelligence",
        "kn": "ಮಾರುಕಟ್ಟೆ ಮಾಹಿತಿ ಪಡೆಯಿರಿ",
        "hi": "बाज़ार जानकारी पाएँ",
    },
    "sidebar.language": {
        "en": "Language", "kn": "ಭಾಷೆ", "hi": "भाषा",
    },

    # Hero
    "hero.what": {
        "en": "What this does",
        "kn": "ಇದು ಏನು ಮಾಡುತ್ತದೆ",
        "hi": "यह क्या करता है",
    },
    "hero.demo_button": {
        "en": "Try demo — Ragi from Bengaluru, KA",
        "kn": "ಪ್ರಯತ್ನಿಸಿ — ಬೆಂಗಳೂರು, ಕರ್ನಾಟಕದಿಂದ ರಾಗಿ",
        "hi": "डेमो आज़माएँ — बेंगलुरु, कर्नाटक से रागी",
    },

    # Answer row
    "answer.title": {
        "en": "Your answer", "kn": "ನಿಮ್ಮ ಉತ್ತರ", "hi": "आपका जवाब",
    },
    "answer.best_mandi": {
        "en": "Best mandi", "kn": "ಉತ್ತಮ ಮಂಡಿ", "hi": "सबसे अच्छी मंडी",
    },
    "answer.distance": {
        "en": "Distance", "kn": "ದೂರ", "hi": "दूरी",
    },
    "answer.modal_price": {
        "en": "Modal price", "kn": "ಪ್ರಮುಖ ಬೆಲೆ", "hi": "मॉडल भाव",
    },
    "answer.net_price": {
        "en": "Net ₹/qtl", "kn": "ನಿವ್ವಳ ₹/ಕ್ವಿಂಟಾಲ್", "hi": "शुद्ध ₹/क्विंटल",
    },

    # Verdict labels
    "verdict.sell_now": {
        "en": "Sell now", "kn": "ಈಗ ಮಾರಿ", "hi": "अभी बेचें",
    },
    "verdict.store": {
        "en": "Store", "kn": "ಸಂಗ್ರಹಿಸಿ", "hi": "रोक लीजिए",
    },
    "verdict.travel": {
        "en": "Travel", "kn": "ಪ್ರಯಾಣಿಸಿ", "hi": "जाइए",
    },
    "verdict.wait": {
        "en": "Wait", "kn": "ನಿರೀಕ್ಷಿಸಿ", "hi": "रुकिए",
    },
    "verdict.verify": {
        "en": "Verify locally",
        "kn": "ಸ್ಥಳೀಯವಾಗಿ ಪರಿಶೀಲಿಸಿ",
        "hi": "स्थानीय जाँच कीजिए",
    },
    "verdict.confidence": {
        "en": "CONFIDENCE", "kn": "ವಿಶ್ವಾಸ", "hi": "विश्वास",
    },

    # Tabs
    "tab.market_intel": {
        "en": "Market intel", "kn": "ಮಾರುಕಟ್ಟೆ ಒಳನೋಟ", "hi": "बाज़ार सूचना",
    },
    "tab.production": {
        "en": "Production (APY)",
        "kn": "ಉತ್ಪಾದನೆ (ಎಪಿವೈ)",
        "hi": "उत्पादन (APY)",
    },
    "tab.about_schemes": {
        "en": "About {crop} & schemes",
        "kn": "{crop} ಮತ್ತು ಯೋಜನೆಗಳ ಬಗ್ಗೆ",
        "hi": "{crop} और योजनाएँ",
    },
    "tab.weather": {
        "en": "Weather & climate",
        "kn": "ಹವಾಮಾನ",
        "hi": "मौसम",
    },

    # Weather tab — climate strip + forecast + calendar
    "weather.climate_signal": {
        "en": "Climate signal",
        "kn": "ಹವಾಮಾನ ಸಂಕೇತ",
        "hi": "जलवायु संकेत",
    },
    "weather.enso": {
        "en": "ENSO", "kn": "ಎನ್‌ಸೋ", "hi": "ENSO",
    },
    "weather.iod": {
        "en": "IOD", "kn": "ಐಒಡಿ", "hi": "IOD",
    },
    "weather.unavailable": {
        "en": "data unavailable",
        "kn": "ದತ್ತಾಂಶ ಲಭ್ಯವಿಲ್ಲ",
        "hi": "डेटा उपलब्ध नहीं",
    },
    "weather.forecast_title": {
        "en": "7-day forecast", "kn": "7-ದಿನಗಳ ಮುನ್ಸೂಚನೆ", "hi": "7-दिन का पूर्वानुमान",
    },
    "weather.calendar_title": {
        "en": "Crop calendar — {crop} in {state}",
        "kn": "{state}ದಲ್ಲಿ {crop} ಬೆಳೆ ಕ್ಯಾಲೆಂಡರ್",
        "hi": "{state} में {crop} फसल कैलेंडर",
    },
    "weather.cal_sow": {
        "en": "Sow", "kn": "ಬಿತ್ತನೆ", "hi": "बुआई",
    },
    "weather.cal_transplant": {
        "en": "Transplant", "kn": "ನಾಟಿ", "hi": "रोपण",
    },
    "weather.cal_harvest": {
        "en": "Harvest", "kn": "ಕೊಯ್ಲು", "hi": "कटाई",
    },
    "weather.cal_critical": {
        "en": "Critical weather", "kn": "ಪ್ರಮುಖ ಹವಾಮಾನ", "hi": "महत्वपूर्ण मौसम",
    },
    "weather.location_needed": {
        "en": "Pick a location in the sidebar to see forecast for your spot.",
        "kn": "ಮುನ್ಸೂಚನೆ ನೋಡಲು ಸೈಡ್‌ಬಾರ್‌ನಲ್ಲಿ ಸ್ಥಳ ಆಯ್ಕೆಮಾಡಿ.",
        "hi": "अपने स्थान का पूर्वानुमान देखने के लिए साइडबार में स्थान चुनें।",
    },
    "weather.no_calendar": {
        "en": "No calendar entry curated yet for this crop+state pair.",
        "kn": "ಈ ಬೆಳೆ-ರಾಜ್ಯ ಜೋಡಿಗೆ ಕ್ಯಾಲೆಂಡರ್ ಇನ್ನೂ ಲಭ್ಯವಿಲ್ಲ.",
        "hi": "इस फसल-राज्य जोड़ी के लिए कैलेंडर अभी उपलब्ध नहीं।",
    },
}


def t(key: str, lang: str, **fmt) -> str:
    """Look up a translation, falling back to English. Optional .format(**fmt)."""
    label = LABELS.get(key, {}).get(lang) or LABELS.get(key, {}).get("en") or key
    if fmt:
        try:
            return label.format(**fmt)
        except (KeyError, IndexError):
            return label
    return label
