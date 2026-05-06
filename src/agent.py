"""State-aware market overview + scheme explainers + info section.

Deterministic Python pipeline + LLM narrative layer. Aggressive in-process caching
via functools.lru_cache keeps repeat queries instant during a Streamlit session.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from functools import lru_cache
from pathlib import Path

try:
    import ollama
except ImportError:
    ollama = None
import google.generativeai as genai

from .config import TRANSPORT_RATE_PER_KM, commodity_display_to_api
from .tools import geo, mandi_geocoder, mandi_prices

MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:e4b")
PROMPTS_DIR = Path(__file__).parent / "prompts"


def analyze_market(
    state: str,
    crop_display: str,
    user_lat: float | None = None,
    user_lng: float | None = None,
    language: str = "en",
) -> dict:
    commodity_api = commodity_display_to_api(state, crop_display)
    all_mandis_raw = mandi_prices.fetch_all_mandis_for_state(state)
    records = mandi_prices.fetch_prices(state, commodity_api)

    mandi_table = geo.build_mandi_table(records) if records else []
    trend = geo.build_trend_rows(records) if records else []
    latest_date = mandi_table[0]["latest_date"] if mandi_table else None

    coords = mandi_geocoder.geocode_mandis(all_mandis_raw + mandi_table, state)
    if user_lat is not None and user_lng is not None and mandi_table:
        mandi_table = geo.decorate_with_distances(mandi_table, coords, user_lat, user_lng)

    all_mandis = _build_all_mandis(
        all_mandis_raw, mandi_table, coords, user_lat, user_lng,
    )

    narrative = None
    if records:
        narrative = _generate_overview(
            state, crop_display, mandi_table, latest_date,
            user_has_location=user_lat is not None,
            language=language,
        )

    verdict = decide_action(
        mandi_table, all_mandis, trend,
        user_has_location=user_lat is not None,
    )
    verdict_headline = None
    if verdict["verdict"] != "no_data":
        try:
            verdict_headline = _headline_for_verdict(
                verdict, state, crop_display, language=language,
            )
        except Exception:
            verdict_headline = None  # fail soft — UI falls back to template

    return {
        "narrative": narrative,
        "mandi_table": mandi_table,
        "all_mandis": all_mandis,
        "trend": trend,
        "latest_date": latest_date,
        "no_data": not records,
        "verdict": verdict,
        "verdict_headline": verdict_headline,
    }


def decide_action(
    mandi_table: list[dict],
    all_mandis: list[dict],
    trend: list[dict],
    user_has_location: bool,
) -> dict:
    """Deterministic verdict — sell_now/store/travel/wait/verify/no_data.

    Decision tree (in order):
      1. No mandi_table → no_data.
      2. Best-mandi staleness > 14d → verify (low confidence).
      3. Trend ≤ −5% week-on-week → sell_now (high if ≤ −10%, else med).
      4. Trend ≥ +5% week-on-week → store (high if ≥ +10%, else med).
      5. Arbitrage gap (best vs nearest) > ₹150/qtl → travel (med).
      6. Otherwise → wait (low) — no strong signal.

    Returns a dict consumable by the headline LLM and the UI callout.
    """
    if not mandi_table:
        return {
            "verdict": "no_data",
            "confidence": "low",
            "reasons": ["No mandi reported this crop in the last 90 days."],
            "best_market": None,
            "best_district": None,
            "best_net_price": None,
            "best_distance_km": None,
            "nearest_market": None,
            "trend_pct_week": None,
            "is_stale_days": None,
            "arb_gap": None,
        }

    best = next((r for r in all_mandis if r["category"] == "best"), None)
    nearest = (
        next((r for r in mandi_table if r.get("dist_km") is not None), None)
        if user_has_location else None
    )

    days_old = (
        best.get("days_old") if best
        else (mandi_table[0].get("days_old") if mandi_table else None)
    )
    is_stale = days_old is not None and days_old > 14

    trend_pct = _trend_change_pct(trend, market=(best["market"] if best else None), days=7)

    arb_gap = None
    if best and nearest and best["market"] != nearest["market"]:
        if (
            nearest.get("modal_price") is not None
            and nearest.get("dist_km") is not None
            and best.get("net_price") is not None
        ):
            nearest_net = (
                nearest["modal_price"] - TRANSPORT_RATE_PER_KM * nearest["dist_km"]
            )
            arb_gap = best["net_price"] - nearest_net

    reasons: list[str] = []
    if is_stale:
        reasons.append(f"Latest reported price is {days_old} days old.")
    if trend_pct is not None:
        reasons.append(f"Best mandi price moved {trend_pct:+.1f}% week-on-week.")
    if arb_gap is not None and arb_gap > 5 and best and nearest:
        reasons.append(
            f"{best['market']} pays ₹{arb_gap:.0f}/qtl more after transport "
            f"than {nearest['market']}."
        )

    if is_stale:
        verdict, conf = "verify", "low"
    elif trend_pct is not None and trend_pct <= -5:
        verdict, conf = "sell_now", ("high" if trend_pct <= -10 else "med")
    elif trend_pct is not None and trend_pct >= 5:
        verdict, conf = "store", ("high" if trend_pct >= 10 else "med")
    elif arb_gap is not None and arb_gap > 150:
        verdict, conf = "travel", "med"
    else:
        verdict, conf = "wait", "low"

    return {
        "verdict": verdict,
        "confidence": conf,
        "reasons": reasons,
        "best_market": best["market"] if best else None,
        "best_district": best.get("district") if best else None,
        "best_net_price": best.get("net_price") if best else None,
        "best_distance_km": best.get("dist_km") if best else None,
        "nearest_market": nearest["market"] if nearest else None,
        "trend_pct_week": round(trend_pct, 1) if trend_pct is not None else None,
        "is_stale_days": days_old if is_stale else None,
        "arb_gap": round(arb_gap, 0) if arb_gap is not None else None,
    }


def _trend_change_pct(
    trend: list[dict],
    market: str | None,
    days: int,
) -> float | None:
    """% change between latest mean modal and `days` ago mean modal.

    If `market` is given, restrict to that market's series. Otherwise pool all.
    Returns None if data is too sparse to compute.
    """
    if not trend:
        return None
    parsed: list[tuple[datetime, float]] = []
    for r in trend:
        if market and r.get("market") != market:
            continue
        try:
            d = datetime.strptime(r["date"], "%d/%m/%Y")
            p = float(r["modal_price"])
        except (ValueError, KeyError, TypeError):
            continue
        parsed.append((d, p))
    if len(parsed) < 4:
        # fallback: pool across all markets if single-market series too thin
        if market:
            return _trend_change_pct(trend, market=None, days=days)
        return None
    parsed.sort(key=lambda x: x[0])
    latest_dt = parsed[-1][0]
    latest_window = [
        p for d, p in parsed if (latest_dt - d).days <= 1
    ]
    earlier_window = [
        p for d, p in parsed if days - 2 <= (latest_dt - d).days <= days + 2
    ]
    if not latest_window or not earlier_window:
        return None
    a = sum(latest_window) / len(latest_window)
    b = sum(earlier_window) / len(earlier_window)
    if b == 0:
        return None
    return (a - b) / b * 100


def _headline_for_verdict(
    verdict: dict, state: str, crop: str, language: str = "en",
) -> str:
    return _headline_cached(json.dumps(verdict, sort_keys=True), state, crop, language)


@lru_cache(maxsize=128)
def _headline_cached(verdict_json: str, state: str, crop: str, language: str) -> str:
    verdict = json.loads(verdict_json)
    system = (PROMPTS_DIR / "decision.md").read_text()
    ctx = {**verdict, "state": state, "crop": crop, "language": language}
    return _chat(system, ctx).strip().strip('"')


def _build_all_mandis(
    all_mandis_raw: list[dict],
    crop_table: list[dict],
    coords: dict[str, tuple[float, float]],
    user_lat: float | None,
    user_lng: float | None,
) -> list[dict]:
    """Union of state-wide mandis + crop-reporting rows, categorized for map rendering.

    Categories (used by the UI for pin color):
      - "best":    top transport-adjusted net ₹/qtl among nearest 5 crop-reporting
      - "nearest": crop-reporting, in nearest 5 by haversine distance
      - "crop":    reports selected crop, but not in nearest 5
      - "other":   active mandi, does not report selected crop
    """
    crop_by_market = {m["market"]: m for m in crop_table}

    rows: list[dict] = []
    for m in all_mandis_raw:
        market = m["market"]
        c = coords.get(market)
        lat, lng = (c[0], c[1]) if c else (None, None)
        dist_km = None
        if c and user_lat is not None and user_lng is not None:
            dist_km = round(float(geo._haversine(user_lat, user_lng, c[0], c[1])), 1)
        crop_info = crop_by_market.get(market)
        modal = crop_info.get("modal_price") if crop_info else None
        net = None
        if modal is not None and dist_km is not None:
            net = modal - TRANSPORT_RATE_PER_KM * dist_km
        rows.append({
            "market": market,
            "district": m["district"],
            "lat": lat,
            "lng": lng,
            "dist_km": dist_km,
            "reports_crop": crop_info is not None,
            "modal_price": modal,
            "days_old": crop_info.get("days_old") if crop_info else None,
            "latest_date": crop_info.get("latest_date") if crop_info else None,
            "net_price": net,
            "category": "other",
        })

    crop_with_dist = sorted(
        (r for r in rows if r["reports_crop"] and r["dist_km"] is not None),
        key=lambda r: r["dist_km"],
    )
    nearest = crop_with_dist[:5]
    nearest_markets = {r["market"] for r in nearest}
    scored = [r for r in nearest if r["net_price"] is not None]
    best_market = max(scored, key=lambda r: r["net_price"])["market"] if scored else None

    for r in rows:
        if r["market"] == best_market:
            r["category"] = "best"
        elif r["market"] in nearest_markets:
            r["category"] = "nearest"
        elif r["reports_crop"]:
            r["category"] = "crop"
    return rows


def _generate_overview(
    state: str,
    crop: str,
    mandi_table: list[dict],
    latest_date: str | None,
    user_has_location: bool,
    language: str = "en",
) -> str:
    system = (PROMPTS_DIR / "market_overview.md").read_text()
    ctx = {
        "state": state,
        "crop": crop,
        "latest_date": latest_date,
        "mandi_count": len(mandi_table),
        "user_has_location": user_has_location,
        "top_mandis": mandi_table[:15],
    }
    return _chat(system, ctx, language=language)


def info_section(state: str, crop_display: str, language: str = "en") -> str:
    return _info_section_cached(state, crop_display, language)


@lru_cache(maxsize=128)
def _info_section_cached(state: str, crop_display: str, language: str) -> str:
    system = (PROMPTS_DIR / "info_section.md").read_text()
    return _chat(system, {"state": state, "crop": crop_display}, language=language)


def explain_scheme(scheme: dict, language: str = "en") -> str:
    return _explain_scheme_cached(json.dumps(scheme, sort_keys=True), language)


@lru_cache(maxsize=256)
def _explain_scheme_cached(scheme_json: str, language: str) -> str:
    scheme = json.loads(scheme_json)
    system = (PROMPTS_DIR / "scheme_layman.md").read_text()
    return _chat(system, scheme, language=language)


def scheme_usecase(scheme: dict, state: str, crop: str, language: str = "en") -> str:
    return _scheme_usecase_cached(json.dumps(scheme, sort_keys=True), state, crop, language)


@lru_cache(maxsize=256)
def _scheme_usecase_cached(scheme_json: str, state: str, crop: str, language: str) -> str:
    scheme = json.loads(scheme_json)
    system = (PROMPTS_DIR / "scheme_usecase.md").read_text()
    return _chat(system, {"scheme": scheme, "state": state, "crop": crop}, language=language)


_LANG_SUFFIX = {
    "kn": (
        "\n\n--- LANGUAGE OVERRIDE ---\n"
        "Write your entire response in Kannada (ಕನ್ನಡ) script. "
        "Do not mix English. Keep numbers and ₹ symbol as-is."
    ),
    "hi": (
        "\n\n--- LANGUAGE OVERRIDE ---\n"
        "Write your entire response in Hindi (हिन्दी) script. "
        "Do not mix English. Keep numbers and ₹ symbol as-is."
    ),
}


def _chat(system: str, user_obj, language: str = "en") -> str:
    if language in _LANG_SUFFIX:
        system = system + _LANG_SUFFIX[language]
    content = (
        json.dumps(user_obj, indent=2, default=str)
        if isinstance(user_obj, dict)
        else str(user_obj)
    )

    # Use Gemini if API key is present (Cloud Deployment)
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(f"SYSTEM: {system}\n\nUSER DATA: {content}")
            return response.text
        except Exception as e:
            return f"LLM Error: {str(e)}"

    # Fallback to local Ollama (Local Development)
    if ollama is not None:
        try:
            resp = ollama.chat(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": content},
                ],
                options={"temperature": 0.2},
            )
            return resp["message"]["content"]
        except Exception:
            return "Narrative unavailable (Ollama offline). Use GEMINI_API_KEY for cloud."
    
    return "Narrative unavailable (Ollama missing). Use GEMINI_API_KEY for cloud."
