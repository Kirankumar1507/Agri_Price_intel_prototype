# 🌾 Agri Price Intel

**Location-aware market intelligence for Indian farmers** — find the best APMC mandi to sell your crop, adjusted for transport cost, with LLM-powered narratives in English, Kannada, and Hindi.

![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40-ff4b4b?style=flat&logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)
![Cost](https://img.shields.io/badge/Cost-₹0/month-0b5d0b?style=flat)

---

## The Problem

Every year, Indian farmers lose ₹thousands per quintal selling at the **nearest** mandi instead of the **best** one. The price data is public ([data.gov.in](https://data.gov.in)). The distance is calculable. The math is simple:

> **modal price − ₹5/km transport = net price**

Nobody is doing this subtraction for the farmer. This tool does.

## What It Does

| Feature | Description |
|---------|-------------|
| **Best Mandi Finder** | Transport-adjusted ₹/qtl — not just highest price, but highest *net* price after ₹5/km deduction |
| **Actionable Verdict** | Deterministic engine: `sell_now` / `store` / `travel` / `wait` / `verify` based on price trends, arbitrage gaps, and data freshness |
| **MSP Comparison** | Shows whether the market price is above or below Minimum Support Price (2025-26 CACP rates) |
| **Interactive Map** | Color-coded pins: your location, best mandi, nearest 5, crop-reporting mandis, and all other mandis |
| **15-Day Price Trends** | Multi-mandi line chart with comparison selector |
| **7-Day Weather** | Temperature + rainfall forecast for your location (Open-Meteo) |
| **Climate Signals** | ENSO (El Niño/La Niña) + IOD phase from NOAA — affects monsoon and crop planning |
| **Crop Calendar** | Sow/transplant/harvest windows + critical weather alerts per crop-state pair |
| **Government Schemes** | 11 schemes (PM-KISAN, PMFBY, KCC, eNAM, Raitha Siri, etc.) with LLM plain-language explainers |
| **Multi-Language** | English 🇬🇧 · ಕನ್ನಡ 🇮🇳 · हिन्दी 🇮🇳 — UI labels + LLM content |
| **Production History** | Area/Production/Yield from DES (1997–2014) with trend charts |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  DATA SOURCES (all free/open)                                │
│  ├── data.gov.in Agmarknet API → live mandi prices (90d)    │
│  ├── Open-Meteo → 7-day forecast                            │
│  ├── NOAA CPC/PSL → ENSO + IOD climate signals              │
│  └── Nominatim (OSM) → geocoding                            │
├─────────────────────────────────────────────────────────────┤
│  INTELLIGENCE LAYER                                          │
│  ├── Deterministic Engine → verdict (sell/store/travel/...)  │
│  │   └── Rules: trend %, arbitrage gap, data staleness       │
│  └── LLM Layer (Ollama, local) → narratives only             │
│      └── Market overview, verdict headline, scheme rewrite   │
├─────────────────────────────────────────────────────────────┤
│  FRONTEND — Streamlit                                        │
│  ├── Folium map with teardrop SVG pins                       │
│  ├── Verdict callout banner                                  │
│  ├── MSP comparison bar                                      │
│  ├── Price trend charts (Pandas + Streamlit charts)          │
│  └── 4 tabs: Market Intel | Production | Weather | Schemes   │
└─────────────────────────────────────────────────────────────┘
```

**Key design choice**: The decision engine is **deterministic** (rule-based, auditable). The LLM only generates natural-language explanations — never the recommendation itself.

## Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai/) installed and running
- A free API key from [data.gov.in](https://data.gov.in/)

### Setup

```bash
# Clone
git clone https://github.com/<your-username>/agri-price-intel.git
cd agri-price-intel

# Virtual environment
python -m venv .venv
source .venv/bin/activate

# Dependencies
pip install -r requirements.txt

# Pull the LLM model
ollama pull gemma4:e4b
# or: ollama pull qwen2.5:7b-instruct

# Environment
cp .env.example .env
# Edit .env → add your DATA_GOV_API_KEY
```

### Run

```bash
streamlit run app.py
```

Open `http://localhost:8501` → pick a state, crop, and location → click **Get market intelligence**.

### Demo Mode

Click the **"Try demo — Ragi from Bengaluru, KA"** button on the landing page for a one-click walkthrough with pre-filled data.

## Coverage

| State | Crops | Mandis |
|-------|-------|--------|
| **Karnataka** | Ragi, Paddy, Tur, Jowar, Maize, Sugarcane, Cotton, Groundnut, Bengal Gram, Green Gram, Onion, Tomato, Potato | ~150 |
| **Haryana** | Wheat, Paddy, Mustard, Bajra, Cotton, Sugarcane, Bengal Gram, Groundnut, Onion, Tomato, Potato | ~80 |

Adding a new state is a config change — add the state dict to `src/config.py`, add crop calendar entries to `data/crop_calendar.json`, and the app works.

## Data Sources

| Source | What | Update Frequency | Cost |
|--------|------|-------------------|------|
| [data.gov.in Agmarknet](https://data.gov.in/) | APMC mandi prices (variety-wise) | Daily | Free (API key) |
| [Open-Meteo](https://open-meteo.com/) | Weather forecast | 6-hourly | Free (no key) |
| [NOAA CPC](https://www.cpc.ncep.noaa.gov/) | ENSO (ONI) | Monthly | Free (no key) |
| [NOAA PSL](https://psl.noaa.gov/) | IOD (DMI) | Monthly | Free (no key) |
| [Nominatim](https://nominatim.openstreetmap.org/) | Geocoding | On demand | Free (rate-limited) |
| [data.gov.in DES](https://data.gov.in/) | APY (1997–2014) | Frozen | Free (API key) |

## Known Limitations

- **District centroid geocoding**: Mandi pins are placed at district centroids, not exact APMC addresses. Multiple mandis in the same district will overlap on the map. This is because Nominatim doesn't index APMC names reliably (~10% hit rate in tests). Phase 2: hand-curated lat/lng file for major APMCs.
- **Haversine distance**: Straight-line distance, not road distance. An OSRM integration exists (`src/tools/distance.py`) but isn't wired into the main pipeline yet.
- **APY data frozen at 2014**: The DES crop production API on data.gov.in hasn't been updated since 2014. Current data (through 2022-23) is behind auth at `data.upag.gov.in`.
- **2 states only**: The Agmarknet API covers all Indian states — scaling is a config change, not a data problem.
- **MSP rates curated manually**: Updated for 2025-26 marketing season. Need to update annually when CACP notifications are released.

## Project Structure

```
agri_location_intel/
├── app.py                  # Streamlit main app (805 lines)
├── src/
│   ├── agent.py            # Market analysis pipeline + LLM calls
│   ├── config.py           # States, crops, API resource IDs
│   ├── i18n.py             # Translation tables (en/kn/hi)
│   ├── prompts/            # LLM system prompts (5 files)
│   └── tools/
│       ├── mandi_prices.py # Agmarknet API + 24h cache
│       ├── geo.py          # Haversine, mandi table builder
│       ├── geocoder.py     # Freeform address search (Nominatim)
│       ├── mandi_geocoder.py # District centroid geocoding
│       ├── msp.py          # MSP rate lookup
│       ├── apy.py          # DES crop production API
│       ├── weather.py      # Open-Meteo 7-day forecast
│       ├── climate.py      # ENSO + IOD from NOAA
│       ├── schemes.py      # Government scheme matcher
│       └── distance.py     # OSRM road distance (unused)
├── data/
│   ├── schemes.json        # 11 curated government schemes
│   ├── crop_calendar.json  # Sow/harvest/critical weather
│   └── msp_rates.json      # MSP rates 2025-26
├── scripts/
│   ├── seed_mandis.py      # Enumerate + geocode Karnataka mandis
│   └── seed_taluks.py      # Taluk-level seeding
├── tests/
│   └── test_tools.py       # Haversine + scheme matching tests
├── walkthrough/            # Static walkthrough page
├── .streamlit/config.toml  # Theme configuration
├── requirements.txt
├── .env.example
└── .gitignore
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit · Folium · Pandas charts |
| LLM | Ollama (local) — Gemma 4 / Qwen 2.5 |
| Data APIs | data.gov.in · Open-Meteo · NOAA · Nominatim |
| Language | Python 3.11+ |
| Caching | File-backed JSON (24h mandi, 6h weather, 7d climate) |

## Contributing

This is a proof-of-concept. Contributions welcome:

1. **Add states**: Add a state config to `src/config.py` + crop calendar entries
2. **Add schemes**: Add to `data/schemes.json` following the existing schema
3. **Improve geocoding**: Hand-curate lat/lng for major APMCs in `data/` 
4. **Wire road distance**: Connect `src/tools/distance.py` (OSRM) into the pipeline

## License

MIT — free for personal and commercial use.
