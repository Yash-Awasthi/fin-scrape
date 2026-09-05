import pandas as pd

from gprobs.analysis.event_study import (
    build_market_model_event_windows,
    select_peak_cluster_events,
    summarize_abnormal_event_windows,
)
from gprobs.config import (
    EVENT_ESTIMATION_GAP_DAYS,
    EVENT_ESTIMATION_WINDOW_DAYS,
    EVENT_MIN_ESTIMATION_OBS,
    EVENT_MIN_GAP_DAYS,
    GPR_EXPANDING_SHOCK_MIN_PERIODS,
)
from gprobs.data.gpr_data import mark_top_quantile_shocks

ROBUSTNESS_COLUMNS = [
    "shock_quantile",
    "window",
    "market_group",
    "cumulative_average_abnormal_return",
    "event_count",
    "std_error",
    "t_stat",
    "p_value",
]


def summarize_window_endpoint(
    summary: pd.DataFrame,
    shock_quantile: float,
    window: int,
) -> pd.DataFrame:
    """Keep the final cumulative abnormal return for each market group."""
    if summary.empty:
        return pd.DataFrame(columns=ROBUSTNESS_COLUMNS)

    endpoint = summary.loc[
        summary["relative_day"] == window,
        [
            "market_group",
            "cumulative_average_abnormal_return",
            "event_count",
            "std_error",
            "t_stat",
            "p_value",
        ],
    ].copy()
    endpoint["shock_quantile"] = float(shock_quantile)
    endpoint["window"] = int(window)

    return (
        endpoint[ROBUSTNESS_COLUMNS]
        .sort_values("market_group")
        .reset_index(drop=True)
    )


def build_event_robustness_table(
    panel: pd.DataFrame,
    gpr: pd.DataFrame,
    shock_quantiles: list[float],
    windows: list[int],
    min_gap_days: int = EVENT_MIN_GAP_DAYS,
    estimation_window: int = EVENT_ESTIMATION_WINDOW_DAYS,
    estimation_gap: int = EVENT_ESTIMATION_GAP_DAYS,
    min_estimation_obs: int = EVENT_MIN_ESTIMATION_OBS,
    expanding_min_periods: int = GPR_EXPANDING_SHOCK_MIN_PERIODS,
) -> pd.DataFrame:
    """Compare event-study endpoints across shock thresholds and windows."""
    panel = panel.copy()
    gpr = gpr.copy()
    panel["date"] = pd.to_datetime(panel["date"])
    gpr["date"] = pd.to_datetime(gpr["date"])

    results = []
    for shock_quantile in shock_quantiles:
        shocked_gpr = mark_top_quantile_shocks(
            gpr,
            quantile=shock_quantile,
            expanding_min_periods=expanding_min_periods,
        )
        event_dates = select_peak_cluster_events(
            shocked_gpr,
            shock_column="gpr_change_shock",
            value_column="gpr_change",
            min_gap_days=min_gap_days,
        )

        for window in windows:
            event_windows = build_market_model_event_windows(
                panel,
                event_dates,
                window=window,
                estimation_window=estimation_window,
                estimation_gap=estimation_gap,
                min_estimation_obs=min_estimation_obs,
            )
            summary = summarize_abnormal_event_windows(event_windows)
            endpoint = summarize_window_endpoint(
                summary,
                shock_quantile=shock_quantile,
                window=window,
            )
            if not endpoint.empty:
                results.append(endpoint)

    if not results:
        return pd.DataFrame(columns=ROBUSTNESS_COLUMNS)

    return (
        pd.concat(results, ignore_index=True)
        .sort_values(["shock_quantile", "window", "market_group"])
        .reset_index(drop=True)
    )
