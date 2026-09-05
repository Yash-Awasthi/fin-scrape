"""Tests for dev-mode tool registry and the market-relevance gate."""

import pytest

from finscrape.analysis.validator import (
    calculate_sentence_sentiment,
    is_market_relevant,
)
from finscrape.devmode import (
    TOOL_CLASSES,
    config_path,
    get_active,
    load,
    save,
    set_provider,
)

# ── dev-mode registry ────────────────────────────────────────────────────────

@pytest.fixture()
def tmp_devtools(tmp_path, monkeypatch):
    monkeypatch.setenv("FINSCRAPE_DEV_TOOLS_PATH", str(tmp_path / "dev_tools.json"))
    return tmp_path / "dev_tools.json"


def test_fresh_config_is_off(tmp_devtools):
    assert load()["mode"] == "off"
    assert get_active("ai") is None  # off → providers inert


def test_set_provider_activates(tmp_devtools):
    set_provider("news_fetch", "firecrawl", {"api_key": "fc-123"})
    cfg = load()
    assert cfg["tools"]["news_fetch"]["active"] == "firecrawl"
    assert cfg["tools"]["news_fetch"]["providers"]["firecrawl"]["api_key"] == "fc-123"
    # known provider presets survive (base_url default kept)
    assert "firecrawl.dev" in cfg["tools"]["news_fetch"]["providers"]["firecrawl"]["base_url"]


def test_activate_requires_dev_mode(tmp_devtools):
    set_provider("ai", "ollama", {"base_url": "http://localhost:11434/v1", "model": "qwen2.5:7b"})
    assert get_active("ai") is None  # mode still off
    cfg = load()
    cfg["mode"] = "dev"
    save(cfg)
    active = get_active("ai")
    assert active["provider"] == "ollama"
    assert active["fields"]["model"] == "qwen2.5:7b"


def test_unknown_class_and_provider_land_gracefully(tmp_devtools):
    result = set_provider("some_unheard_class", "my_tool_xyz", {"api_key": "k1"})
    assert result["tool_class"] == "custom"  # unknown class → custom bucket
    set_provider("web_search", "brand_new_engine", {"api_key": "k2"})
    assert "brand_new_engine" in load()["tools"]["web_search"]["providers"]


def test_every_tool_class_declares_fields():
    for cls, spec in TOOL_CLASSES.items():
        assert spec["fields"], f"{cls} must declare its columns"


def test_config_path_respects_override(tmp_devtools):
    assert str(config_path()) == str(tmp_devtools)


# ── market-relevance gate ────────────────────────────────────────────────────

def test_lifestyle_junk_rejected():
    assert not is_market_relevant(
        "I'm a nutritionist from Japan: 7 essential anti-inflammatory foods",
        "These foods reduce inflammation and I swear by them every morning.",
    )


def test_minor_quake_without_market_angle_rejected():
    assert not is_market_relevant(
        "M4.8 earthquake strikes remote region",
        "A magnitude 4.8 earthquake struck a sparsely populated area. No injuries were reported.",
    )


def test_major_quake_with_market_angle_kept():
    assert is_market_relevant(
        "M7.2 earthquake strikes Tokyo region",
        "Insurers face billions in damage claims; stocks fell and supply chains face disruption.",
    )


def test_normal_market_news_kept():
    assert is_market_relevant(
        "Nvidia earnings surge on AI chip demand",
        "Revenue rose 20% beating estimates; data center demand remains exceptional.",
    )


# ── scoring blend ────────────────────────────────────────────────────────────

def test_positive_scoring_detects_bullish_text():
    label, score = calculate_sentence_sentiment(
        "Revenue surged 50% beating all estimates with exceptional growth."
    )
    assert label == "positive"
    assert score > 0


def test_negative_scoring_detects_bearish_text():
    label, score = calculate_sentence_sentiment(
        "The company crashes after bankruptcy filing and massive losses."
    )
    assert label == "negative"
    assert score < 0


def test_neutral_scoring_for_plain_text():
    label, _ = calculate_sentence_sentiment("The market opened today.")
    assert label == "neutral"
