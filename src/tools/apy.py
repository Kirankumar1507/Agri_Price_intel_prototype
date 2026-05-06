"""DES Crop Area-Production-Yield (1997-2014, frozen). 7d cached per (state, crop).

Resource records are at (state, district, season, year, crop) granularity. We
aggregate to state-year totals — sum area_ and production_ across districts and
seasons, then derive yield = production / area (kg/ha if base units are tonnes
and hectares, which DES uses).

Why this dataset: it's the only public APY API on data.gov.in that covers
multi-decade history. It stops at 2014 — DES no longer updates the open
endpoint. Acceptable tradeoff for showing trend depth in the demo.
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import requests

from src.config import APY_RESOURCE_ID

CACHE_DIR = Path(".cache/apy")
CACHE_TTL_HOURS = 24 * 7
BASE_URL = f"https://api.data.gov.in/resource/{APY_RESOURCE_ID}"


def fetch_apy(state: str, apy_crop: str) -> list[dict]:
    """Return [{year, area_ha, production_tonnes, yield_kg_ha}] sorted by year asc.

    Empty list = no records for this (state, crop) pair in the DES dataset.
    """
    key = _cache_key(state, apy_crop)
    cached = _read_cache(key)
    if cached is not None:
        return cached

    resp = requests.get(
        BASE_URL,
        params={
            "api-key": _get_key(),
            "format": "json",
            "limit": 5000,
            "filters[state_name]": state,
            "filters[crop]": apy_crop,
        },
        timeout=60,
    )
    if not resp.ok:
        return []
    raw = resp.json().get("records", [])
    rows = _aggregate_by_year(raw)
    _write_cache(key, rows)
    return rows


def _aggregate_by_year(raw: list[dict]) -> list[dict]:
    by_year: dict[int, dict] = defaultdict(lambda: {"area": 0.0, "production": 0.0})
    for r in raw:
        year = r.get("crop_year")
        if not isinstance(year, int):
            try:
                year = int(str(year).split("-")[0])
            except (ValueError, AttributeError, TypeError):
                continue
        a = _to_float(r.get("area_"))
        p = _to_float(r.get("production_"))
        if a is not None:
            by_year[year]["area"] += a
        if p is not None:
            by_year[year]["production"] += p

    out: list[dict] = []
    for year, agg in sorted(by_year.items()):
        area = agg["area"]
        prod = agg["production"]
        # DES: area in hectares, production in tonnes → yield = (tonnes * 1000) / ha = kg/ha
        yield_kg_ha = (prod * 1000.0 / area) if area > 0 else None
        out.append({
            "year": year,
            "area_ha": area if area > 0 else None,
            "production_tonnes": prod if prod > 0 else None,
            "yield_kg_ha": yield_kg_ha,
        })
    return out


def _to_float(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _get_key() -> str:
    k = os.environ.get("DATA_GOV_API_KEY")
    if not k:
        raise RuntimeError("DATA_GOV_API_KEY missing in env")
    return k


def _cache_key(state: str, apy_crop: str) -> str:
    safe = (
        apy_crop.replace("/", "_").replace(" ", "_")
        .replace("(", "").replace(")", "").replace("&", "and")
    )
    return f"{state.lower()}_{safe}.json"


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
