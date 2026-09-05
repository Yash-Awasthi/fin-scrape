import pandas as pd

from gprobs.validation.data_contracts import ensure_columns


def make_forward_returns(
    df: pd.DataFrame,
    horizons: list[int],
    return_col: str = "excess_return",
    group_col: str = "market_id",
) -> pd.DataFrame:
    ensure_columns(df, ["date_month", group_col, return_col])
    result = df.sort_values([group_col, "date_month"]).copy()
    _assert_contiguous_months(result, group_col)

    for horizon in horizons:
        column = f"ret_fwd_{horizon}m"
        result[column] = result.groupby(group_col, group_keys=False)[return_col].transform(
            lambda series, h=horizon: _future_cumulative_return(series, h)
        )

    return result.sort_values(["date_month", group_col]).reset_index(drop=True)


def _future_cumulative_return(series: pd.Series, horizon: int) -> pd.Series:
    future = series.shift(-1)
    return future.rolling(horizon, min_periods=horizon).sum().shift(-(horizon - 1))


def _assert_contiguous_months(df: pd.DataFrame, group_col: str) -> None:
    for group_value, group in df.groupby(group_col, sort=False):
        dates = pd.to_datetime(group["date_month"], errors="raise").reset_index(drop=True)
        if dates.empty:
            continue
        expected = pd.Series(pd.date_range(dates.iloc[0], dates.iloc[-1], freq="MS"))
        if len(dates) != len(expected) or not dates.equals(expected):
            raise ValueError(f"{group_col}={group_value} must have a contiguous monthly sequence")
