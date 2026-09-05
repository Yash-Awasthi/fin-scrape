import pandas as pd

from gprobs.config import MARKET_CONTROL_TICKERS
from gprobs.features.returns import calculate_log_returns
from gprobs.utils import require_columns

CONTROL_TICKERS = MARKET_CONTROL_TICKERS

CONTROL_COLUMNS = [
    "global_market_return",
    "vix_change",
    "oil_change",
    "dollar_return",
    "us10y_change",
]


def build_market_controls(prices: pd.DataFrame) -> pd.DataFrame:
    required_tickers = list(MARKET_CONTROL_TICKERS)
    require_columns(prices, required_tickers, "Market control prices")

    controls = pd.DataFrame(index=prices.index)
    controls["global_market_return"] = calculate_log_returns(prices["ACWI"])
    controls["vix_change"] = prices["^VIX"].diff()
    controls["oil_change"] = prices["CL=F"].diff()
    controls["dollar_return"] = calculate_log_returns(prices["UUP"])
    controls["us10y_change"] = prices["^TNX"].diff()
    controls = controls.dropna().reset_index()
    controls = controls.rename(columns={controls.columns[0]: "date"})
    return controls[["date"] + CONTROL_COLUMNS]


def merge_market_controls(panel: pd.DataFrame, controls: pd.DataFrame) -> pd.DataFrame:
    require_columns(controls, CONTROL_COLUMNS, "Market controls")
    return panel.merge(controls[["date"] + CONTROL_COLUMNS], on="date", how="left")
