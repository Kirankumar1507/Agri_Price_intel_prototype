"""Seed data/ka_mandis.csv by enumerating mandis from Agmarknet + geocoding.

Strategy:
1. Hit data.gov.in Agmarknet resource with state=Karnataka, paginate.
2. Extract unique (market, district) pairs from price records.
3. Geocode each via Nominatim (1 req/s to respect their ToS).
4. Cache geocode results in .cache/geocode.json so re-runs are cheap.
5. Write data/ka_mandis.csv (name, district, lat, lng).
6. Write data/geocode_failed.csv for manual review (mandis with no match).

Run:
    DATA_GOV_API_KEY=... python scripts/seed_mandis.py

Expect: ~150 mandis, ~3 minutes wall time first run.
"""
import csv
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
AGMARKNET_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_UA = "agri-location-intel/0.1 (personal tool; github.com/kiran)"

OUT_CSV = Path("data/ka_mandis.csv")
FAIL_CSV = Path("data/geocode_failed.csv")
CACHE_PATH = Path(".cache/geocode.json")


def fetch_all_ka_mandis(api_key: str) -> set[tuple[str, str]]:
    """Paginate through Agmarknet for Karnataka, return unique (market, district)."""
    seen: set[tuple[str, str]] = set()
    offset = 0
    page_size = 1000
    while True:
        resp = requests.get(
            AGMARKNET_URL,
            params={
                "api-key": api_key,
                "format": "json",
                "limit": page_size,
                "offset": offset,
                "filters[state.keyword]": "Karnataka",
            },
            timeout=30,
        )
        resp.raise_for_status()
        records = resp.json().get("records", [])
        if not records:
            break
        for r in records:
            market = (r.get("market") or "").strip()
            district = (r.get("district") or "").strip()
            if market and district:
                seen.add((market, district))
        print(f"  offset={offset} got {len(records)} records, unique mandis so far: {len(seen)}")
        if len(records) < page_size:
            break
        offset += page_size
    return seen


def geocode(market: str, district: str, cache: dict) -> tuple[float, float] | None:
    key = f"{market}|{district}"
    if key in cache:
        return tuple(cache[key]) if cache[key] else None

    query = f"{market}, {district}, Karnataka, India"
    resp = requests.get(
        NOMINATIM_URL,
        params={"q": query, "format": "json", "limit": 1, "countrycodes": "in"},
        headers={"User-Agent": NOMINATIM_UA},
        timeout=20,
    )
    time.sleep(1.1)  # Nominatim ToS: max 1 req/s
    if resp.status_code != 200:
        print(f"    nominatim {resp.status_code} for {query}")
        cache[key] = None
        return None
    hits = resp.json()
    if not hits:
        cache[key] = None
        return None
    result = (float(hits[0]["lat"]), float(hits[0]["lon"]))
    cache[key] = list(result)
    return result


def load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text())
    return {}


def save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2))


def main() -> int:
    api_key = os.environ.get("DATA_GOV_API_KEY")
    if not api_key:
        print("ERROR: set DATA_GOV_API_KEY (free from data.gov.in)", file=sys.stderr)
        return 1

    print("1/3 Fetching Karnataka mandi list from Agmarknet...")
    mandis = sorted(fetch_all_ka_mandis(api_key))
    print(f"    -> {len(mandis)} unique (market, district) pairs")

    print("2/3 Geocoding via Nominatim (~1 req/s)...")
    cache = load_cache()
    rows: list[dict] = []
    failures: list[dict] = []
    for i, (market, district) in enumerate(mandis, 1):
        coords = geocode(market, district, cache)
        if coords:
            rows.append({"name": market, "district": district, "lat": coords[0], "lng": coords[1]})
        else:
            failures.append({"name": market, "district": district})
        if i % 20 == 0:
            save_cache(cache)
            print(f"    {i}/{len(mandis)} done ({len(failures)} failed so far)")
    save_cache(cache)

    print(f"3/3 Writing {OUT_CSV} ({len(rows)}) and {FAIL_CSV} ({len(failures)})...")
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "district", "lat", "lng"])
        writer.writeheader()
        writer.writerows(rows)
    if failures:
        with FAIL_CSV.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "district"])
            writer.writeheader()
            writer.writerows(failures)

    print(f"Done. Geocoded {len(rows)}/{len(mandis)}.")
    if failures:
        print(f"Review {FAIL_CSV} and manually add coords or fix names.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
