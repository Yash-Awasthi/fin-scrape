import numpy as np
import pandas as pd
from scipy import stats

from gprobs.config import (
    EVENT_ESTIMATION_GAP_DAYS,
    EVENT_ESTIMATION_WINDOW_DAYS,
    EVENT_MIN_ESTIMATION_OBS,
    EVENT_MIN_GAP_DAYS,
    EVENT_WINDOW_DAYS,
)
from gprobs.utils import require_columns

EVENT_WINDOW_COLUMNS = [
    "event_date",
    "event_trading_date",
    "relative_day",
    "date",
    "ticker",
    "country",
    "market_group",
    "region",
    "return",
]

EVENT_SUMMARY_COLUMNS = [
    "market_group",
    "relative_day",
    "average_return",
    "cumulative_average_return",
    "observation_count",
    "event_count",
]

ABNORMAL_EVENT_WINDOW_COLUMNS = EVENT_WINDOW_COLUMNS + [
    "global_market_return",
    "expected_return",
    "abnormal_return",
]

ABNORMAL_EVENT_SUMMARY_COLUMNS = [
    "market_group",
    "relative_day",
    "average_abnormal_return",
    "cumulative_average_abnormal_return",
    "observation_count",
    "event_count",
    "std_error",
    "t_stat",
    "p_value",
]


def select_spaced_events(
    gpr: pd.DataFrame,
    min_gap_days: int = EVENT_MIN_GAP_DAYS,
    shock_column: str = "gpr_shock",
) -> pd.Series:
    """Select shock dates while avoiding clusters of nearby shocks."""
    shock_dates = gpr.loc[gpr[shock_column], "date"].sort_values()

    selected_dates = []
    last_selected = None
    for date in shock_dates:
        date = pd.Timestamp(date)
        if last_selected is None or (date - last_selected).days >= min_gap_days:
            selected_dates.append(date)
            last_selected = date

    return pd.Series(selected_dates, name="event_date")


def select_peak_cluster_events(
    gpr: pd.DataFrame,
    shock_column: str = "gpr_shock",
    value_column: str = "gpr_change",
    min_gap_days: int = EVENT_MIN_GAP_DAYS,
) -> pd.Series:
    """Select the largest shock inside each cluster of nearby shock days."""
    require_columns(gpr, ["date", shock_column, value_column], "GPR data")
    shock_rows = (
        gpr.loc[gpr[shock_column], ["date", value_column]]
        .sort_values("date")
        .reset_index(drop=True)
    )
    if shock_rows.empty:
        return pd.Series([], name="event_date", dtype="datetime64[ns]")

    selected_dates = []
    cluster_start = 0
    previous_date = pd.Timestamp(shock_rows.loc[0, "date"])

    for row_number in range(1, len(shock_rows)):
        current_date = pd.Timestamp(shock_rows.loc[row_number, "date"])
        if (current_date - previous_date).days >= min_gap_days:
            selected_dates.append(_cluster_peak_date(shock_rows, cluster_start, row_number, value_column))
            cluster_start = row_number
        previous_date = current_date

    selected_dates.append(_cluster_peak_date(shock_rows, cluster_start, len(shock_rows), value_column))
    return pd.Series(sorted(selected_dates), name="event_date")


def _cluster_peak_date(
    shock_rows: pd.DataFrame,
    start: int,
    end: int,
    value_column: str,
) -> pd.Timestamp:
    cluster = shock_rows.iloc[start:end]
    peak_row = cluster[value_column].idxmax()
    return pd.Timestamp(shock_rows.loc[peak_row, "date"])


def build_event_windows(
    panel: pd.DataFrame,
    event_dates: pd.Series,
    window: int = EVENT_WINDOW_DAYS,
) -> pd.DataFrame:
    """Build ticker-level return windows around each GPR shock date."""
    frames = []

    for _, ticker_panel in panel.groupby("ticker"):
        ticker_panel = ticker_panel.sort_values("date").reset_index(drop=True)
        trading_dates = ticker_panel["date"]

        for event_date in event_dates:
            event_date = pd.Timestamp(event_date)
            event_position = trading_dates.searchsorted(event_date, side="left")
            if event_position >= len(ticker_panel):
                continue

            start_position = max(event_position - window, 0)
            end_position = min(event_position + window + 1, len(ticker_panel))

            event_window = ticker_panel.iloc[start_position:end_position].copy()
            event_window.insert(0, "event_date", event_date)
            event_window.insert(1, "event_trading_date", trading_dates.iloc[event_position])
            event_window.insert(
                2,
                "relative_day",
                list(range(start_position - event_position, end_position - event_position)),
            )
            frames.append(event_window)

    if not frames:
        return pd.DataFrame(columns=EVENT_WINDOW_COLUMNS)

    windows = pd.concat(frames, ignore_index=True)
    return windows[EVENT_WINDOW_COLUMNS]


