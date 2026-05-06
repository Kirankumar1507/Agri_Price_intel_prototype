"""MSP (Minimum Support Price) lookup from curated JSON.

Data source: CACP/CCEA notifications for Marketing Season 2025-26.
Horticulture crops (Tomato, Onion, Potato) have no MSP — returns None.
"""
from __future__ import annotations

import json
from pathlib import Path

MSP_PATH = Path("data/msp_rates.json")


def get_msp(crop_display: str) -> dict | None:
    """Return {msp, season, unit, note?} for a crop, or None if no MSP exists.

    Uses the display name from config (e.g. "Ragi", "Paddy", "Wheat").
    """
    data = json.loads(MSP_PATH.read_text())
    rates = data.get("rates", {})
    entry = rates.get(crop_display)
    if entry is None:
        return None
    return entry
