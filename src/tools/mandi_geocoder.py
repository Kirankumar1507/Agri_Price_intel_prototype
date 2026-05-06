"""Cached geocoding for mandis — via their DISTRICT centroid (not specific address).

Why district centroid, not mandi-specific:
- Nominatim doesn't index mandi names (APMC, Mandi, Yard, Grain Market).
- Mandi-specific geocoding had ~10% hit rate in tests.
- District centroid always resolves (admin-level entry in OSM).
- For "is this mandi near me" the error (±20 km) is acceptable for a demo.

Caveat: all mandis in a district share coords, so the map pins overlap.
Phase 2 can layer a hand-curated lat/lng file for APMCs that matter.

First query per state: 1 Nominatim call per unique district (~22 for HY, ~31 for KA).
Cached in .cache/mandi_coords.json and reused forever.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import requests

CACHE_PATH = Path("data/mandi_coords.json")
USER_AGENT = "agri-location-intel/0.2 (personal tool)"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def geocode_mandis(mandis: list[dict], state: str) -> dict[str, tuple[float, float]]:
    """For [{market, district}, ...] return {market: (lat, lng)} using district centroids."""
    cache = _load_cache()
    unique_districts = {m["district"] for m in mandis if m.get("district")}

    dirty = False
    for district in unique_districts:
        key = f"DISTRICT|{district}|{state}"
        if key in cache:
            continue
        coords = _geocode_district(district, state)
        cache[key] = list(coords) if coords else None
        dirty = True
    if dirty:
        _save_cache(cache)

    out: dict[str, tuple[float, float]] = {}
    for m in mandis:
        district = m.get("district")
        market = m.get("market")
        if not (district and market):
            continue
        key = f"DISTRICT|{district}|{state}"
        val = cache.get(key)
        if val:
            out[market] = (val[0], val[1])
    return out


def _geocode_district(district: str, state: str) -> tuple[float, float] | None:
    q = f"{district} district, {state}, India"
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"q": q, "format": "json", "limit": 1, "countrycodes": "in"},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        time.sleep(1.0)
        if resp.status_code != 200:
            return None
        hits = resp.json()
        if not hits:
            # Fallback without "district"
            resp2 = requests.get(
                NOMINATIM_URL,
                params={
                    "q": f"{district}, {state}, India",
                    "format": "json",
                    "limit": 1,
                    "countrycodes": "in",
                },
                headers={"User-Agent": USER_AGENT},
                timeout=15,
            )
            time.sleep(1.0)
            hits = resp2.json() if resp2.status_code == 200 else []
        if not hits:
            return None
        return (float(hits[0]["lat"]), float(hits[0]["lon"]))
    except Exception:
        return None


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text())
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2))
