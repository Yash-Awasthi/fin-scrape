import numpy as np
import pandas as pd


def calculate_log_returns(prices: pd.Series) -> pd.Series:
    """Calculate log returns from a price series without forward-filling prices."""
    if (prices.dropna() <= 0).any():
        raise ValueError("Prices must be positive before log returns can be calculated.")

    returns = np.log(prices / prices.shift(1)).dropna()
    returns.name = "return"
    return returns


def build_returns_panel(price_panel: pd.DataFrame) -> pd.DataFrame:
    """Convert wide adjusted prices into a long date-ticker-return panel."""
    frames = []

    for ticker in price_panel.columns:
        ticker_returns = calculate_log_returns(price_panel[ticker])
        frame = ticker_returns.reset_index()
        frame.columns = ["date", "return"]
        frame.insert(1, "ticker", ticker)
        frames.append(frame)

    if not frames:
        return pd.DataFrame(columns=["date", "ticker", "return"])

    return pd.concat(frames, ignore_index=True)
