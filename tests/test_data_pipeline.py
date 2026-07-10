"""Hermetic tests for the data pipeline — no real network, no repo cache touched.

Strategy:
- Monkeypatch `requests.get` (all tools share the `requests` module) with a fake.
- No-op `time.sleep` so Nominatim rate-limit waits don't slow tests.
- `chdir(tmp_path)` when we need the live API path (so the relative seed/cache
  files under data/ and .cache/ don't exist and the code falls through).
"""
from __future__ import annotations

import json

import pytest

from src.tools import geo, geocoder, mandi_geocoder, mandi_prices


class FakeResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda *a, **k: None)


def _boom(*a, **k):  # requests.get that must not be called
    raise AssertionError("network was called but should not have been")


# --------------------------------------------------------------------------- #
# mandi_prices
# --------------------------------------------------------------------------- #

def test_fetch_prices_returns_empty_without_key(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATA_GOV_API_KEY", raising=False)
    monkeypatch.setattr("requests.get", _boom)  # must not hit network
    assert mandi_prices.fetch_prices("Karnataka", "Ragi (Finger Millet)") == []


def test_fetch_prices_applies_90_day_window(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATA_GOV_API_KEY", "dummy")
    records = {"records": [
        {"Market": "Mandya", "District": "Mandya", "Arrival_Date": "10/07/2026",
         "Min_Price": "3000", "Max_Price": "3200", "Modal_Price": "3100"},
        {"Market": "Mysuru", "District": "Mysuru", "Arrival_Date": "01/06/2026",
         "Min_Price": "2900", "Max_Price": "3100", "Modal_Price": "3000"},
        {"Market": "Hassan", "District": "Hassan", "Arrival_Date": "01/01/2026",  # >90d before latest
         "Min_Price": "2800", "Max_Price": "3000", "Modal_Price": "2900"},
    ]}
    monkeypatch.setattr("requests.get", lambda *a, **k: FakeResp(records))
    out = mandi_prices.fetch_prices("Karnataka", "Ragi (Finger Millet)")
    markets = {r["market"] for r in out}
    assert markets == {"Mandya", "Mysuru"}          # Hassan dropped (outside 90d)
    assert out[0]["modal_price"] == 3100.0          # normalized to float


def test_fetch_all_seed_short_circuits_without_network(monkeypatch):
    # Real data/mandi_lists.json is seeded → must return it with ZERO network.
    monkeypatch.setattr("requests.get", _boom)
    rows = mandi_prices.fetch_all_mandis_for_state("Karnataka")
    assert len(rows) > 0
    assert all("market" in r and "district" in r for r in rows)


def test_fetch_all_api_dedupes_case_insensitively(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # no seed / no cache here → API path
    monkeypatch.setenv("DATA_GOV_API_KEY", "dummy")
    raw = {"records": [
        {"Market": "Mandya", "District": "Mandya"},
        {"Market": "mandya", "District": "mandya"},   # dup (different case)
        {"Market": "Hassan", "District": "Hassan"},
        {"Market": "", "District": "X"},              # skipped (no market)
    ]}
    monkeypatch.setattr("requests.get", lambda *a, **k: FakeResp(raw))
    rows = mandi_prices.fetch_all_mandis_for_state("Karnataka")
    assert len(rows) == 2
    assert {r["market"] for r in rows} == {"Mandya", "Hassan"}


# --------------------------------------------------------------------------- #
# geo transforms (pure)
# --------------------------------------------------------------------------- #

def test_build_mandi_table_keeps_latest_per_market():
    records = [
        {"market": "Mandya", "district": "Mandya", "arrival_date": "01/07/2026", "modal_price": 3000},
        {"market": "Mandya", "district": "Mandya", "arrival_date": "08/07/2026", "modal_price": 3100},
        {"market": "Hassan", "district": "Hassan", "arrival_date": "05/07/2026", "modal_price": 2900},
    ]
    table = geo.build_mandi_table(records)
    assert len(table) == 2  # one row per market
    mandya = next(r for r in table if r["market"] == "Mandya")
    assert mandya["latest_date"] == "08/07/2026"   # kept the newer row
    assert mandya["modal_price"] == 3100


def test_decorate_with_distances_sorts_missing_coords_last():
    table = [
        {"market": "Faraway", "district": "F", "modal_price": 3000},
        {"market": "Nearby", "district": "N", "modal_price": 3000},
        {"market": "NoCoord", "district": "Z", "modal_price": 3000},
    ]
    coords = {
        "Faraway": (13.5, 76.5),
        "Nearby": (12.98, 77.58),
        # NoCoord intentionally absent
    }
    out = geo.decorate_with_distances(table, coords, user_lat=12.97, user_lng=77.59)
    assert out[0]["market"] == "Nearby"            # closest first
    assert out[-1]["market"] == "NoCoord"          # missing coords sorted last
    assert out[-1]["dist_km"] is None


# --------------------------------------------------------------------------- #
# geocoder / mandi_geocoder caching
# --------------------------------------------------------------------------- #

def test_geocoder_search_uses_cache_without_network(tmp_path, monkeypatch):
    cache_file = tmp_path / "geocode.json"
    cache_file.write_text(json.dumps({
        "Mandya, Karnataka": [{"display_name": "Mandya", "lat": 12.5, "lng": 76.9}]
    }))
    monkeypatch.setattr(geocoder, "CACHE_PATH", cache_file)
    monkeypatch.setattr("requests.get", _boom)  # cache hit → no network
    res = geocoder.search("Mandya, Karnataka")
    assert res[0]["lat"] == 12.5


def test_mandi_geocoder_geocodes_only_missing_districts(tmp_path, monkeypatch):
    cache_file = tmp_path / "coords.json"
    cache_file.write_text(json.dumps({"DISTRICT|Mandya|Karnataka": [12.5, 76.9]}))
    monkeypatch.setattr(mandi_geocoder, "CACHE_PATH", cache_file)

    calls = {"n": 0}

    def fake_get(*a, **k):
        calls["n"] += 1
        return FakeResp([{"lat": "13.0", "lon": "76.1"}])

    monkeypatch.setattr("requests.get", fake_get)
    mandis = [
        {"market": "Mandya APMC", "district": "Mandya"},    # cached → no call
        {"market": "Mandya Rural", "district": "Mandya"},   # same district → shares coord
        {"market": "Hassan APMC", "district": "Hassan"},    # missing → 1 call
    ]
    out = mandi_geocoder.geocode_mandis(mandis, "Karnataka")
    assert calls["n"] == 1                                  # only Hassan geocoded
    assert out["Mandya APMC"] == out["Mandya Rural"]        # shared district centroid
    assert out["Mandya APMC"] == (12.5, 76.9)
    assert out["Hassan APMC"] == (13.0, 76.1)
