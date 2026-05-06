"""Demo scope — states, crops, single data source (variety-wise, 90-day window)."""
from __future__ import annotations

RESOURCE_ID = "35985678-0d79-46b4-9ed6-6f13308a1d24"
APY_RESOURCE_ID = "35be999b-0208-4354-b557-f6ca9a5355de"
WINDOW_DAYS = 90
TREND_DAYS = 15

TRANSPORT_RATE_PER_KM = 5.0

# Each commodity carries three name variants:
#   api     — Agmarknet variety-wise enum (live mandi prices)
#   display — UI label (short)
#   apy     — DES APY 1997-2014 resource crop name (None if not tracked there)
STATES: dict[str, dict] = {
    "Haryana": {
        "commodities": [
            {"api": "Wheat", "display": "Wheat", "apy": "Wheat"},
            {"api": "Paddy(Dhan)(Common)", "display": "Paddy", "apy": "Rice"},
            {"api": "Mustard", "display": "Mustard", "apy": "Rapeseed &Mustard"},
            {"api": "Bajra", "display": "Bajra", "apy": "Bajra"},
            {"api": "Cotton", "display": "Cotton", "apy": "Cotton(lint)"},
            {"api": "Sugarcane", "display": "Sugarcane", "apy": "Sugarcane"},
            {"api": "Bengal Gram(Gram)(Whole)", "display": "Bengal Gram (Chana)", "apy": "Gram"},
            {"api": "Groundnut", "display": "Groundnut", "apy": "Groundnut"},
            {"api": "Onion", "display": "Onion", "apy": "Onion"},
            {"api": "Tomato", "display": "Tomato", "apy": None},
            {"api": "Potato", "display": "Potato", "apy": "Potato"},
        ],
        "map_center": [29.06, 76.12],
        "map_zoom": 7,
    },
    "Karnataka": {
        "commodities": [
            {"api": "Ragi (Finger Millet)", "display": "Ragi", "apy": "Ragi"},
            {"api": "Paddy(Dhan)(Common)", "display": "Paddy", "apy": "Rice"},
            {"api": "Arhar (Tur/Red Gram)(Whole)", "display": "Tur", "apy": "Arhar/Tur"},
            {"api": "Jowar(Sorghum)", "display": "Jowar", "apy": "Jowar"},
            {"api": "Maize", "display": "Maize", "apy": "Maize"},
            {"api": "Sugarcane", "display": "Sugarcane", "apy": "Sugarcane"},
            {"api": "Cotton", "display": "Cotton", "apy": "Cotton(lint)"},
            {"api": "Groundnut", "display": "Groundnut", "apy": "Groundnut"},
            {"api": "Bengal Gram(Gram)(Whole)", "display": "Bengal Gram (Chana)", "apy": "Gram"},
            {"api": "Green Gram (Moong)(Whole)", "display": "Green Gram (Moong)", "apy": "Moong(Green Gram)"},
            {"api": "Onion", "display": "Onion", "apy": "Onion"},
            {"api": "Tomato", "display": "Tomato", "apy": "Tomato"},
            {"api": "Potato", "display": "Potato", "apy": "Potato"},
        ],
        "map_center": [15.3173, 75.7139],
        "map_zoom": 6,
    },
}


def list_states() -> list[str]:
    return list(STATES.keys())


def commodity_display_to_api(state: str, display: str) -> str:
    for c in STATES[state]["commodities"]:
        if c["display"] == display:
            return c["api"]
    raise KeyError(f"Unknown crop {display!r} for {state}")


def commodity_display_to_apy(state: str, display: str) -> str | None:
    for c in STATES[state]["commodities"]:
        if c["display"] == display:
            return c.get("apy")
    raise KeyError(f"Unknown crop {display!r} for {state}")


def crop_displays(state: str) -> list[str]:
    return [c["display"] for c in STATES[state]["commodities"]]
