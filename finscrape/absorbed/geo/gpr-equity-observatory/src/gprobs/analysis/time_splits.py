from dataclasses import dataclass

import pandas as pd

from gprobs.validation.data_contracts import assert_no_future_leakage


@dataclass(frozen=True)
class Split:
    train_dates: list[pd.Timestamp]
    test_dates: list[pd.Timestamp]


def make_time_splits(dates: pd.Series, min_train_months: int, test_window: int = 1) -> list[Split]:
    unique_dates = pd.Series(pd.to_datetime(dates).drop_duplicates()).reset_index(drop=True)
    if not unique_dates.is_monotonic_increasing:
        raise ValueError("dates must be increasing")
    if min_train_months < 1 or test_window < 1:
        raise ValueError("min_train_months and test_window must be positive")

    splits = []
    start = min_train_months
    while start < len(unique_dates):
        train_dates = unique_dates.iloc[:start].tolist()
        test_dates = unique_dates.iloc[start : start + test_window].tolist()
        assert_no_future_leakage(pd.Series(train_dates), pd.Series(test_dates))
        splits.append(Split(train_dates=train_dates, test_dates=test_dates))
        start += test_window
    return splits
