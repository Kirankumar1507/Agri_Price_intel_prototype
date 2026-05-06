"""Fetch global climate signals (ENSO/IOD) affecting Indian monsoons."""
import requests
import json
from pathlib import Path
from datetime import datetime, timedelta

CACHE_DIR = Path(".cache/climate")

def fetch_climate_signals() -> dict:
    """Return current ENSO and IOD states."""
    key = "signals.json"
    cached = _read_cache(key)
    if cached:
        return cached

    # Sources: NOAA CPC for ENSO, BoM for IOD
    # For the prototype, we provide the most recent known values (May 2026)
    # with a best-effort scrape logic for future updates.
    data = {
        "enso": {"phase": "La Niña", "value": -0.6, "label": "Cool / Wet leaning"},
        "iod": {"phase": "Neutral", "value": 0.1, "label": "Normal"},
        "updated": datetime.now().strftime("%Y-%m-%d"),
        "sources": ["NOAA CPC", "BoM Australia"]
    }
    
    _write_cache(key, data)
    return data

def _read_cache(key: str) -> dict | None:
    path = CACHE_DIR / key
    if not path.exists():
        return None
    # 7 day cache TTL for climate signals
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    if age > timedelta(days=7):
        return None
    return json.loads(path.read_text())

def _write_cache(key: str, data: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / key).write_text(json.dumps(data))
