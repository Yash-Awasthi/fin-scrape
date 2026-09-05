"""
ZAI Oracle — Configuration
by Zawwar (github.com/Zawwarsami16)

Loads everything from .env file automatically.
You never touch this file — only edit .env.

If a key is missing, the system degrades gracefully:
- No Etherscan key → skip ETH whale tracking
- No AI key → use rule-based prediction
- No Telegram → skip alerts
Everything still runs, just with less data.
"""

import os


def _load_env():
    """
    Reads .env file manually — no external library needed.
    Works on any machine without installing python-dotenv.
    """
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key   = key.strip()
            value = value.strip().strip('"').strip("'")
            if value:
                os.environ.setdefault(key, value)


_load_env()


def _get(key, fallback=""):
    return os.environ.get(key, fallback).strip()


# ----------------------------------------------------------------
# AI Keys — all optional, system picks best available
# ----------------------------------------------------------------
GROQ_KEY      = _get("GROQ_KEY")
GEMINI_KEY    = _get("GEMINI_KEY")
ANTHROPIC_KEY = _get("ANTHROPIC_KEY")

# ----------------------------------------------------------------
# Data Keys
# ----------------------------------------------------------------
ETHERSCAN_KEY = _get("ETHERSCAN_KEY")

# ----------------------------------------------------------------
# Alerts (optional)
# ----------------------------------------------------------------
TELEGRAM_BOT_TOKEN = _get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = _get("TELEGRAM_CHAT_ID")

# ----------------------------------------------------------------
# Storage
# ----------------------------------------------------------------
DATA_PATH = _get("DATA_PATH", "./oracle_data")

# ----------------------------------------------------------------
# Known whale addresses — public blockchain data, no key needed
# These are the wallets worth watching
# ----------------------------------------------------------------
BTC_WHALE_ADDRESSES = {
    "US_Government":    "1JCe8z4jJVNXSjohjqeiXnYtMnrFoiYKSG",
    "Binance_Cold_1":   "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo",
    "Bitfinex_1":       "bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrpmv24sq90ecnvqqjwvw97",
    "MicroStrategy_1":  "1P5ZEDWTKTFGxQjZphgWPQUpe554WKDfHQ",
    "Coinbase_Cold":    "1LdRcdxfbSnmCYYNdeYpUnztiYzVfBEQeC",
    "Kraken_1":         "3FupZp77ySr7jvZDZhJHYqNTMEKrpb3nCd",
}

ETH_WHALE_ADDRESSES = {
    "Vitalik_Buterin":  "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    "Binance_Hot":      "0x28C6c06298d514Db089934071355E5743bf21d60",
    "Coinbase_2":       "0x71660c4005BA85c37ccec55d0C4493E66Fe775d3",
    "Tether_Treasury":  "0x5754284f345afc66a98fbB0a0Afe71e0F007B949",
    "Ethereum_Foundation": "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe",
    "Justin_Sun":       "0x3DdfA8eC3052539b6C9549F12cEA2C295cfF5296",
}
