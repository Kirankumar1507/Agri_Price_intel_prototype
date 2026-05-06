"""7-day local forecast from Open-Meteo. No API key, free, decent India coverage.

Single endpoint hit, JSON response. We round lat/lng to 2dp for the cache key
so a Bengaluru-ward radius doesn't fragment the cache.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import requests

CACHE_DIR = Path(".cache/weather")
CACHE_TTL_HOURS = 6
BASE_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_forecast(lat: float, lng: float) -> dict | None:
    """Return {days: [{date, tmax, tmin, precip_mm, wind_kmh, humidity_max}, ...], units}.

    None on hard failure (network, 5xx). Cached 6h per (lat_2dp, lng_2dp).
    """
    key = _cache_key(lat, lng)
    cached = _read_cache(key)
    if cached is not None:
        return cached

    try:
        resp = requests.get(
            BASE_URL,
            params={
                "latitude": round(lat, 4),
                "longitude": round(lng, 4),
                "daily": (
                    "temperature_2m_max,temperature_2m_min,"
                    "precipitation_sum,wind_speed_10m_max,relative_humidity_2m_max"
                ),
                "forecast_days": 7,
                "timezone": "Asia/Kolkata",
            },
            timeout=15,
        )
    except requests.RequestException:
        return None
    if not resp.ok:
        return None

    raw = resp.json()
    daily = raw.get("daily") or {}
    times = daily.get("time") or []
    tmax = daily.get("temperature_2m_max") or []
    tmin = daily.get("temperature_2m_min") or []
    precip = daily.get("precipitation_sum") or []
    wind = daily.get("wind_speed_10m_max") or []
    humid = daily.get("relative_humidity_2m_max") or []

    days = []
    for i, d in enumerate(times):
        days.append({
            "date": d,
            "tmax": _at(tmax, i),
            "tmin": _at(tmin, i),
            "precip_mm": _at(precip, i),
            "wind_kmh": _at(wind, i),
            "humidity_max": _at(humid, i),
        })

    out = {
        "days": days,
        "units": raw.get("daily_units") or {},
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
    }
    _write_cache(key, out)
    return out


def _at(arr, i):
    if i < len(arr):
        return arr[i]
    return None


def _cache_key(lat: float, lng: float) -> str:
    return f"forecast_{round(lat, 2)}_{round(lng, 2)}.json"


def _read_cache(key: str) -> dict | None:
    path = CACHE_DIR / key
    if not path.exists():
        return None
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    if age > timedelta(hours=CACHE_TTL_HOURS):
        return None
    return json.loads(path.read_text())


def _write_cache(key: str, data: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / key).write_text(json.dumps(data))
