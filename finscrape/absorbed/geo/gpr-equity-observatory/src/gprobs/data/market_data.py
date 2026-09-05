from pathlib import Path

import pandas as pd

from gprobs.config import (
    DATA_START_DATE,
    DEFAULT_DOWNLOAD_RETRIES,
    DEFAULT_DOWNLOAD_TIMEOUT_SECONDS,
    DEFAULT_RETRY_BACKOFF_SECONDS,
)
from gprobs.data.download_cache import retry
from gprobs.utils import require_columns

COUNTRY_COLUMNS = ["country", "ticker", "market_group", "region"]


def load_country_universe(path: str | Path = "data/country_universe.csv") -> pd.DataFrame:
    universe = pd.read_csv(path)
    require_columns(universe, COUNTRY_COLUMNS, "Country universe")
    return universe[COUNTRY_COLUMNS].copy()


def download_adjusted_prices(
    tickers: list[str],
    start: str = DATA_START_DATE,
    end: str | None = None,
    cache_path: str | Path | None = None,
    refresh: bool = False,
    timeout: int = DEFAULT_DOWNLOAD_TIMEOUT_SECONDS,
    retries: int = DEFAULT_DOWNLOAD_RETRIES,
    retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
) -> pd.DataFrame:
    """Download adjusted close prices from yfinance."""
    cache_path = Path(cache_path) if cache_path is not None else None
    metadata = _price_request_metadata(tickers, start, end)
    if cache_path is not None and cache_path.exists() and not refresh:
        data = _read_price_cache(cache_path, metadata)
    else:
        data = None

    if data is None:
        data = _download_yfinance_prices(
            tickers=tickers,
            start=start,
            end=end,
            timeout=timeout,
            retries=retries,
            retry_backoff_seconds=retry_backoff_seconds,
        )
        if cache_path is not None:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            pd.to_pickle({"metadata": metadata, "data": data}, cache_path)

    prices = extract_adjusted_close(data)
    prices.index.name = "date"
    return prices.sort_index()


def _price_request_metadata(
    tickers: list[str],
    start: str,
    end: str | None,
) -> dict:
    return {
        "tickers": sorted(tickers),
        "start": start,
        "end": end,
    }


def _read_price_cache(cache_path: Path, expected_metadata: dict):
    cached = pd.read_pickle(cache_path)
    if not isinstance(cached, dict):
        return None
    if cached.get("metadata") != expected_metadata:
        return None
    return cached.get("data")


def _download_yfinance_prices(
    tickers: list[str],
    start: str,
    end: str | None,
    timeout: int,
    retries: int,
    retry_backoff_seconds: float,
) -> pd.DataFrame:
    try:
        import yfinance as yf
    except ImportError as error:
        raise ImportError(
            "yfinance is required to download market data. "
            "Install dependencies with: python -m pip install -e ."
        ) from error

    return retry(
        lambda: yf.download(
            tickers=tickers,
            start=start,
            end=end,
            auto_adjust=False,
            progress=False,
            timeout=timeout,
        ),
        retries=retries,
        backoff_seconds=retry_backoff_seconds,
    )


def extract_adjusted_close(data: pd.DataFrame) -> pd.DataFrame:
    """Return one adjusted-close price column per ticker from yfinance output."""
    if data.empty:
        return pd.DataFrame()

    if isinstance(data.columns, pd.MultiIndex):
        first_level = data.columns.get_level_values(0)
        second_level = data.columns.get_level_values(1)

        if "Adj Close" in first_level:
            prices = data["Adj Close"]
        elif "Close" in first_level:
            prices = data["Close"]
        elif "Adj Close" in second_level:
            prices = data.xs("Adj Close", level=1, axis=1)
        elif "Close" in second_level:
            prices = data.xs("Close", level=1, axis=1)
        else:
            raise ValueError("Could not find adjusted close or close prices in yfinance data.")
    elif "Adj Close" in data.columns:
        prices = data[["Adj Close"]].rename(columns={"Adj Close": "price"})
    elif "Close" in data.columns:
        prices = data[["Close"]].rename(columns={"Close": "price"})
    else:
        raise ValueError("Could not find adjusted close or close prices in yfinance data.")

    if isinstance(prices, pd.Series):
        prices = prices.to_frame()

    return prices.dropna(how="all")
