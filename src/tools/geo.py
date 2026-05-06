"""Data munging — derive mandi table + trend rows from price records.

Coord-based distance was part of the old design; we may bring it back in Phase 2
when we geocode mandis. _haversine is kept for that future use and for tests.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime

import numpy as np


def build_mandi_table(records: list[dict]) -> list[dict]:
    """Group records by market; return latest price row per market, sorted by recency."""
    latest: dict[str, dict] = {}
    for r in records:
        m = (r.get("market") or "").strip()
        if not m:
            continue
        try:
            d = datetime.strptime(r["arrival_date"], "%d/%m/%Y")
        except (TypeError, ValueError):
            continue
        key = m.lower()
        prev = latest.get(key)
        if prev is None or d > datetime.strptime(prev["arrival_date"], "%d/%m/%Y"):
            latest[key] = r

    today = datetime.now()
    out = []
    for r in latest.values():
        try:
            d = datetime.strptime(r["arrival_date"], "%d/%m/%Y")
            age = (today - d).days
        except (TypeError, ValueError):
            age = None
        out.append({
            "market": r["market"],
            "district": r.get("district"),
            "latest_date": r["arrival_date"],
            "days_old": age,
            "modal_price": r.get("modal_price"),
            "min_price": r.get("min_price"),
            "max_price": r.get("max_price"),
        })
    out.sort(key=lambda x: (
        x["days_old"] if x["days_old"] is not None else 10**6,
        -(x.get("modal_price") or 0),
    ))
    return out


def decorate_with_distances(
    mandi_table: list[dict],
    coords: dict[str, tuple[float, float]],
    user_lat: float,
    user_lng: float,
) -> list[dict]:
    """Mutate and return: add lat/lng/dist_km per row; sort by distance."""
    for row in mandi_table:
        c = coords.get(row["market"])
        if c:
            row["lat"] = c[0]
            row["lng"] = c[1]
            row["dist_km"] = round(float(_haversine(user_lat, user_lng, c[0], c[1])), 1)
        else:
            row["lat"] = None
            row["lng"] = None
            row["dist_km"] = None
    mandi_table.sort(key=lambda r: (r["dist_km"] is None, r.get("dist_km") or 0))
    return mandi_table


def build_trend_rows(records: list[dict]) -> list[dict]:
    """Aggregate (market, date) → avg modal_price."""
    bucket: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in records:
        m = (r.get("market") or "").strip()
        d = r.get("arrival_date")
        p = r.get("modal_price")
        if not (m and d and p is not None):
            continue
        bucket[(m, d)].append(float(p))
    return [
        {"market": m, "date": d, "modal_price": sum(v) / len(v)}
        for (m, d), v in bucket.items()
    ]


def _haversine(lat1, lng1, lat2, lng2):
    R = 6371.0
    lat1, lng1, lat2, lng2 = map(np.radians, [lat1, lng1, lat2, lng2])
    dlat, dlng = lat2 - lat1, lng2 - lng1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlng / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))
