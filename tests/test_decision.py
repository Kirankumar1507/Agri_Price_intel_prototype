"""Unit tests for the deterministic decision engine (src/agent.decide_action).

Pure Python — no network, no LLM, no Streamlit. Covers every verdict branch,
confidence tier, the ordering of the rules, key edge cases, and the
week-on-week trend calculation. Thresholds are read from src.config so these
tests track the config, not hard-coded magic numbers.
"""
from __future__ import annotations

import pytest

from src import config
from src.agent import _trend_change_pct, decide_action

# Fixed dates so the trend window is deterministic (the engine compares against
# the latest date *in the data*, never "now").
_LATEST = "10/07/2026"
_EARLIER = "02/07/2026"  # 8 days before _LATEST → inside the 5..9 day earlier window


def mk_trend(market: str, latest_price: float, earlier_price: float, n: int = 2):
    """Build a trend series that yields a known week-on-week % for `market`.

    Emits `n` rows at the latest date and `n` at the earlier date (>=4 total so
    the single-market branch doesn't fall through to the pooled fallback).
    """
    rows = []
    for _ in range(n):
        rows.append({"market": market, "date": _LATEST, "modal_price": latest_price})
        rows.append({"market": market, "date": _EARLIER, "modal_price": earlier_price})
    return rows


def best_row(market="Mandya", days_old=2, net_price=3000, modal_price=3000, dist_km=40):
    return {
        "category": "best", "market": market, "district": market,
        "days_old": days_old, "net_price": net_price,
        "modal_price": modal_price, "dist_km": dist_km,
    }


def near_row(market="Bengaluru", days_old=2, net_price=2550, modal_price=2600, dist_km=10):
    return {
        "category": "nearest", "market": market, "district": market,
        "days_old": days_old, "net_price": net_price,
        "modal_price": modal_price, "dist_km": dist_km,
    }


# --------------------------------------------------------------------------- #
# Verdict paths
# --------------------------------------------------------------------------- #

def test_no_data_when_table_empty():
    v = decide_action([], [], trend=[], user_has_location=False)
    assert v["verdict"] == "no_data"
    assert v["confidence"] == "low"
    assert v["best_market"] is None


def test_verify_when_stale():
    b = best_row(days_old=config.STALE_DAYS + 6)  # 20 days
    v = decide_action([b], [b], trend=[], user_has_location=False)
    assert v["verdict"] == "verify"
    assert v["confidence"] == "low"
    assert v["is_stale_days"] == config.STALE_DAYS + 6


def test_stale_takes_priority_over_trend():
    """Staleness is rule 1 — a falling price on stale data still → verify."""
    b = best_row(days_old=config.STALE_DAYS + 1)
    trend = mk_trend("Mandya", latest_price=900, earlier_price=1000)  # -10%
    v = decide_action([b], [b], trend=trend, user_has_location=False)
    assert v["verdict"] == "verify"


@pytest.mark.parametrize("latest,earlier,exp_conf", [
    (930, 1000, "med"),   # -7%  → med
    (900, 1000, "high"),  # -10% → high (boundary)
    (940, 1000, "med"),   # -6%
])
def test_sell_now_on_falling_price(latest, earlier, exp_conf):
    b = best_row(days_old=2)
    trend = mk_trend("Mandya", latest, earlier)
    v = decide_action([b], [b], trend=trend, user_has_location=False)
    assert v["verdict"] == "sell_now"
    assert v["confidence"] == exp_conf


@pytest.mark.parametrize("latest,earlier,exp_conf", [
    (1070, 1000, "med"),   # +7%  → med
    (1100, 1000, "high"),  # +10% → high (boundary)
])
def test_store_on_rising_price(latest, earlier, exp_conf):
    b = best_row(days_old=2)
    trend = mk_trend("Mandya", latest, earlier)
    v = decide_action([b], [b], trend=trend, user_has_location=False)
    assert v["verdict"] == "store"
    assert v["confidence"] == exp_conf


def test_travel_when_arbitrage_gap_beats_threshold():
    b = best_row(net_price=3000, dist_km=40)
    n = near_row(modal_price=2600, dist_km=10)  # net = 2600 - 5*10 = 2550; gap = 450
    v = decide_action([n, b], [b, n], trend=[], user_has_location=True)
    assert v["verdict"] == "travel"
    assert v["confidence"] == "med"
    assert v["arb_gap"] == pytest.approx(450.0)


