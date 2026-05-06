"""Freeform address search via Nominatim. Cached per query.

Nominatim ToS: identify yourself with User-Agent, keep rate under 1 req/s.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "agri-location-intel/0.2 (personal tool)"
CACHE_PATH = Path(".cache/geocode_search.json")


def search(query: str, limit: int = 5) -> list[dict]:
    """Return list of {display_name, lat, lng} matches for a freeform query."""
    cache = _load_cache()
    if query in cache:
        return cache[query]

    resp = requests.get(
        NOMINATIM_URL,
        params={
            "q": query,
            "format": "json",
            "limit": limit,
            "countrycodes": "in",
            "addressdetails": 1,
        },
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    time.sleep(1.0)  # Nominatim rate limit
    resp.raise_for_status()
    results = [
        {
            "display_name": h.get("display_name", ""),
            "lat": float(h["lat"]),
            "lng": float(h["lon"]),
        }
        for h in resp.json()
    ]
    cache[query] = results
    _save_cache(cache)
    return results


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text())
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2))
