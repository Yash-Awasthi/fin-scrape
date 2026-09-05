"""Developer mode: bring-your-own API keys for arbitrary external tools.

The universe of tools is infinite, so this is organized by tool CLASS (the
"columns" you see in dev mode) rather than by product. Any new tool fits an
existing class — web_search, ai, news_fetch, market_data, alerts, geo_intel —
or the escape-hatch `custom` class. Each class declares its config FIELDS
(api_key, base_url, model, bot_token, ...); within a class you register any
number of NAMED providers and mark one active.

Storage: secrets/dev_tools.json (secrets/ is gitignored — keys never enter
the repo). `mode: "dev"` must be set for any of this to take effect; with any
other mode the rest of the file is inert and finscrape behaves exactly as
before.

Wiring: `apply_to_env()` (called by main.py at startup in dev mode) projects
the active AI provider onto OPENAI_BASE_URL / OPENAI_API_KEY / FINSCRAPE_MODEL
and tool keys onto provider-specific env vars (FIRECRAWL_API_KEY,
SERPAPI_API_KEY, ...) so the existing config plumbing picks everything up
without each module knowing about dev mode.

CLI:
    python main.py devtools list
    python main.py devtools set ai ollama --field base_url=http://localhost:11434/v1 --field model=qwen2.5:7b
    python main mode: devtools set web_search serpapi --field api_key=... --activate
    python main.py devtools test ai
    python main.py devtools path
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

# The "columns" of dev mode. `fields` are the config keys a provider in this
# class may carry; `providers` are pre-declared known names (any other name
# is accepted too and created on first `devtools set`).
TOOL_CLASSES: dict[str, dict[str, Any]] = {
    "ai": {
        "label": "AI / LLM providers",
        "fields": ["api_key", "base_url", "model"],
        "env_map": {"api_key": "OPENAI_API_KEY", "base_url": "OPENAI_BASE_URL", "model": "FINSCRAPE_MODEL"},
        "providers": {
            "ollama": {"base_url": "http://localhost:11434/v1", "model": "qwen2.5:7b"},
            "openrouter": {},
            "openai": {},
            "freemodel": {},
        },
    },
    "web_search": {
        "label": "Web search APIs",
        "fields": ["api_key", "base_url", "engine"],
        "env_map": {},
        "providers": {"serp": {}, "serpapi": {}, "tavily": {}, "brave": {}, "google_cse": {}},
    },
    "news_fetch": {
        "label": "News fetch / scraping tools",
        "fields": ["api_key", "base_url"],
        "env_map": {},
        "providers": {
            "firecrawl": {"base_url": "https://api.firecrawl.dev"},
            "tinyfish": {},
            "scrapingbee": {},
        },
    },
    "market_data": {
        "label": "Market data APIs",
        "fields": ["api_key", "base_url"],
        "env_map": {},
        "providers": {"alphavantage": {}, "polygon": {}, "finnhub": {}},
    },
    "geo_intel": {
        "label": "Geo / intel APIs",
        "fields": ["api_key", "base_url"],
        "env_map": {},
        "providers": {},
    },
    "alerts": {
        "label": "Alert channels",
        "fields": ["bot_token", "chat_id", "api_key", "webhook_url"],
        "env_map": {},
        "providers": {"telegram": {}, "discord": {}, "slack": {}},
    },
    "custom": {
        "label": "Anything else (generic api_key/base_url columns)",
        "fields": ["api_key", "base_url"],
        "env_map": {},
        "providers": {},
    },
}


def _project_root() -> Path:
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (parent / "main.py").exists() or (parent / ".git").exists():
            return parent
    return current.parent


def config_path() -> Path:
    override = os.environ.get("FINSCRAPE_DEV_TOOLS_PATH")
    return Path(override) if override else _project_root() / "secrets" / "dev_tools.json"


def load() -> dict:
    """Load the dev-tools config, creating a fresh skeleton if absent."""
    path = config_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
    return {"mode": "off", "tools": {}}


def save(cfg: dict) -> Path:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def is_dev_mode() -> bool:
    return load().get("mode") == "dev"


def set_mode(mode: str) -> None:
    assert mode in ("dev", "off"), "mode must be 'dev' or 'off'"
    cfg = load()
    cfg["mode"] = mode
    save(cfg)


def set_provider(tool_class: str, name: str, fields: dict[str, str], activate: bool = True) -> dict:
    """Create or update a provider under a tool class and (by default) make it active.

    Unknown tool classes land in `custom`; unknown providers are created on the fly —
    the tool universe is open-ended.
    """
    if tool_class not in TOOL_CLASSES:
        tool_class = "custom"
    spec = TOOL_CLASSES[tool_class]
    cfg = load()
    tools = cfg.setdefault("tools", {})
    entry = tools.setdefault(tool_class, {"active": "", "providers": {}})
    providers = entry.setdefault("providers", {})
    known = providers.get(name, dict(spec["providers"].get(name, {})))
    known.update({k: v for k, v in fields.items() if v})
    providers[name] = known
    if activate:
        entry["active"] = name
    save(cfg)
    return {"tool_class": tool_class, "provider": name, "fields": known, "active": entry["active"]}


def get_provider(tool_class: str, name: str) -> dict | None:
    """Fields for one named provider, regardless of active state."""
    entry = load().get("tools", {}).get(tool_class, {})
    fields = entry.get("providers", {}).get(name)
    return dict(fields) if fields else None


def get_active(tool_class: str) -> dict | None:
    """{'provider': name, 'fields': {...}} for the active provider of a class.

    None unless dev mode is on and the class has an active provider.
    """
    if not is_dev_mode():
        return None
    entry = load().get("tools", {}).get(tool_class, {})
    name = entry.get("active", "")
    fields = entry.get("providers", {}).get(name)
    if not name or fields is None:
        return None
    return {"provider": name, "fields": dict(fields)}


def apply_to_env() -> list[str]:
    """Project active dev-mode providers onto environment variables.

    Only the AI class maps to env today (OPENAI_* / FINSCRAPE_MODEL — the
    existing config plumbing reads those); other classes expose their keys via
    devmode.get_active/get_provider at use sites. Returns the env names set.
    """
    applied: list[str] = []
    active = get_active("ai")
    if not active:
        return applied
    env_map = TOOL_CLASSES["ai"]["env_map"]
    for field, env_name in env_map.items():
        value = active["fields"].get(field)
        if value:
            os.environ[env_name] = str(value)
            applied.append(env_name)
    return applied


def status() -> dict:
    """Summary for the CLI: mode + every class with its providers/active."""
    cfg = load()
    tools = cfg.get("tools", {})
    out: dict[str, Any] = {"mode": cfg.get("mode", "off"), "path": str(config_path()), "classes": {}}
    for cls, spec in TOOL_CLASSES.items():
        entry = tools.get(cls, {})
        out["classes"][cls] = {
            "label": spec["label"],
            "fields": spec["fields"],
            "providers": sorted(set(spec["providers"]) | set(entry.get("providers", {}))),
            "active": entry.get("active", ""),
        }
    return out
