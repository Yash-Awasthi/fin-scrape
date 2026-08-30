"""Quantitative Strategy Engine.

Extracted from QuantDinger (inspiration).
Strategy definition, signal generation, position sizing, and risk management
for systematic trading.

All pure functions — no DB, no async.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MarketData:
    """OHLCV market data point."""
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Signal:
    """Trading signal."""
    ticker: str
    direction: str  # "long", "short", "flat"
    strength: float  # -1 to +1
    timestamp: str
    reason: str = ""


@dataclass
class Position:
    """Current position."""
    ticker: str
    direction: str
    size: float  # number of shares/contracts
    entry_price: float
    entry_date: str
    current_price: float = 0.0
    unrealized_pnl: float = 0.0


@dataclass
class RiskLimits:
    """Risk management limits."""
    max_position_pct: float = 0.10  # max 10% per position
    max_drawdown_pct: float = 0.15  # max 15% drawdown
    max_leverage: float = 1.0  # no leverage by default
    stop_loss_pct: float = 0.05  # 5% stop loss
    take_profit_pct: float = 0.10  # 10% take profit
    max_daily_trades: int = 10
    max_correlation: float = 0.7  # max correlation between positions


# --- Signal Generation ---

def sma(values: list[float], period: int) -> list[float]:
    """Simple Moving Average.

    Args:
        values: Price series
        period: Lookback period

    Returns:
        SMA values (first period-1 entries are None)
    """
    if len(values) < period:
        return [None] * len(values)  # type: ignore

    result = [None] * (period - 1)  # type: ignore
    for i in range(period - 1, len(values)):
        avg = sum(values[i - period + 1:i + 1]) / period
        result.append(avg)
    return result


def ema(values: list[float], period: int) -> list[float]:
    """Exponential Moving Average.

    Args:
        values: Price series
        period: Lookback period

    Returns:
        EMA values
    """
    if not values:
        return []

    multiplier = 2.0 / (period + 1)
    result = [values[0]]

    for i in range(1, len(values)):
        ema_val = (values[i] - result[-1]) * multiplier + result[-1]
        result.append(ema_val)

    return result


def rsi(closes: list[float], period: int = 14) -> list[Optional[float]]:
    """Relative Strength Index.

    Args:
        closes: Close prices
        period: RSI period (default 14)

    Returns:
        RSI values (0-100)
    """
    if len(closes) < period + 1:
        return [None] * len(closes)

    # Calculate gains and losses
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(0, d) for d in deltas]
    losses = [max(0, -d) for d in deltas]

    # Initial averages
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    result = [None] * period

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            rsi_val = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi_val = 100 - (100 / (1 + rs))

        result.append(round(rsi_val, 2))

    return result


def macd(
    closes: list[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> dict:
    """MACD (Moving Average Convergence Divergence).

    Args:
        closes: Close prices
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period

    Returns:
        Dict with macd_line, signal_line, histogram
    """
    if len(closes) < slow:
        return {"macd_line": [], "signal_line": [], "histogram": []}

    fast_ema = ema(closes, fast)
    slow_ema = ema(closes, slow)

    macd_line = [f - s for f, s in zip(fast_ema, slow_ema)]
    signal_line = ema(macd_line, signal)
    histogram = [m - s for m, s in zip(macd_line, signal_line)]

    return {
        "macd_line": macd_line,
        "signal_line": signal_line,
        "histogram": histogram,
    }


def bollinger_bands(
    closes: list[float],
    period: int = 20,
    std_dev: float = 2.0,
) -> dict:
    """Bollinger Bands.

    Args:
        closes: Close prices
        period: Moving average period
        std_dev: Standard deviation multiplier

    Returns:
        Dict with upper, middle, lower bands
    """
    if len(closes) < period:
        return {"upper": [], "middle": [], "lower": []}

    middle = sma(closes, period)
    upper = []
    lower = []

    for i in range(len(closes)):
        if middle[i] is None:
            upper.append(None)
            lower.append(None)
        else:
            window = closes[i - period + 1:i + 1]
            std = math.sqrt(sum((x - middle[i]) ** 2 for x in window) / period)
            upper.append(middle[i] + std_dev * std)
            lower.append(middle[i] - std_dev * std)

    return {"upper": upper, "middle": middle, "lower": lower}


# --- Strategy Signals ---

def ma_crossover_signal(
    closes: list[float],
    fast_period: int = 10,
    slow_period: float = 30,
) -> Signal:
    """Moving average crossover signal.

    Args:
        closes: Close prices
        fast_period: Fast MA period
        slow_period: Slow MA period

    Returns:
        Signal based on crossover
    """
    fast_ma = sma(closes, fast_period)
    slow_ma = sma(closes, int(slow_period))

    if not fast_ma or not slow_ma:
        return Signal(ticker="", direction="flat", strength=0.0, timestamp="")

    last_fast = fast_ma[-1]
    last_slow = slow_ma[-1]
    prev_fast = fast_ma[-2] if len(fast_ma) > 1 else last_fast
    prev_slow = slow_ma[-2] if len(slow_ma) > 1 else last_slow

    if last_fast is None or last_slow is None or prev_fast is None or prev_slow is None:
        return Signal(ticker="", direction="flat", strength=0.0, timestamp="")

    # Bullish crossover
    if prev_fast <= prev_slow and last_fast > last_slow:
        strength = min(1.0, (last_fast - last_slow) / last_slow * 10)
        return Signal(ticker="", direction="long", strength=round(strength, 3), timestamp="")

    # Bearish crossover
    if prev_fast >= prev_slow and last_fast < last_slow:
        strength = min(1.0, (last_slow - last_fast) / last_slow * 10)
        return Signal(ticker="", direction="short", strength=round(-strength, 3), timestamp="")

    return Signal(ticker="", direction="flat", strength=0.0, timestamp="")


def rsi_signal(closes: list[float], period: int = 14) -> Signal:
    """RSI-based signal.

    Args:
        closes: Close prices
        period: RSI period

    Returns:
        Signal based on RSI
    """
    rsi_values = rsi(closes, period)
    current_rsi = rsi_values[-1] if rsi_values and rsi_values[-1] is not None else 50

    if current_rsi < 30:
        return Signal(ticker="", direction="long", strength=round((30 - current_rsi) / 30, 3), timestamp="")
    elif current_rsi > 70:
        return Signal(ticker="", direction="short", strength=round(-(current_rsi - 70) / 30, 3), timestamp="")

    return Signal(ticker="", direction="flat", strength=0.0, timestamp="")


# --- Risk Management ---

def calculate_position_size(
    capital: float,
    entry_price: float,
    risk_limits: RiskLimits,
    current_drawdown: float = 0.0,
) -> float:
    """Calculate position size based on risk limits.

    Args:
        capital: Available capital
        entry_price: Entry price per share
        risk_limits: Risk constraints
        current_drawdown: Current portfolio drawdown

    Returns:
        Number of shares to buy
    """
    if entry_price <= 0 or capital <= 0:
        return 0.0

    # Check drawdown limit
    if current_drawdown >= risk_limits.max_drawdown_pct:
        return 0.0

    # Max position value
    max_position_value = capital * risk_limits.max_position_pct

    # Stop loss based sizing
    stop_loss_value = entry_price * risk_limits.stop_loss_pct
    risk_per_share = stop_loss_value

    if risk_per_share <= 0:
        return 0.0

    # Risk-based sizing (risk 1% of capital per trade)
    risk_budget = capital * 0.01
    risk_based_shares = risk_budget / risk_per_share

    # Cap by max position
    max_shares = max_position_value / entry_price

    return min(risk_based_shares, max_shares)


def check_stop_loss(
    position: Position,
    current_price: float,
    risk_limits: RiskLimits,
) -> bool:
    """Check if position should be stopped out.

    Args:
        position: Current position
        current_price: Current market price
        risk_limits: Risk constraints

    Returns:
        True if stop loss triggered
    """
    if position.direction == "long":
        loss_pct = (position.entry_price - current_price) / position.entry_price
    else:
        loss_pct = (current_price - position.entry_price) / position.entry_price

    return loss_pct >= risk_limits.stop_loss_pct


def check_take_profit(
    position: Position,
    current_price: float,
    risk_limits: RiskLimits,
) -> bool:
    """Check if position should take profit.

    Args:
        position: Current position
        current_price: Current market price
        risk_limits: Risk constraints

    Returns:
        True if take profit triggered
    """
    if position.direction == "long":
        gain_pct = (current_price - position.entry_price) / position.entry_price
    else:
        gain_pct = (position.entry_price - current_price) / position.entry_price

    return gain_pct >= risk_limits.take_profit_pct


def calculate_portfolio_metrics(positions: list[Position]) -> dict:
    """Calculate portfolio-level risk metrics.

    Args:
        positions: List of current positions

    Returns:
        Portfolio metrics
    """
    if not positions:
        return {
            "total_exposure": 0.0,
            "long_exposure": 0.0,
            "short_exposure": 0.0,
            "net_exposure": 0.0,
            "position_count": 0,
            "total_unrealized_pnl": 0.0,
        }

    long_positions = [p for p in positions if p.direction == "long"]
    short_positions = [p for p in positions if p.direction == "short"]

    long_exposure = sum(p.size * p.current_price for p in long_positions)
    short_exposure = sum(p.size * p.current_price for p in short_positions)

    return {
        "total_exposure": round(long_exposure + short_exposure, 2),
        "long_exposure": round(long_exposure, 2),
        "short_exposure": round(short_exposure, 2),
        "net_exposure": round(long_exposure - short_exposure, 2),
        "position_count": len(positions),
        "total_unrealized_pnl": round(sum(p.unrealized_pnl for p in positions), 2),
    }
