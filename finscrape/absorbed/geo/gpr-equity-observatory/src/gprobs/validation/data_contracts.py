import pandas as pd


def ensure_columns(df: pd.DataFrame, required: list[str]) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        names = ", ".join(missing)
        raise ValueError(f"missing required columns: {names}")


def standardize_month_start(values: pd.Series) -> pd.Series:
    dates = pd.to_datetime(values, errors="raise")
    return dates.dt.to_period("M").dt.to_timestamp()


def assert_no_duplicate_keys(df: pd.DataFrame, keys: list[str]) -> None:
    duplicates = df.duplicated(keys, keep=False)
    if duplicates.any():
        sample = df.loc[duplicates, keys].drop_duplicates().head(5).to_dict("records")
        raise ValueError(f"duplicate keys found for {keys}: {sample}")


def assert_dates_are_month_start(df: pd.DataFrame, column: str) -> None:
    dates = pd.to_datetime(df[column], errors="raise")
    bad_dates = dates[dates.dt.day != 1]
    if not bad_dates.empty:
        sample = bad_dates.head(5).dt.strftime("%Y-%m-%d").tolist()
        raise ValueError(f"{column} contains dates that are not month-start: {sample}")


def assert_no_future_leakage(train_dates: pd.Series, test_dates: pd.Series) -> None:
    train_max = pd.to_datetime(train_dates, errors="raise").max()
    test_min = pd.to_datetime(test_dates, errors="raise").min()
    if test_min <= train_max:
        raise ValueError("test dates must be after all training dates")


def missingness_report(df: pd.DataFrame) -> pd.DataFrame:
    missing = df.isna().sum()
    return pd.DataFrame(
        {
            "column": missing.index,
            "missing_count": missing.to_numpy(dtype=int),
            "missing_share": (missing / len(df)).round(4).to_numpy(dtype=float),
        }
    )
