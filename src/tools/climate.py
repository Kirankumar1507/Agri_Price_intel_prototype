"""ENSO + IOD climate signals from NOAA data files.

Two sources, both plain ASCII (no HTML scraping needed — we tried; HTML-only pages
were timeout-prone):

- ENSO: NOAA CPC ONI table  →  https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
  Format per line: "  SEASON  YYYY  TOTAL  ANOM"
  Phase rule: ANOM ≥ +0.5 → El Niño, ≤ −0.5 → La Niña, else Neutral.

- IOD: NOAA PSL HadISST-based DMI  →  https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmi.had.long.data
  Format per line: "YYYY Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec"
  -9999 sentinels mean missing month. Phase: ≥ +0.4 positive, ≤ −0.4 negative, else neutral.
  This file lags ~6–9 months behind real-time (HadISST update cadence). Surface the
  data-month timestamp so the UI is honest about staleness. BoM has a fresher value
  but their wrap-up returns 403 and the per-fortnight value isn't on a clean ASCII path.

Each source is fetched + cached independently so one outage doesn't kill the other.
File-backed cache survives Streamlit reruns. 7d TTL — these signals update monthly.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import requests

CACHE_DIR = Path(".cache/climate")
CACHE_TTL_HOURS = 24 * 7

ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
DMI_URL = "https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmi.had.long.data"

_UA = "agri-location-intel/0.2 (personal tool)"


def fetch_climate_signals() -> dict:
    """Return the merged signal dict. Either source missing → that field is None.

    Shape:
      {
        enso: {phase, value, season, sources: [...]} | None,
        iod:  {phase, value, month, sources: [...]} | None,
        fetched_at: iso8601,
      }
    """
    return {
        "enso": _fetch_enso(),
        "iod": _fetch_iod(),
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
    }


def _fetch_enso() -> dict | None:
    cached = _read_cache("enso.json")
    if cached is not None:
        return cached

    try:
        r = requests.get(ONI_URL, headers={"User-Agent": _UA}, timeout=20)
    except requests.RequestException:
        return None
    if not r.ok:
        return None

    # Last non-empty line — e.g. "  JFM 2026  26.57  -0.16"
    last = None
    for line in r.text.splitlines():
        s = line.strip()
        if not s or s.lower().startswith("seas"):
            continue
        parts = s.split()
        # season(3 char) year value anom
        if len(parts) == 4 and len(parts[0]) == 3 and parts[0].isalpha():
            last = parts
    if not last:
        return None

    season, year, _total, anom = last
    try:
        anom_val = float(anom)
    except ValueError:
        return None

    if anom_val >= 0.5:
        phase = "El Niño"
    elif anom_val <= -0.5:
        phase = "La Niña"
    else:
        phase = "Neutral"

    out = {
        "phase": phase,
        "value": round(anom_val, 2),
        "season": f"{season} {year}",
        "sources": ["NOAA CPC ONI"],
    }
    _write_cache("enso.json", out)
    return out


def _fetch_iod() -> dict | None:
    cached = _read_cache("iod.json")
    if cached is not None:
        return cached

    try:
        r = requests.get(DMI_URL, headers={"User-Agent": _UA}, timeout=20)
    except requests.RequestException:
        return None
    if not r.ok:
        return None

    # Find the most recent (year, month_idx) where value != -9999.
    last_year = None
    last_month_idx = None  # 1..12
    last_value = None
    for line in r.text.splitlines():
        s = line.strip()
        if not s:
            continue
        parts = s.split()
        # Year-row has 13 tokens: year + 12 monthly values
        if len(parts) != 13:
            continue
        if not re.fullmatch(r"\d{4}", parts[0]):
            continue
        try:
            year = int(parts[0])
            vals = [float(p) for p in parts[1:]]
        except ValueError:
            continue
        for i, v in enumerate(vals, start=1):
            if abs(v - (-9999.0)) < 1e-3:
                continue
            last_year, last_month_idx, last_value = year, i, v

    if last_value is None:
        return None

    if last_value >= 0.4:
        phase = "Positive"
    elif last_value <= -0.4:
        phase = "Negative"
    else:
        phase = "Neutral"

    month_label = datetime(last_year, last_month_idx, 1).strftime("%b %Y")
    out = {
        "phase": phase,
        "value": round(last_value, 2),
        "month": month_label,
        "sources": ["NOAA PSL DMI (HadISST1.1)"],
    }
    _write_cache("iod.json", out)
    return out


def _read_cache(key: str) -> dict | None:
    path = CACHE_DIR / key
    if not path.exists():
        return None
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    if age > timedelta(hours=CACHE_TTL_HOURS):
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _write_cache(key: str, data: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / key).write_text(json.dumps(data))
