"""i18n completeness guard — turns 'no English leakage' into a CI gate.

Hermetic: reads app.py as text and imports only src.i18n (no Streamlit).
Fails if any UI string key referenced via t(...) is missing from LABELS, or if
any LABELS entry lacks a non-empty translation in English, Kannada, or Hindi.
"""
from __future__ import annotations

import pathlib
import re

from src import i18n

_APP = pathlib.Path(__file__).resolve().parent.parent / "app.py"
_LANGS = ("en", "kn", "hi")

# Keys used indirectly (not as literal t("...") calls) — e.g. via _VERDICT_STYLE.
_INDIRECT_KEYS = {
    "verdict.sell_now", "verdict.store", "verdict.travel",
    "verdict.wait", "verdict.verify",
}


def _referenced_keys() -> set[str]:
    src = _APP.read_text(encoding="utf-8")
    # Standalone t("key") / t('key') — the negative lookbehind excludes get(, format(, etc.
    return set(re.findall(r'(?<![A-Za-z0-9_])t\(\s*["\']([^"\']+)["\']', src))


def test_all_referenced_keys_exist():
    missing = sorted(
        k for k in (_referenced_keys() | _INDIRECT_KEYS) if k not in i18n.LABELS
    )
    assert not missing, f"i18n keys referenced but missing from LABELS: {missing}"


def test_every_label_has_all_three_languages():
    incomplete = {
        key: [lang for lang in _LANGS if not entry.get(lang)]
        for key, entry in i18n.LABELS.items()
        if any(not entry.get(lang) for lang in _LANGS)
    }
    assert not incomplete, f"LABELS entries missing translations: {incomplete}"


def test_t_falls_back_safely():
    # Missing key → returns the key itself (visible, not a crash).
    assert i18n.t("no.such.key", "kn") == "no.such.key"
    # Known key resolves per language and never returns the raw key.
    assert i18n.t("verdict.sell_now", "hi") != "verdict.sell_now"
    assert i18n.t("verdict.sell_now", "kn") != "verdict.sell_now"
