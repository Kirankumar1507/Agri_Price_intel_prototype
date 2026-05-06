"""7-day local forecast via Open-Meteo (No API key required)."""
import requests
import json
from pathlib import Path
from datetime import datetime, timedelta

CACHE_DIR = Path(".cache/weather")

def fetch_forecast(lat: float, lng: float) -> dict | None:
    """Return 7-day daily forecast for the given coordinates."""
    # Round to 2 decimal places for cache efficiency (~1.1km precision)
    lat_r, lng_r = round(lat, 2), round(lng, 2)
    key = f"{lat_r}_{lng_r}.json"
    
    cached = _read_cache(key)
    if cached:
        return cached

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lng,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "Asia/Kolkata",
        "forecast_days": 7
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("daily", {})
        _write_cache(key, data)
        return data
    except Exception:
        return None

def _read_cache(key: str) -> dict | None:
    path = CACHE_DIR / key
    if not path.exists():
        return None
    # 6 hour cache TTL
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    if age > timedelta(hours=6):
        return None
    return json.loads(path.read_text())

def _write_cache(key: str, data: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / key).write_text(json.dumps(data))
