import numpy as np
import pandas as pd

from gprobs.config import ROLLING_BETA_MIN_PERIODS, ROLLING_BETA_WINDOW_DAYS

ROLLING_COLUMNS = [
    "date",
    "ticker",
    "country",
    "market_group",
    "rolling_gpr_beta",
]


def calculate_rolling_gpr_beta(
    panel: pd.DataFrame,
    window: int = ROLLING_BETA_WINDOW_DAYS,
    min_periods: int = ROLLING_BETA_MIN_PERIODS,
) -> pd.DataFrame:
    """Estimate rolling return sensitivity to raw daily GPR."""
    if window < 2:
        raise ValueError("window must be at least 2.")
    if min_periods < 2:
        raise ValueError("min_periods must be at least 2.")

    data = panel[["date", "ticker", "country", "market_group", "return", "gpr"]].dropna().copy()
    if data["gpr"].std(ddof=0) == 0:
        raise ValueError("GPR has no variation, so rolling beta cannot be calculated.")

    frames = []
    for _, country_data in data.groupby("ticker"):
        country_data = country_data.sort_values("date").reset_index(drop=True)
        rolling_covariance = country_data["return"].rolling(
            window=window,
            min_periods=min_periods,
        ).cov(country_data["gpr"])
        rolling_variance = country_data["gpr"].rolling(
            window=window,
            min_periods=min_periods,
        ).var()

        country_data["rolling_gpr_beta"] = rolling_covariance / rolling_variance
        country_data["rolling_gpr_beta"] = country_data["rolling_gpr_beta"].replace([np.inf, -np.inf], np.nan)
        frames.append(country_data[ROLLING_COLUMNS])

    if not frames:
        return pd.DataFrame(columns=ROLLING_COLUMNS)

    return pd.concat(frames, ignore_index=True)
