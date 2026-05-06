"""Match agri schemes to (crop, district) from a local curated JSON.

Seed: data/schemes.json — curate by hand (or scrape MyScheme.gov.in + KA dept).
Schema:
    {
      "name": str,
      "authority": "Centre" | "Karnataka",
      "applicable_crops": [str] | ["all"],
      "districts": [str] | ["all"],
      "eligibility": str,
      "benefit": str,
      "how_to_apply": str,
      "source_url": str
    }
"""
from __future__ import annotations

import json
from pathlib import Path

SCHEMES_PATH = Path("data/schemes.json")


def list_schemes(crop: str | None = None, district: str | None = None) -> list[dict]:
    data = json.loads(SCHEMES_PATH.read_text())
    out = data
    if crop:
        out = [s for s in out if _match(crop, s.get("applicable_crops", ["all"]))]
    if district:
        out = [s for s in out if _match(district, s.get("districts", ["all"]))]
    return out


def _match(value: str, values: list[str]) -> bool:
    lowered = [v.lower() for v in values]
    return "all" in lowered or value.lower() in lowered