def summarize_event_windows(windows: pd.DataFrame) -> pd.DataFrame:
    """Average event-window returns by market group and relative day."""
    if windows.empty:
        return pd.DataFrame(columns=EVENT_SUMMARY_COLUMNS)

    summary = (
        windows.groupby(["market_group", "relative_day"], as_index=False)
        .agg(
            average_return=("return", "mean"),
            observation_count=("return", "count"),
            event_count=("event_date", "nunique"),
        )
        .sort_values(["market_group", "relative_day"])
        .reset_index(drop=True)
    )
    summary["cumulative_average_return"] = summary.groupby("market_group")[
        "average_return"
    ].cumsum()
    return summary[EVENT_SUMMARY_COLUMNS]


def build_market_model_event_windows(
    panel: pd.DataFrame,
    event_dates: pd.Series,
    window: int = EVENT_WINDOW_DAYS,
    estimation_window: int = EVENT_ESTIMATION_WINDOW_DAYS,
    estimation_gap: int = EVENT_ESTIMATION_GAP_DAYS,
    min_estimation_obs: int = EVENT_MIN_ESTIMATION_OBS,
) -> pd.DataFrame:
    """Build event windows with market-model abnormal returns."""
    frames = []

    for _, ticker_panel in panel.groupby("ticker"):
        ticker_panel = ticker_panel.sort_values("date").reset_index(drop=True)
        trading_dates = ticker_panel["date"]

        for event_date in event_dates:
            event_date = pd.Timestamp(event_date)
            event_position = trading_dates.searchsorted(event_date, side="left")
            if event_position >= len(ticker_panel):
                continue

            estimation_end = event_position - estimation_gap
            estimation_start = estimation_end - estimation_window
            if estimation_start < 0:
                continue

            estimation_data = ticker_panel.iloc[estimation_start:estimation_end].dropna(
                subset=["return", "global_market_return"]
            )
            if len(estimation_data) < min_estimation_obs:
                continue

            market_variance = estimation_data["global_market_return"].var()
            if market_variance == 0:
                continue

            beta = estimation_data["return"].cov(estimation_data["global_market_return"]) / market_variance
            alpha = estimation_data["return"].mean() - beta * estimation_data["global_market_return"].mean()

            start_position = max(event_position - window, 0)
            end_position = min(event_position + window + 1, len(ticker_panel))
            event_window = ticker_panel.iloc[start_position:end_position].copy()
            event_window["expected_return"] = alpha + beta * event_window["global_market_return"]
            event_window["abnormal_return"] = event_window["return"] - event_window["expected_return"]
            event_window.insert(0, "event_date", event_date)
            event_window.insert(1, "event_trading_date", trading_dates.iloc[event_position])
            event_window.insert(
                2,
                "relative_day",
                list(range(start_position - event_position, end_position - event_position)),
            )
            frames.append(event_window)

    if not frames:
        return pd.DataFrame(columns=ABNORMAL_EVENT_WINDOW_COLUMNS)

    windows = pd.concat(frames, ignore_index=True)
    return windows[ABNORMAL_EVENT_WINDOW_COLUMNS]


def summarize_abnormal_event_windows(windows: pd.DataFrame) -> pd.DataFrame:
    """Average abnormal event-window returns by market group and relative day."""
    if windows.empty:
        return pd.DataFrame(columns=ABNORMAL_EVENT_SUMMARY_COLUMNS)

    summary = (
        windows.groupby(["market_group", "relative_day"], as_index=False)
        .agg(
            average_abnormal_return=("abnormal_return", "mean"),
            observation_count=("abnormal_return", "count"),
            event_count=("event_date", "nunique"),
        )
        .sort_values(["market_group", "relative_day"])
        .reset_index(drop=True)
    )
    inference = _abnormal_car_inference(windows)
    summary = summary.drop(columns=["cumulative_average_abnormal_return"], errors="ignore")
    summary = summary.merge(inference, on=["market_group", "relative_day"], how="left")
    return summary[ABNORMAL_EVENT_SUMMARY_COLUMNS]


def _abnormal_car_inference(windows: pd.DataFrame) -> pd.DataFrame:
    car_group_columns = ["market_group", "event_date"]
    if "ticker" in windows.columns:
        car_group_columns.append("ticker")

    event_cars = windows.sort_values(car_group_columns + ["relative_day"]).copy()
    event_cars["_car"] = event_cars.groupby(car_group_columns)["abnormal_return"].cumsum()
    inference = (
        event_cars.groupby(["market_group", "relative_day"], as_index=False)
        .agg(
            cumulative_average_abnormal_return=("_car", "mean"),
            car_count=("_car", "count"),
            car_std=("_car", "std"),
        )
        .sort_values(["market_group", "relative_day"])
        .reset_index(drop=True)
    )
    inference["std_error"] = inference["car_std"] / np.sqrt(inference["car_count"])
    inference["t_stat"] = inference["cumulative_average_abnormal_return"] / inference["std_error"]
    inference["p_value"] = inference.apply(_two_sided_t_p_value, axis=1)
    return inference[
        [
            "market_group",
            "relative_day",
            "cumulative_average_abnormal_return",
            "std_error",
            "t_stat",
            "p_value",
        ]
    ]


def _two_sided_t_p_value(row: pd.Series) -> float:
    if row["car_count"] <= 1 or pd.isna(row["t_stat"]) or np.isinf(row["t_stat"]):
        return float("nan")
    return float(2 * stats.t.sf(abs(row["t_stat"]), df=row["car_count"] - 1))
