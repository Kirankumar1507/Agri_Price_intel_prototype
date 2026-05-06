from __future__ import annotations

import folium
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from streamlit_folium import st_folium

from src.agent import (
    analyze_market,
    explain_scheme,
    info_section,
    scheme_usecase,
)
from datetime import datetime
from pathlib import Path

from src.config import STATES, commodity_display_to_apy, crop_displays
from src.i18n import LANGUAGES, STATE_DEFAULT_LANG, t
from src.tools import apy as apy_tool
from src.tools import climate as climate_tool
from src.tools import geocoder, schemes
from src.tools import msp as msp_tool
from src.tools import weather as weather_tool

load_dotenv()

st.set_page_config(page_title="Agri Price Intel", layout="wide")
st.title("Agri Price Intel")


# Color + size hierarchy for the map. Teardrop SVG pins (not folium.Icon) because
# folium's built-in marker palette has no "yellow" — SVG takes any hex.
_CATEGORY_STYLE = {
    "best":    ("#0b5d0b", 40),
    "nearest": ("#2ecc40", 30),
    "crop":    ("#f1c40f", 22),
    "other":   ("#1e88e5", 14),
}


def _mandi_pin(color: str, size: int) -> folium.DivIcon:
    """Material-style teardrop pin, scaled by `size`. Tip anchors at the coord."""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'width="{size}" height="{size}" '
        f'style="display:block;filter:drop-shadow(0 1px 2px rgba(0,0,0,0.45));">'
        f'<path fill="{color}" stroke="#ffffff" stroke-width="1.2" '
        f'd="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>'
        f'<circle cx="12" cy="9" r="2.4" fill="#ffffff"/>'
        f'</svg>'
    )
    return folium.DivIcon(
        html=svg,
        icon_size=(size, size),
        icon_anchor=(size // 2, int(size * 22 / 24)),
    )


def _most_active(tdf: pd.DataFrame, n: int) -> list[str]:
    return tdf.groupby("market").size().sort_values(ascending=False).head(n).index.tolist()


_BADGE_LLM = (
    '<span style="font-size:0.65rem;padding:2px 8px;border-radius:4px;'
    'font-weight:600;letter-spacing:0.4px;background:#eaf1fb;color:#1a57b8;'
    'vertical-align:middle;margin-left:0.5rem;">LLM REASONING</span>'
)


# Verdict callout palette: (border/accent, soft background, i18n key)
_VERDICT_STYLE = {
    "sell_now": ("#0b5d0b", "#e8f5e9", "verdict.sell_now"),
    "store":    ("#1565c0", "#e3f2fd", "verdict.store"),
    "travel":   ("#e65100", "#fff3e0", "verdict.travel"),
    "wait":     ("#616161", "#f5f5f5", "verdict.wait"),
    "verify":   ("#f9a825", "#fffde7", "verdict.verify"),
}


def _render_verdict_callout(
    verdict_obj: dict, headline: str | None, lang: str = "en",
) -> None:
    """Big colored verdict box, replaces a plain success banner."""
    fg, bg, label_key = _VERDICT_STYLE.get(
        verdict_obj["verdict"], ("#616161", "#f5f5f5", "verdict.wait"),
    )
    label = t(label_key, lang)
    conf_label = t("verdict.confidence", lang)
    conf = verdict_obj.get("confidence", "low").upper()
    headline_text = headline or _fallback_headline(verdict_obj)
    reasons = " · ".join(verdict_obj.get("reasons", [])[:3])
    html = (
        f'<div style="background:{bg};border-left:4px solid {fg};'
        f'padding:14px 18px;border-radius:6px;margin-bottom:12px;">'
        f'<div style="display:flex;align-items:center;gap:10px;">'
        f'<span style="background:{fg};color:#fff;padding:3px 10px;'
        f'border-radius:4px;font-weight:700;font-size:0.72rem;'
        f'letter-spacing:0.6px;">{label.upper()}</span>'
        f'<span style="font-size:0.7rem;color:{fg};font-weight:600;">'
        f'{conf_label}: {conf}</span>'
        f'<span style="{ _BADGE_LLM_INLINE_STYLE }">LLM HEADLINE</span>'
        f'</div>'
        f'<div style="font-size:1.1rem;font-weight:600;color:#1a1a1a;'
        f'margin:10px 0 4px;line-height:1.35;">{headline_text}</div>'
        f'<div style="font-size:0.85rem;color:#555;">{reasons}</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


_BADGE_LLM_INLINE_STYLE = (
    "font-size:0.6rem;padding:1px 7px;border-radius:3px;"
    "font-weight:600;letter-spacing:0.3px;background:#eaf1fb;color:#1a57b8;"
    "margin-left:auto;"
)


def _fallback_headline(verdict_obj: dict) -> str:
    """Used when LLM headline generation fails — template stays factual."""
    v = verdict_obj["verdict"]
    market = verdict_obj.get("best_market")
    days = verdict_obj.get("is_stale_days")
    pct = verdict_obj.get("trend_pct_week")
    arb = verdict_obj.get("arb_gap")
    if v == "verify" and days:
        return f"Verify with local mandi — last reported price is {days} days old."
    if v == "sell_now" and market and pct is not None:
        return f"Sell at {market} — prices fell {pct:+.1f}% this week."
    if v == "store" and pct is not None:
        return f"Store for now — prices up {pct:+.1f}% week-on-week."
    if v == "travel" and market and arb:
        return f"Travel to {market} — earns ₹{arb:.0f}/qtl more after transport."
    return "Wait — no strong price signal yet."


DEMO = {
    "state": "Karnataka",
    "crop": "Ragi",
    "display_name": "Bengaluru, Karnataka, India",
    "lat": 12.9716,
    "lng": 77.5946,
}


# Crop calendar — loaded once at import time, no caching needed.
_CALENDAR_PATH = Path("data/crop_calendar.json")
try:
    import json as _json
    _CROP_CALENDAR = _json.loads(_CALENDAR_PATH.read_text())
except (OSError, _json.JSONDecodeError):
    _CROP_CALENDAR = {}


# Climate-strip phase colors (independent of language)
_ENSO_COLORS = {
    "El Niño":  "#e65100",
    "La Niña":  "#1565c0",
    "Neutral":  "#616161",
}
_IOD_COLORS = {
    "Positive": "#e65100",
    "Negative": "#1565c0",
    "Neutral":  "#616161",
}


def _phase_chip(label: str, value: str | None, color: str) -> str:
    val_part = f" {value}" if value else ""
    return (
        f'<span style="background:{color};color:#fff;padding:2px 9px;'
        f'border-radius:12px;font-size:0.72rem;font-weight:600;'
        f'letter-spacing:0.3px;margin-right:6px;">'
        f'{label}{val_part}</span>'
    )


# Demo prefill must run before widgets read session_state — Streamlit populates
# widget values from state on the same render pass.
if st.session_state.pop("_apply_demo", False):
    st.session_state["state_sel"] = DEMO["state"]
    st.session_state["crop_sel"] = DEMO["crop"]
    st.session_state["candidates"] = [{
        "display_name": DEMO["display_name"],
        "lat": DEMO["lat"],
        "lng": DEMO["lng"],
    }]
    st.session_state["selected_idx"] = 0
    st.session_state["_run_demo"] = True


# --- Sidebar ---
# Read state early so we can pick a sensible default language for the toggle.
_pre_state = st.session_state.get("state_sel", list(STATES.keys())[0])
_default_lang = STATE_DEFAULT_LANG.get(_pre_state, "en")

with st.sidebar:
    lang_codes = list(LANGUAGES.keys())
    lang = st.selectbox(
        "Language / ಭಾಷೆ / भाषा",
        lang_codes,
        format_func=lambda c: LANGUAGES[c],
        index=lang_codes.index(st.session_state.get("lang_sel", _default_lang)),
        key="lang_sel",
    )

    st.header(t("sidebar.scope", lang))
    state = st.selectbox(t("sidebar.state", lang), list(STATES.keys()), key="state_sel")
    cfg = STATES[state]
    crop = st.selectbox(t("sidebar.crop", lang), crop_displays(state), key="crop_sel")

    st.divider()
    st.header(t("sidebar.location", lang))
    address_query = st.text_input(
        t("sidebar.address_input", lang),
        key="addr_q",
        placeholder=f"e.g. Mandya, {state}",
    )
    search_btn = st.button(t("sidebar.search", lang), use_container_width=True)

    if search_btn and address_query.strip():
        with st.spinner(t("sidebar.searching", lang)):
            try:
                candidates = geocoder.search(f"{address_query.strip()}, {state}")
                st.session_state["candidates"] = candidates
                st.session_state["selected_idx"] = 0 if candidates else None
            except Exception as e:
                st.error(f"Geocoder failed: {e}")
                st.session_state["candidates"] = []

    candidates = st.session_state.get("candidates", [])
    selected = None
    if candidates:
        idx = st.radio(
            t("sidebar.pick_one", lang),
            range(len(candidates)),
            format_func=lambda i: candidates[i]["display_name"][:80],
            key="selected_idx",
        )
        selected = candidates[idx]
    elif search_btn and address_query.strip():
        st.info(t("sidebar.no_matches", lang))

    st.divider()
    go = st.button(
        t("sidebar.get_intel", lang),
        type="primary",
        disabled=selected is None,
        use_container_width=True,
    )

# --- Compute (once per Go click or demo trigger) ---
run_demo = st.session_state.pop("_run_demo", False)
if (go or run_demo) and selected:
    with st.spinner("Fetching live mandi prices & analyzing market trends..."):
        st.session_state["result"] = analyze_market(
            state, crop,
            user_lat=selected["lat"],
            user_lng=selected["lng"],
            language=lang,
        )
        st.session_state["result_for"] = {
            "state": state, "crop": crop,
            "lat": selected["lat"], "lng": selected["lng"],
            "display_name": selected["display_name"],
            "language": lang,
        }

# Show result only if it matches the current scope selection
result = st.session_state.get("result")
result_for = st.session_state.get("result_for")
stale_result = False
if result and result_for:
    if (
        result_for["state"] != state
        or result_for["crop"] != crop
        or result_for.get("language", "en") != lang
    ):
        stale_result = True


# --- Landing hero OR answer-first metric row ---
def _fmt_rupees(v: float) -> str:
    return f"₹{v:,.0f}"


if not result:
    st.markdown(f"#### {t('hero.what', lang)}")
    st.markdown(
        "Pick a state, crop, and village in the sidebar → get the **best APMC mandi** "
        "(highest net ₹/qtl after ₹5/km transport), the nearest 5 options, and the "
        "government schemes that apply — rewritten in plain English."
    )
    c_demo, c_info = st.columns([1, 3])
    with c_demo:
        if st.button(
            t("hero.demo_button", lang),
            type="primary",
            use_container_width=True,
        ):
            st.session_state["_apply_demo"] = True
            st.rerun()
    with c_info:
        st.caption(
            "Or use the sidebar to pick your own state, crop, and location. "
            "Data source: data.gov.in Agmarknet (variety-wise daily prices)."
        )
elif not stale_result and not result["no_data"]:
    verdict_obj = result.get("verdict") or {}
    verdict_headline = result.get("verdict_headline")
    if verdict_obj.get("verdict") and verdict_obj["verdict"] != "no_data":
        _render_verdict_callout(verdict_obj, verdict_headline, lang)

    best = next(
        (r for r in result["all_mandis"] if r["category"] == "best"), None
    )
    nearest_rows = [
        r for r in result["mandi_table"] if r.get("dist_km") is not None
    ]
    nearest = nearest_rows[0] if nearest_rows else None

    if best:
        st.subheader(t("answer.title", lang))
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            t("answer.best_mandi", lang),
            best["market"],
            help=f"{best['district']} district · {best['days_old']}d old price",
        )
        c2.metric(t("answer.distance", lang), f"{best['dist_km']:.1f} km")
        c3.metric(t("answer.modal_price", lang), f"{_fmt_rupees(best['modal_price'])}/qtl")
        delta = None
        if (
            nearest
            and nearest["market"] != best["market"]
            and nearest.get("modal_price") is not None
        ):
            nearest_net = nearest["modal_price"] - 5 * nearest["dist_km"]
            diff = best["net_price"] - nearest_net
            if diff > 5:
                delta = f"+{_fmt_rupees(diff)} vs nearest"
        c4.metric(
            t("answer.net_price", lang),
            _fmt_rupees(best["net_price"]),
            delta=delta,
            help="modal price − ₹5/km × distance (transport-adjusted)",
        )
        if delta:
            st.caption(
                f"Going to **{best['market']}** instead of the nearest mandi "
                f"({nearest['market']}, {nearest['dist_km']} km) earns you "
                f"{delta.lstrip('+')}/quintal after transport."
            )

        # MSP comparison
        msp_info = msp_tool.get_msp(crop)
        if msp_info and best.get("modal_price") is not None:
            msp_val = msp_info["msp"]
            modal = best["modal_price"]
            msp_diff = modal - msp_val
            msp_pct = (msp_diff / msp_val * 100) if msp_val else 0
            msp_color = "#0b5d0b" if msp_diff >= 0 else "#e53935"
            msp_icon = "↑" if msp_diff >= 0 else "↓"
            msp_label = "above MSP" if msp_diff >= 0 else "below MSP"
            st.markdown(
                f'<div style="background:#f8faf8;border:1px solid #e0e8e0;'
                f'border-radius:8px;padding:12px 18px;margin:8px 0 4px;">'
                f'<span style="font-size:0.78rem;color:#555;">MSP Comparison</span> · '
                f'<span style="font-weight:700;color:{msp_color};font-size:0.95rem;">'
                f'{msp_icon} {_fmt_rupees(abs(msp_diff))}/qtl {msp_label}</span>'
                f'<span style="font-size:0.78rem;color:#888;margin-left:8px;">'
                f'(MSP: {_fmt_rupees(msp_val)}/qtl · Market: {_fmt_rupees(modal)}/qtl · '
                f'{msp_pct:+.1f}% · {msp_info["season"]})</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

# --- Main columns ---
col_map, col_out = st.columns([1, 1])

with col_map:
    st.subheader("Map")
    if selected:
        center = [selected["lat"], selected["lng"]]
        zoom = 10
    else:
        center = cfg["map_center"]
        zoom = cfg["map_zoom"]
    m = folium.Map(location=center, zoom_start=zoom)

    if selected:
        folium.Marker(
            [selected["lat"], selected["lng"]],
            popup=selected["display_name"],
            icon=folium.Icon(color="red", icon="user"),
            tooltip="Your location",
        ).add_to(m)

    all_mandis = (
        result.get("all_mandis", []) if (result and not stale_result) else []
    )
    # Draw lowest-priority first so the best/nearest pins render on top.
    _draw_order = {"other": 0, "crop": 1, "nearest": 2, "best": 3}
    for r in sorted(all_mandis, key=lambda x: _draw_order.get(x["category"], 0)):
        if r.get("lat") is None or r.get("lng") is None:
            continue
        color, size = _CATEGORY_STYLE[r["category"]]
        dist_label = f"{r['dist_km']} km" if r.get("dist_km") is not None else "—"
        if r["reports_crop"]:
            price_label = (
                f"₹{r['modal_price']:.0f}/qtl"
                if r.get("modal_price") is not None else "no price"
            )
            days_label = (
                f"{r['days_old']}d old" if r.get("days_old") is not None else ""
            )
            net_label = (
                f"net ₹{r['net_price']:.0f}/qtl after transport"
                if r.get("net_price") is not None else ""
            )
            parts = [p for p in [price_label, dist_label, days_label, net_label] if p]
            popup = f"<b>{r['market']}</b> ({r['district']})<br>{' · '.join(parts)}"
            tooltip = f"{r['market']} — {price_label}"
        else:
            parts = [f"No {crop} data", dist_label]
            popup = f"<b>{r['market']}</b> ({r['district']})<br>{' · '.join(parts)}"
            tooltip = f"{r['market']} — no {crop} data"
        folium.Marker(
            [r["lat"], r["lng"]],
            popup=popup,
            tooltip=tooltip,
            icon=_mandi_pin(color, size),
        ).add_to(m)

    st_folium(m, height=420, returned_objects=[])

    if selected:
        st.caption(f"**{selected['display_name']}**")
    else:
        st.caption("Search an address in the sidebar to pick your location.")
    if all_mandis:
        st.caption(
            "Legend: "
            "<span style='color:#dc3545'>●</span> you · "
            "<span style='color:#0b5d0b'>●</span> best (net of ₹5/km transport) · "
            "<span style='color:#2ecc40'>●</span> 5 nearest · "
            "<span style='color:#f1c40f'>●</span> reports crop · "
            "<span style='color:#1e88e5'>●</span> other mandi",
            unsafe_allow_html=True,
        )
        st.caption(
            "⚠️ **Note**: Pins are placed at district centroids (not exact mandi addresses) — "
            "multiple mandis within the same district will overlap on the map. "
            "This is a known limitation of free geocoding for APMC names."
        )

with col_out:
    if stale_result:
        st.info(
            "You changed state/crop after fetching. Click **Get market intelligence** "
            "again to refresh."
        )

    tab_intel, tab_production, tab_weather, tab_context = st.tabs([
        t("tab.market_intel", lang),
        t("tab.production", lang),
        t("tab.weather", lang),
        t("tab.about_schemes", lang, crop=crop),
    ])

    with tab_intel:
        if not result or stale_result:
            st.caption(
                "Run a query from the sidebar (or hit the demo button above) "
                "to see prices, nearest mandis, and price trends here."
            )
        elif result["no_data"]:
            st.error(
                f"**Data not available from source** — no {result_for['crop']} prices "
                f"reported in {result_for['state']} over the last 90 days via data.gov.in."
            )
        else:
            latest = result["latest_date"]
            nearest = next(
                (r for r in result["mandi_table"] if r.get("dist_km") is not None),
                None,
            )
            st.info(
                f"Latest data: **{latest}**  ·  **{len(result['mandi_table'])}** "
                f"mandis reported in 90-day window"
            )

            if nearest:
                price_str = (
                    f"₹{nearest['modal_price']:.0f}/qtl"
                    if nearest.get("modal_price") else "no recent price"
                )
                st.success(
                    f"**Nearest mandi**: {nearest['market']} ({nearest['district']}) · "
                    f"**{nearest['dist_km']} km** · {price_str} · "
                    f"{nearest['days_old']} days old"
                )

            st.markdown(
                f"### Market overview {_BADGE_LLM}",
                unsafe_allow_html=True,
            )
            st.markdown(result["narrative"])

            st.subheader("Mandis — sorted by distance")
            df = pd.DataFrame(result["mandi_table"])
            show_cols = [
                "market", "district", "dist_km", "modal_price",
                "min_price", "max_price", "latest_date", "days_old",
            ]
            df = df[[c for c in show_cols if c in df.columns]]
            st.dataframe(df, hide_index=True, use_container_width=True)

            if result["trend"]:
                st.subheader("15-day price trend")
                tdf = pd.DataFrame(result["trend"])
                tdf["date_parsed"] = pd.to_datetime(
                    tdf["date"], format="%d/%m/%Y", errors="coerce"
                )
                tdf = tdf.dropna(subset=["date_parsed"])
                if not tdf.empty:
                    latest_dt = tdf["date_parsed"].max()
                    cutoff = latest_dt - pd.Timedelta(days=15)
                    tdf = tdf[tdf["date_parsed"] >= cutoff]
                    all_markets = sorted(tdf["market"].unique())
                    # Default: nearest mandis that appear in trend
                    nearest_mandis = [
                        r["market"] for r in result["mandi_table"]
                        if r.get("dist_km") is not None
                    ][:5]
                    default = [m for m in nearest_mandis if m in all_markets]
                    if not default:
                        default = _most_active(tdf, 5)
                    picked = st.multiselect(
                        "Compare mandis (default: 5 nearest)",
                        all_markets,
                        default=default,
                    )
                    if picked:
                        plot_df = tdf[tdf["market"].isin(picked)]
                        pivot = plot_df.pivot_table(
                            index="date_parsed",
                            columns="market",
                            values="modal_price",
                        )
                        st.line_chart(pivot)
                    else:
                        st.caption("Pick at least one mandi.")

    with tab_production:
        apy_crop = commodity_display_to_apy(state, crop)
        if not apy_crop:
            st.info(
                f"**{crop}** is not tracked in the DES Crop Production dataset "
                "(1997–2014). This dataset is frozen at 2014 — DES no longer "
                "publishes APY through the open API."
            )
        else:
            try:
                apy_rows = apy_tool.fetch_apy(state, apy_crop)
            except Exception as e:
                st.error(f"APY fetch failed: {e}")
                apy_rows = []

            if not apy_rows:
                st.info(
                    f"No APY records returned for **{crop}** in **{state}**. "
                    "The DES dataset (1997–2014) may not cover this combination."
                )
            else:
                st.caption(
                    f"**Source**: data.gov.in DES Crop Production · "
                    f"{apy_rows[0]['year']}–{apy_rows[-1]['year']} "
                    f"({len(apy_rows)} years). "
                    f"This is the only public APY API on data.gov.in for "
                    f"state-wise crop production; it stops at 2014. "
                    f"Current figures (through 2022-23) live behind auth at "
                    f"`data.upag.gov.in` (UPAg API, OAuth2) and "
                    f"`data.desagri.gov.in` (DES portal, Excel export only)."
                )

                latest = apy_rows[-1]
                prev = apy_rows[-2] if len(apy_rows) >= 2 else None

                def _delta_pct(curr, prior):
                    if curr is None or prior is None or prior == 0:
                        return None
                    return (curr - prior) / prior * 100

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Year", str(latest["year"]))

                area_l = latest.get("area_ha")
                m2.metric(
                    "Area",
                    f"{area_l/1000:,.0f} kha" if area_l else "—",
                    help="thousand hectares",
                )

                prod_l = latest.get("production_tonnes")
                d_prod = (
                    _delta_pct(prod_l, prev.get("production_tonnes"))
                    if prev else None
                )
                m3.metric(
                    "Production",
                    f"{prod_l/1000:,.0f} kt" if prod_l else "—",
                    delta=f"{d_prod:+.1f}% YoY" if d_prod is not None else None,
                    help="thousand tonnes",
                )

                yield_l = latest.get("yield_kg_ha")
                d_yield = (
                    _delta_pct(yield_l, prev.get("yield_kg_ha"))
                    if prev else None
                )
                m4.metric(
                    "Yield",
                    f"{yield_l:,.0f} kg/ha" if yield_l else "—",
                    delta=f"{d_yield:+.1f}% YoY" if d_yield is not None else None,
                )

                st.subheader("Yield trend")
                ydf = pd.DataFrame(apy_rows).set_index("year")[["yield_kg_ha"]]
                ydf.columns = [f"{crop} yield (kg/ha)"]
                st.line_chart(ydf)

                with st.expander("Area & production over time"):
                    ap_df = pd.DataFrame(apy_rows).set_index("year")[
                        ["area_ha", "production_tonnes"]
                    ]
                    ap_df.columns = ["Area (ha)", "Production (tonnes)"]
                    st.line_chart(ap_df)

                st.caption(
                    "Note: aggregated across all districts and seasons within "
                    f"{state}. Yield is derived as production ÷ area, so very "
                    "early years with patchy district reporting may show noise."
                )

    with tab_weather:
        # 1. Climate signal strip (always visible — global signals, no location needed)
        try:
            climate = climate_tool.fetch_climate_signals()
        except Exception as e:
            climate = {"enso": None, "iod": None, "fetched_at": None}
            st.caption(f"climate fetch failed: {e}")

        chips = []
        unavail = t("weather.unavailable", lang)
        if climate.get("enso"):
            e = climate["enso"]
            color = _ENSO_COLORS.get(e["phase"], "#616161")
            chips.append(_phase_chip(
                f"{t('weather.enso', lang)}: {e['phase']}",
                f"({e['value']:+.2f}, {e['season']})",
                color,
            ))
        else:
            chips.append(_phase_chip(t("weather.enso", lang), unavail, "#9e9e9e"))
        if climate.get("iod"):
            i = climate["iod"]
            color = _IOD_COLORS.get(i["phase"], "#616161")
            chips.append(_phase_chip(
                f"{t('weather.iod', lang)}: {i['phase']}",
                f"({i['value']:+.2f}, {i['month']})",
                color,
            ))
        else:
            chips.append(_phase_chip(t("weather.iod", lang), unavail, "#9e9e9e"))

        sources = []
        if climate.get("enso"): sources += climate["enso"].get("sources", [])
        if climate.get("iod"):  sources += climate["iod"].get("sources", [])
        src_line = " · ".join(sorted(set(sources))) if sources else "—"

        st.markdown(
            f"##### {t('weather.climate_signal', lang)} {_BADGE_LLM if False else ''}",
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="margin-bottom:8px;">{"".join(chips)}</div>'
            f'<div style="font-size:0.75rem;color:#666;">Source: {src_line}</div>',
            unsafe_allow_html=True,
        )
        st.divider()

        # 2. 7-day forecast for the selected user location
        st.markdown(f"##### {t('weather.forecast_title', lang)}")
        if selected:
            try:
                fc = weather_tool.fetch_forecast(selected["lat"], selected["lng"])
            except Exception as e:
                fc = None
                st.caption(f"forecast fetch failed: {e}")
            if fc and fc.get("days"):
                fdf = pd.DataFrame(fc["days"])
                fdf["date"] = pd.to_datetime(fdf["date"])
                fdf = fdf.set_index("date")
                temp_df = fdf[["tmax", "tmin"]].rename(
                    columns={"tmax": "Max °C", "tmin": "Min °C"}
                )
                st.line_chart(temp_df)
                rain_df = fdf[["precip_mm"]].rename(columns={"precip_mm": "Rain (mm)"})
                st.bar_chart(rain_df)
                st.caption(
                    f"Source: Open-Meteo · for "
                    f"{selected['display_name'][:80]} · "
                    f"fetched {fc['fetched_at']}"
                )
            else:
                st.caption("forecast unavailable")
        else:
            st.info(t("weather.location_needed", lang))
        st.divider()

        # 3. Crop calendar card
        st.markdown(
            t("weather.calendar_title", lang, crop=crop, state=state)
        )
        cal_entry = _CROP_CALENDAR.get(state, {}).get(crop)
        if not cal_entry:
            st.caption(t("weather.no_calendar", lang))
        else:
            cur_month_short = datetime.now().strftime("%b")
            def _highlight_if_current(window: str | None) -> str:
                if not window:
                    return "—"
                # crude: highlight if current month abbrev is mentioned
                if cur_month_short in window:
                    return f"**{window}** ⬅"
                return window

            cc1, cc2, cc3 = st.columns(3)
            cc1.metric(t("weather.cal_sow", lang),
                       _highlight_if_current(cal_entry.get("sow")))
            tp = cal_entry.get("transplant")
            if tp:
                cc2.metric(t("weather.cal_transplant", lang),
                           _highlight_if_current(tp))
            else:
                cc2.metric(t("weather.cal_transplant", lang), "—")
            cc3.metric(t("weather.cal_harvest", lang),
                       _highlight_if_current(cal_entry.get("harvest")))

            st.markdown(
                f"**{t('weather.cal_critical', lang)}** — "
                f"{cal_entry.get('critical_weather', '—')}"
            )
            if cal_entry.get("season"):
                st.caption(f"Season: {cal_entry['season']}")

    with tab_context:
        st.markdown(
            f"### About {crop} in {state} {_BADGE_LLM}",
            unsafe_allow_html=True,
        )
        with st.spinner("Generating info section..."):
            try:
                st.markdown(info_section(state, crop, language=lang))
            except Exception as e:
                st.error(f"Info section failed: {e}")

        st.markdown(
            f"### Government schemes — from growing to selling {_BADGE_LLM}",
            unsafe_allow_html=True,
        )
        try:
            matches = schemes.list_schemes(crop=crop)
        except Exception as e:
            st.error(f"Scheme lookup failed: {e}")
            matches = []

        if not matches:
            st.info("No schemes in data/schemes.json match this crop.")
        else:
            stage_order = [
                ("growing", "Before & during growing"),
                ("insurance", "Protect your crop"),
                ("selling", "At selling time"),
            ]
            by_stage: dict[str, list[dict]] = {k: [] for k, _ in stage_order}
            for s in matches:
                by_stage.setdefault(s.get("stage", "growing"), []).append(s)

            top_scheme = next(
                (by_stage[k][0] for k, _ in stage_order if by_stage.get(k)),
                None,
            )
            if top_scheme:
                st.markdown(f"**Start here — {top_scheme['name']}**")
                with st.spinner("Generating plain-English explainer..."):
                    try:
                        st.markdown("**What it is**")
                        st.markdown(explain_scheme(top_scheme, language=lang))
                        st.markdown("**When it helps you**")
                        st.markdown(scheme_usecase(top_scheme, state, crop, language=lang))
                    except Exception as e:
                        st.error(f"LLM failed: {e}")
                st.divider()

            shown_more = False
            for stage_key, stage_label in stage_order:
                bucket = [s for s in by_stage.get(stage_key, []) if s is not top_scheme]
                if not bucket:
                    continue
                if not shown_more:
                    st.markdown("**More schemes**")
                    shown_more = True
                st.markdown(f"_{stage_label}_")
                for s in bucket:
                    with st.expander(s["name"]):
                        load_key = f"load_{s['name']}"
                        if st.button("Explain in plain English", key=load_key):
                            with st.spinner("Writing plain-English rewrite..."):
                                try:
                                    st.markdown("**What it is**")
                                    st.markdown(explain_scheme(s, language=lang))
                                    st.markdown("**When it helps you**")
                                    st.markdown(scheme_usecase(s, state, crop, language=lang))
                                except Exception as e:
                                    st.error(f"LLM failed: {e}")
                        else:
                            st.caption("Click above for layman explanation + use cases.")
