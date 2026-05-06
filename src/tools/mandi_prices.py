"""Agmarknet variety-wise via data.gov.in. 90-day window, cached 24h per (state, commodity)."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import requests

from src.config import RESOURCE_ID, WINDOW_DAYS

CACHE_DIR = Path(".cache/mandi")
CACHE_TTL_HOURS = 24
BASE_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"


def fetch_prices(state: str, commodity_api: str, days: int = WINDOW_DAYS) -> list[dict]:
    """Return up to `days` of records for (state, commodity), newest first."""
    key = _cache_key(state, commodity_api, days)
    cached = _read_cache(key)
    if cached is not None:
        return cached

    api_key = _get_key()
    if not api_key:
        return []

    resp = requests.get(
        BASE_URL,
        params={
            "api-key": api_key,
            "format": "json",
            "limit": 2000,
            "filters[State]": state,
            "filters[Commodity]": commodity_api,
            "sort[Arrival_Date]": "desc",
        },
        timeout=120,
    )
    resp.raise_for_status()
    raw = resp.json().get("records", [])
    records = [_normalize(r) for r in raw]
    if not records:
        _write_cache(key, [])
        return []
    latest = _parse_date(records[0]["arrival_date"])
    cutoff = latest - timedelta(days=days)
    filtered = [r for r in records if _parse_date(r["arrival_date"]) >= cutoff]
    _write_cache(key, filtered)
    return filtered


def fetch_all_mandis_for_state(state: str) -> list[dict]:
    """Return unique {market, district} pairs active in the state. 
    Checks data/mandi_lists.json first, then local cache, then API.
    """
    # 1. Check pre-seeded static list (FASTEST for Live Demo).
    #    Only short-circuit if the seed actually has entries — empty lists
    #    fall through to cache/API so the app stays usable when the seed
    #    file is committed but unpopulated.
    seed_path = Path("data/mandi_lists.json")
    if seed_path.exists():
        try:
            lists = json.loads(seed_path.read_text())
            if state in lists and lists[state]:
                return lists[state]
        except Exception:
            pass

    # 2. Check 24h local cache
    key = _cache_key_all(state)
    cached = _read_cache(key)
    if cached is not None:
        return cached

    # 3. Fetch from API (Slowest)
    api_key = _get_key()
    if not api_key:
        return []

    resp = requests.get(
        BASE_URL,
        params={
            "api-key": api_key,
            "format": "json",
            "limit": 2000,
            "filters[State]": state,
            "sort[Arrival_Date]": "desc",
        },
        timeout=120,
    )
    resp.raise_for_status()
    raw = resp.json().get("records", [])

    seen: dict[tuple[str, str], dict] = {}
    for r in raw:
        market = (r.get("Market") or "").strip()
        district = (r.get("District") or "").strip()
        if not (market and district):
            continue
        seen.setdefault(
            (market.lower(), district.lower()),
            {"market": market, "district": district},
        )
    result = list(seen.values())
    _write_cache(key, result)
    return result


def _cache_key_all(state: str) -> str:
    return f"{state.lower()}_all.json"


def _normalize(r: dict) -> dict:
    return {
        "market": r.get("Market"),
        "district": r.get("District"),
        "arrival_date": r.get("Arrival_Date"),
        "min_price": _to_float(r.get("Min_Price")),
        "max_price": _to_float(r.get("Max_Price")),
        "modal_price": _to_float(r.get("Modal_Price")),
    }


def _to_float(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_date(s: str) -> datetime:
    return datetime.strptime(s, "%d/%m/%Y")


def _get_key() -> str | None:
    return os.environ.get("DATA_GOV_API_KEY")


def _cache_key(state: str, commodity: str, days: int) -> str:
    safe = commodity.replace("/", "_").replace(" ", "_").replace("(", "").replace(")", "")
    return f"{state.lower()}_{safe}_{days}d.json"


def _read_cache(key: str) -> list[dict] | None:
    path = CACHE_DIR / key
    if not path.exists():
        return None
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    if age > timedelta(hours=CACHE_TTL_HOURS):
        return None
    return json.loads(path.read_text())


def _write_cache(key: str, data: list[dict]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / key).write_text(json.dumps(data))
