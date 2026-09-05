import pandas as pd

from gprobs.config import LARGE_RETURN_THRESHOLD


def flag_large_returns(
    panel: pd.DataFrame,
    threshold: float = LARGE_RETURN_THRESHOLD,
) -> pd.DataFrame:
    """Flag unusually large daily ETF returns for manual review."""
    flagged = panel.loc[panel["return"].abs() > threshold].copy()
    flagged["abs_return"] = flagged["return"].abs()

    columns = ["date", "ticker", "country", "return", "abs_return"]
    available_columns = [column for column in columns if column in flagged.columns]
    return flagged[available_columns].sort_values("abs_return", ascending=False).reset_index(drop=True)


def summarize_country_coverage(panel: pd.DataFrame) -> pd.DataFrame:
    """Summarize available return dates by country ETF."""
    return (
        panel.groupby(["country", "ticker", "market_group"], as_index=False)
        .agg(
            first_date=("date", "min"),
            last_date=("date", "max"),
            observation_count=("return", "count"),
        )
        .sort_values(["market_group", "country"])
        .reset_index(drop=True)
    )
