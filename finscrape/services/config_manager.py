"""Configuration Manager.

Extracted from OracleX (inspiration).
Centralized configuration with environment variable loading,
validation, provider fallback chains, and rate limit management.

All pure functions — no DB, no async.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMProviderConfig:
    """Configuration for an LLM provider."""
    name: str
    model: str = ""
    base_url: str = ""
    api_key: str = ""
    max_retries: int = 3
    timeout: float = 30.0
    rate_limit_cooldown: float = 60.0
    daily_quota_cooldown: float = 1800.0


@dataclass
class ProviderFallbackChain:
    """Fallback chain for LLM providers."""
    primary: LLMProviderConfig
    fallbacks: list[LLMProviderConfig] = field(default_factory=list)
    current_index: int = 0
    cooldown_until: dict[str, float] = field(default_factory=dict)

    def get_active_provider(self) -> LLMProviderConfig:
        """Get the currently active provider."""
        if self.current_index == 0:
            return self.primary
        if self.current_index <= len(self.fallbacks):
            return self.fallbacks[self.current_index - 1]
        return self.primary

    def should_fallback(self, provider_name: str, current_time: float) -> bool:
        """Check if we should fallback from a provider."""
        cooldown = self.cooldown_until.get(provider_name, 0)
        return current_time >= cooldown

    def set_cooldown(self, provider_name: str, cooldown_seconds: float, current_time: float) -> None:
        """Set cooldown for a provider."""
        self.cooldown_until[provider_name] = current_time + cooldown_seconds


@dataclass
class MarketDataConfig:
    """Market data configuration."""
    stream_exchange: str = "okx"
    default_symbols: list[str] = field(default_factory=lambda: ["BTC/USDT", "ETH/USDT"])
    websocket_url: str = ""
    rest_url: str = ""


@dataclass
class AppConfig:
    """Main application configuration."""
    llm: ProviderFallbackChain = field(default_factory=lambda: ProviderFallbackChain(
        primary=LLMProviderConfig(name="ollama", model="qwen3.6:35b-a3b")
    ))
    market_data: MarketDataConfig = field(default_factory=MarketDataConfig)
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    encryption_secret: str = ""


# --- Provider Parsing ---

def parse_provider_string(provider_str: str) -> tuple[str, str]:
    """Parse provider string into (provider, model).

    Supports formats: "provider", "provider:model", "provider:model:variant"

    Args:
        provider_str: Provider configuration string

    Returns:
        Tuple of (provider_name, model_name)
    """
    parts = provider_str.split(":", 1)
    provider = parts[0].strip()
    model = parts[1].strip() if len(parts) > 1 else ""
    return provider, model


def build_fallback_chain(
    primary_str: str,
    fallback_str: str = "",
    default_model: str = "",
) -> ProviderFallbackChain:
    """Build a provider fallback chain from config strings.

    Args:
        primary_str: Primary provider string
        fallback_str: Comma-separated fallback providers
        default_model: Default model when not specified

    Returns:
        Provider fallback chain
    """
    primary_name, primary_model = parse_provider_string(primary_str)
    primary = LLMProviderConfig(
        name=primary_name,
        model=primary_model or default_model,
    )

    fallbacks = []
    if fallback_str:
        for fb_str in fallback_str.split(","):
            fb_str = fb_str.strip()
            if fb_str:
                fb_name, fb_model = parse_provider_string(fb_str)
                fallbacks.append(LLMProviderConfig(
                    name=fb_name,
                    model=fb_model or default_model,
                ))

    return ProviderFallbackChain(primary=primary, fallbacks=fallbacks)


# --- Rate Limiting ---

def check_rate_limit(
    provider: LLMProviderConfig,
    current_time: float,
    cooldown_until: dict[str, float],
    max_wait: float = 30.0,
) -> tuple[bool, float]:
    """Check if a provider is rate-limited.

    Args:
        provider: Provider config
        current_time: Current timestamp
        cooldown_until: Dict of provider -> cooldown timestamp
        max_wait: Maximum wait time before giving up

    Returns:
        Tuple of (is_limited, wait_seconds)
    """
    cooldown = cooldown_until.get(provider.name, 0)
    if current_time < cooldown:
        wait = cooldown - current_time
        if wait > max_wait:
            return True, 0.0  # Give up, use fallback
        return True, wait
    return False, 0.0


def calculate_cooldown(
    attempt: int,
    base_cooldown: float = 60.0,
    max_cooldown: float = 1800.0,
) -> float:
    """Calculate exponential backoff cooldown.

    Args:
        attempt: Current retry attempt
        base_cooldown: Base cooldown in seconds
        max_cooldown: Maximum cooldown in seconds

    Returns:
        Cooldown in seconds
    """
    cooldown = base_cooldown * (2 ** min(attempt, 10))
    return min(cooldown, max_cooldown)


# --- Configuration Loading ---

def load_from_env(prefix: str = "", defaults: dict[str, str] = None) -> dict[str, str]:
    """Load configuration from environment variables.

    Args:
        prefix: Optional prefix for env var names
        defaults: Default values

    Returns:
        Dictionary of configuration values
    """
    config = defaults or {}

    for key, value in config.items():
        env_key = f"{prefix}{key}" if prefix else key
        env_value = os.environ.get(env_key)
        if env_value is not None:
            config[key] = env_value

    return config


def validate_config(config: dict[str, str], required_keys: list[str]) -> list[str]:
    """Validate configuration has required keys.

    Args:
        config: Configuration dictionary
        required_keys: List of required key names

    Returns:
        List of missing key names
    """
    return [key for key in required_keys if key not in config or not config[key]]


# --- Encryption Helpers ---

def mask_api_key(key: str, visible_chars: int = 4) -> str:
    """Mask an API key for display.

    Args:
        key: API key to mask
        visible_chars: Number of visible characters at end

    Returns:
        Masked key string
    """
    if len(key) <= visible_chars:
        return "*" * len(key)
    return "*" * (len(key) - visible_chars) + key[-visible_chars:]


def validate_api_key_format(key: str, expected_prefix: str = "") -> bool:
    """Validate API key format.

    Args:
        key: API key to validate
        expected_prefix: Expected prefix (e.g., "sk-")

    Returns:
        True if format is valid
    """
    if not key:
        return False
    if expected_prefix and not key.startswith(expected_prefix):
        return False
    return True
