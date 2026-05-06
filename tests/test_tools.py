import json
from pathlib import Path

import pytest

from src.tools import geo, schemes


def test_haversine_self_distance_is_zero():
    d = geo._haversine(12.97, 77.59, 12.97, 77.59)
    assert float(d) == pytest.approx(0.0, abs=1e-6)


def test_haversine_blr_to_mys_is_reasonable():
    # Bangalore → Mysore straight-line ~ 127 km
    d = geo._haversine(12.9716, 77.5946, 12.2958, 76.6394)
    assert 120 < float(d) < 140


def test_schemes_json_valid():
    data = json.loads(Path("data/schemes.json").read_text())
    assert isinstance(data, list) and data
    required = {"name", "applicable_crops", "districts", "eligibility", "benefit", "how_to_apply", "source_url"}
    for s in data:
        assert required.issubset(s.keys()), f"missing keys in {s.get('name')}"


def test_schemes_filter_by_crop():
    ragi = schemes.list_schemes(crop="Ragi")
    names = {s["name"] for s in ragi}
    assert "Raitha Siri (Millet Incentive)" in names
    assert "PM-KISAN" in names  # 'all' crops


def test_schemes_filter_excludes_unrelated():
    tur = schemes.list_schemes(crop="Tur")
    names = {s["name"] for s in tur}
    assert "Raitha Siri (Millet Incentive)" not in names
