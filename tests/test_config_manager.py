"""Tests for config manager service."""

import pytest
from finscrape.services.config_manager import (
    parse_provider_string,
    build_fallback_chain,
    check_rate_limit,
    calculate_cooldown,
    load_from_env,
    validate_config,
    mask_api_key,
    validate_api_key_format,
)


class TestProviderParsing:
    def test_parse_simple(self):
        provider, model = parse_provider_string("ollama")
        assert provider == "ollama"
        assert model == ""

    def test_parse_with_model(self):
        provider, model = parse_provider_string("ollama:qwen3.6:35b-a3b")
        assert provider == "ollama"
        assert model == "qwen3.6:35b-a3b"

    def test_build_chain(self):
        chain = build_fallback_chain("ollama", "gemini:gemini-2.5-flash,openai")
        assert chain.primary.name == "ollama"
        assert len(chain.fallbacks) == 2
        assert chain.fallbacks[0].name == "gemini"


class TestRateLimit:
    def test_check_not_limited(self):
        limited, wait = check_rate_limit(
            __import__('finscrape.services.config_manager', fromlist=['LLMProviderConfig']).LLMProviderConfig(name="test"),
            1000.0, {},
        )
        assert not limited

    def test_check_limited(self):
        limited, wait = check_rate_limit(
            __import__('finscrape.services.config_manager', fromlist=['LLMProviderConfig']).LLMProviderConfig(name="test"),
            1000.0, {"test": 2000.0},
        )
        assert limited

    def test_cooldown_calculation(self):
        assert calculate_cooldown(0) == 60.0
        assert calculate_cooldown(1) == 120.0
        assert calculate_cooldown(2) == 240.0


class TestValidation:
    def test_validate_config(self):
        missing = validate_config({"a": "1", "b": ""}, ["a", "b", "c"])
        assert "b" in missing
        assert "c" in missing

    def test_mask_api_key(self):
        assert mask_api_key("sk-1234567890") == "*********7890"
        assert mask_api_key("ab") == "**"

    def test_validate_api_key_format(self):
        assert validate_api_key_format("sk-12345", "sk-")
        assert not validate_api_key_format("", "sk-")
        assert not validate_api_key_format("bad-1234", "sk-")
