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
    }
}

def t(key: str, lang: str = "en") -> str:
    """Return the translated label for the given key and language."""
    parts = key.split(".")
    obj = LABELS
    for p in parts:
        obj = obj.get(p, {})
    
    val = obj.get(lang)
    if val:
        return val
    return obj.get("en", key)
