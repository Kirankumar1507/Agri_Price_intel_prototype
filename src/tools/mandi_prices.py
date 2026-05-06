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

    resp = requests.get(
        BASE_URL,
        params={
            "api-key": _get_key(),
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
    """Return unique {market, district} pairs active in the state (any commodity). 24h cached.

    Used as the base layer for map rendering — includes mandis that don't report the
    currently selected crop. Single API call, no commodity filter, sorted newest first.
    """
    key = _cache_key_all(state)
    cached = _read_cache(key)
    if cached is not None:
        return cached

    resp = requests.get(
        BASE_URL,
        params={
            "api-key": _get_key(),
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


def _get_key() -> str:
    k = os.environ.get("DATA_GOV_API_KEY")
    if not k:
        raise RuntimeError("DATA_GOV_API_KEY missing in env")
    return k


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
