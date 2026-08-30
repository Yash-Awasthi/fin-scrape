"""
Cryptocurrency data service from coingecko_py — market data and price tracking.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import math
import time


@dataclass
class CoinData:
    id: str
    symbol: str
    name: str
    price_usd: float = 0.0
    market_cap: float = 0.0
    volume_24h: float = 0.0
    price_change_24h: float = 0.0
    price_change_7d: float = 0.0
    price_change_30d: float = 0.0
    ath: float = 0.0
    ath_change_pct: float = 0.0
    circulating_supply: float = 0.0
    total_supply: float = 0.0
    max_supply: Optional[float] = None
    last_updated: float = 0.0


@dataclass
class MarketOverview:
    total_market_cap: float = 0.0
    total_volume_24h: float = 0.0
    btc_dominance: float = 0.0
    eth_dominance: float = 0.0
    active_cryptos: int = 0
    market_cap_change_24h: float = 0.0


@dataclass
class PriceHistory:
    timestamps: List[float]
    prices: List[float]
    volumes: List[float]


MOCK_COINS = {
    "bitcoin": CoinData(id="bitcoin", symbol="btc", name="Bitcoin", price_usd=67500, market_cap=1.32e12, volume_24h=28e9),
    "ethereum": CoinData(id="ethereum", symbol="eth", name="Ethereum", price_usd=3450, market_cap=414e9, volume_24h=14e9),
    "solana": CoinData(id="solana", symbol="sol", name="Solana", price_usd=175, market_cap=77e9, volume_24h=3e9),
    "cardano": CoinData(id="cardano", symbol="ada", name="Cardano", price_usd=0.45, market_cap=16e9, volume_24h=500e6),
    "ripple": CoinData(id="ripple", symbol="xrp", name="XRP", price_usd=0.52, market_cap=28e9, volume_24h=1.2e9),
}


def get_coin_data(coin_id: str) -> Optional[CoinData]:
    return MOCK_COINS.get(coin_id.lower())


def get_market_overview() -> MarketOverview:
    total_mcap = sum(c.market_cap for c in MOCK_COINS.values())
    total_vol = sum(c.volume_24h for c in MOCK_COINS.values())
    btc = MOCK_COINS["bitcoin"]
    eth = MOCK_COINS["ethereum"]
    return MarketOverview(
        total_market_cap=total_mcap,
        total_volume_24h=total_vol,
        btc_dominance=btc.market_cap / total_mcap * 100,
        eth_dominance=eth.market_cap / total_mcap * 100,
        active_cryptos=len(MOCK_COINS),
    )


def generate_price_history(coin_id: str, days: int = 30) -> PriceHistory:
    coin = MOCK_COINS.get(coin_id)
    if not coin:
        return PriceHistory([], [], [])

    now = time.time()
    timestamps = [now - (days - i) * 86400 for i in range(days)]
    base = coin.price_usd
    prices = []
    volumes = []
    for i in range(days):
        variation = 1 + 0.02 * math.sin(i * 0.5) + 0.01 * math.cos(i * 0.3)
        prices.append(base * variation)
        volumes.append(coin.volume_24h * (0.8 + 0.4 * math.sin(i * 0.7)))
    return PriceHistory(timestamps=timestamps, prices=prices, volumes=volumes)


def compute_portfolio_value(holdings: Dict[str, float]) -> float:
    total = 0.0
    for coin_id, amount in holdings.items():
        coin = MOCK_COINS.get(coin_id)
        if coin:
            total += coin.price_usd * amount
    return total


def sort_coins_by(metric: str = "market_cap", limit: int = 10) -> List[CoinData]:
    coins = list(MOCK_COINS.values())
    if metric == "market_cap":
        coins.sort(key=lambda c: c.market_cap, reverse=True)
    elif metric == "volume":
        coins.sort(key=lambda c: c.volume_24h, reverse=True)
    elif metric == "price_change_24h":
        coins.sort(key=lambda c: c.price_change_24h, reverse=True)
    return coins[:limit]