def test_wait_when_no_signal():
    b = best_row(net_price=2600, dist_km=10)
    n = near_row(modal_price=2600, net_price=2550, dist_km=10)  # gap tiny
    v = decide_action([n, b], [b, n], trend=[], user_has_location=True)
    assert v["verdict"] == "wait"
    assert v["confidence"] == "low"


# --------------------------------------------------------------------------- #
# Rule ordering & edges
# --------------------------------------------------------------------------- #

def test_trend_beats_arbitrage():
    """Trend (rule 3/4) is evaluated before arbitrage (rule 5)."""
    b = best_row(market="Mandya", net_price=3000, dist_km=40)
    n = near_row(modal_price=2600, dist_km=10)  # big arb gap present too
    trend = mk_trend("Mandya", latest_price=930, earlier_price=1000)  # -7% → sell
    v = decide_action([n, b], [b, n], trend=trend, user_has_location=True)
    assert v["verdict"] == "sell_now"


def test_no_travel_without_location():
    """No location → nearest is None → arb_gap None → cannot travel."""
    b = best_row(net_price=3000, dist_km=40)
    n = near_row(modal_price=2600, dist_km=10)
    v = decide_action([n, b], [b, n], trend=[], user_has_location=False)
    assert v["verdict"] == "wait"
    assert v["arb_gap"] is None


def test_missing_net_price_yields_no_arb_gap():
    b = best_row(net_price=None)          # best has no net_price
    n = near_row()
    v = decide_action([n, b], [b, n], trend=[], user_has_location=True)
    assert v["arb_gap"] is None
    assert v["verdict"] == "wait"


def test_arbitrage_exactly_at_threshold_is_not_travel():
    """Rule is strict `> ARBITRAGE_MIN_GAP`, so exactly-at-threshold → wait."""
    # nearest net = modal - 5*dist; choose so gap == ARBITRAGE_MIN_GAP exactly.
    n = near_row(modal_price=2550, dist_km=10)          # nearest_net = 2500
    b = best_row(net_price=2500 + config.ARBITRAGE_MIN_GAP, dist_km=40)  # gap == 150
    v = decide_action([n, b], [b, n], trend=[], user_has_location=True)
    assert v["arb_gap"] == pytest.approx(config.ARBITRAGE_MIN_GAP)
    assert v["verdict"] == "wait"


# --------------------------------------------------------------------------- #
# _trend_change_pct
# --------------------------------------------------------------------------- #

def test_trend_empty_is_none():
    assert _trend_change_pct([], market=None, days=7) is None


def test_trend_dense_exact_pct():
    trend = mk_trend("X", latest_price=100, earlier_price=110)  # (100-110)/110
    pct = _trend_change_pct(trend, market="X", days=7)
    assert pct == pytest.approx(-9.0909, abs=1e-3)


def test_trend_sparse_single_market_falls_back_to_pool():
    # Only 2 rows for market "X" (sparse) but >=4 total across markets → pool.
    trend = [
        {"market": "X", "date": _LATEST, "modal_price": 90},
        {"market": "X", "date": _EARLIER, "modal_price": 100},
        {"market": "Y", "date": _LATEST, "modal_price": 90},
        {"market": "Y", "date": _EARLIER, "modal_price": 100},
    ]
    # Single-market "X" has <4 → recurses market=None, pools all 4 → -10%.
    pct = _trend_change_pct(trend, market="X", days=7)
    assert pct == pytest.approx(-10.0, abs=1e-6)


def test_trend_sparse_pool_is_none():
    trend = [
        {"market": "X", "date": _LATEST, "modal_price": 90},
        {"market": "X", "date": _EARLIER, "modal_price": 100},
    ]
    assert _trend_change_pct(trend, market=None, days=7) is None


def test_trend_zero_base_is_none():
    trend = mk_trend("X", latest_price=100, earlier_price=0)  # earlier mean 0
    assert _trend_change_pct(trend, market="X", days=7) is None


def test_trend_unparseable_rows_skipped():
    trend = mk_trend("X", latest_price=90, earlier_price=100)
    trend += [
        {"market": "X", "date": "not-a-date", "modal_price": 999},
        {"market": "X", "date": _LATEST, "modal_price": "NaN-ish"},
    ]
    pct = _trend_change_pct(trend, market="X", days=7)
    assert pct == pytest.approx(-10.0, abs=1e-6)
