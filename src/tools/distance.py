"""Road distance via public OSRM. In-process LRU cache.

Public OSRM has rate limits (~1 req/s, demo use). Swap to a self-hosted OSRM
or Mapbox/Google for production.
"""
from functools import lru_cache

import requests

OSRM_URL = "https://router.project-osrm.org/route/v1/driving"


@lru_cache(maxsize=4096)
def road_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    url = f"{OSRM_URL}/{lng1},{lat1};{lng2},{lat2}"
    resp = requests.get(url, params={"overview": "false"}, timeout=15)
    resp.raise_for_status()
    return resp.json()["routes"][0]["distance"] / 1000.0
