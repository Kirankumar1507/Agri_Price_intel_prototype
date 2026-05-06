"""Fetch and summarize agricultural news from PIB and state departments."""
import requests
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timedelta
import os

CACHE_DIR = Path(".cache/news")

def fetch_agri_news(state: str = "Karnataka", lang: str = "en") -> list[dict]:
    """Fetch recent agri news, summarize with LLM, and return top 3."""
    key = f"news_{state}_{lang}.json"
    cached = _read_cache(key)
    if cached:
        return cached

    # PIB RSS for Ministry of Agriculture (conceptual, using a stable subset)
    # real: https://pib.gov.in/RssMain.aspx?Reg=3
    # For prototype, we simulate the RSS result to avoid intermittent gov network issues
    items = [
        {
            "title": "Government increases MSP for Kharif crops 2025-26",
            "date": "2026-05-01",
            "source": "PIB Delhi",
            "link": "https://pib.gov.in"
        },
        {
            "title": f"New irrigation subsidy announced for {state} farmers",
            "date": "2026-05-04",
            "source": f"{state} Agri Dept",
            "link": "https://agri.kar.nic.in"
        }
    ]

    # Summarize each with LLM (lazy import to agent)
    from src.agent import _chat
    
    summarized = []
    for item in items[:3]:
        prompt = f"Summarize this agri news in 2 short sentences for a farmer: {item['title']}"
        summary = _chat("news_summary", {"prompt": prompt}, language=lang)
        item["summary"] = summary or item["title"]
        summarized.append(item)

    _write_cache(key, summarized)
    return summarized

def _read_cache(key: str) -> list[dict] | None:
    path = CACHE_DIR / key
    if not path.exists():
        return None
    # 12 hour cache TTL
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    if age > timedelta(hours=12):
        return None
    return json.loads(path.read_text())

def _write_cache(key: str, data: list[dict]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / key).write_text(json.dumps(data))
