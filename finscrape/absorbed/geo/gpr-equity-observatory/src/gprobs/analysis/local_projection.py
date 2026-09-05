import math

import pandas as pd
import statsmodels.formula.api as smf

from gprobs.analysis.panel_regression import CONTROL_COLUMNS
from gprobs.config import (
    EVENT_ESTIMATION_GAP_DAYS,
    EVENT_ESTIMATION_WINDOW_DAYS,
    EVENT_MIN_ESTIMATION_OBS,
    LOCAL_PROJECTION_MAX_HORIZON,
)
from gprobs.utils import coerce_shock_to_int, require_columns

LOCAL_PROJECTION_COLUMNS = [
    "horizon",
    "date",
    "ticker",
    "country",
    "market_group",
    "cumulative_abnormal_return",
    "gpr_shock",
    "emerging_market",
]

RESULT_COLUMNS = [
    "horizon",
    "market_group",
    "estimate",
    "std_error",
    "ci_low",
    "ci_high",
    "p_value",
]


def build_local_projection_data(
    panel: pd.DataFrame,
    max_horizon: int = LOCAL_PROJECTION_MAX_HORIZON,
    include_controls: bool = False,
    estimation_window: int = EVENT_ESTIMATION_WINDOW_DAYS,
    estimation_gap: int = EVENT_ESTIMATION_GAP_DAYS,
    min_estimation_obs: int = EVENT_MIN_ESTIMATION_OBS,
) -> pd.DataFrame:
    """Build cumulative future abnormal returns for local projection regressions."""
    if max_horizon < 0:
        raise ValueError("max_horizon must be non-negative.")
    if estimation_window < 2:
        raise ValueError("estimation_window must be at least 2.")
    if estimation_gap < 0:
        raise ValueError("estimation_gap must be non-negative.")
    if min_estimation_obs < 2:
        raise ValueError("min_estimation_obs must be at least 2.")

    base_columns = [
        "date",
        "ticker",
        "country",
        "market_group",
        "return",
        "global_market_return",
        "gpr_shock",
    ]
    if include_controls:
        base_columns = base_columns + [column for column in CONTROL_COLUMNS if column not in base_columns]

    require_columns(panel, base_columns, "Local projection panel")

    data = panel[base_columns].dropna(subset=["date", "ticker", "return", "global_market_return", "gpr_shock"]).copy()
    data["gpr_shock"] = data["gpr_shock"].map(coerce_shock_to_int)
    data["emerging_market"] = (data["market_group"] == "emerging").astype(int)

    frames = []
    for _, ticker_data in data.groupby("ticker"):
        ticker_data = ticker_data.sort_values("date").reset_index(drop=True)
        frames.extend(
            _ticker_projection_rows(
                ticker_data,
                max_horizon=max_horizon,
                estimation_window=estimation_window,
                estimation_gap=estimation_gap,
                min_estimation_obs=min_estimation_obs,
            )
        )

    if not frames:
        return pd.DataFrame(columns=_projection_columns(include_controls))

    projection_data = pd.DataFrame(frames)
    return projection_data[_projection_columns(include_controls)].reset_index(drop=True)


def estimate_local_projections(
    panel: pd.DataFrame,
    max_horizon: int = LOCAL_PROJECTION_MAX_HORIZON,
    include_controls: bool = False,
    estimation_window: int = EVENT_ESTIMATION_WINDOW_DAYS,
    estimation_gap: int = EVENT_ESTIMATION_GAP_DAYS,
    min_estimation_obs: int = EVENT_MIN_ESTIMATION_OBS,
    cluster_by_ticker: bool = True,
    cluster_by_date: bool | None = None,
) -> pd.DataFrame:
    """Estimate GPR shock response paths using market-model abnormal returns."""
    data = build_local_projection_data(
        panel,
        max_horizon=max_horizon,
        include_controls=include_controls,
        estimation_window=estimation_window,
        estimation_gap=estimation_gap,
        min_estimation_obs=min_estimation_obs,
    )

    rows = []
    for horizon, horizon_data in data.groupby("horizon"):
        result = _fit_horizon_model(
            horizon_data,
            include_controls=include_controls,
            cluster_by_ticker=cluster_by_ticker,
            cluster_by_date=cluster_by_date,
        )
        rows.extend(_response_rows(result, int(horizon)))

    return pd.DataFrame(rows, columns=RESULT_COLUMNS)


def _projection_columns(include_controls: bool) -> list[str]:
    columns = LOCAL_PROJECTION_COLUMNS.copy()
    if include_controls:
        columns.extend(CONTROL_COLUMNS)
    return columns


def _ticker_projection_rows(
    ticker_data: pd.DataFrame,
    max_horizon: int,
    estimation_window: int,
    estimation_gap: int,
    min_estimation_obs: int,
) -> list[dict]:
    ticker_data = _add_market_model_parameters(
        ticker_data,
        estimation_window=estimation_window,
        estimation_gap=estimation_gap,
        min_estimation_obs=min_estimation_obs,
    )

    rows = []
    for horizon in range(max_horizon + 1):
        horizon_data = ticker_data.copy()
        return_sum = _forward_sum(horizon_data["return"], horizon)
        market_sum = _forward_sum(horizon_data["global_market_return"], horizon)
        horizon_data["horizon"] = horizon
        horizon_data["cumulative_abnormal_return"] = (
            return_sum
            - horizon_data["_market_alpha"] * (horizon + 1)
            - horizon_data["_market_beta"] * market_sum
        )
        horizon_data = horizon_data.dropna(
            subset=["_market_alpha", "_market_beta", "cumulative_abnormal_return"]
        )
        horizon_data = horizon_data.drop(
            columns=[
                "_market_mean",
                "_return_mean",
                "_market_variance",
                "_market_covariance",
                "_market_alpha",
                "_market_beta",
            ]
        )
        rows.extend(horizon_data.to_dict("records"))

    return rows


def _add_market_model_parameters(
    ticker_data: pd.DataFrame,
    estimation_window: int,
    estimation_gap: int,
    min_estimation_obs: int,
) -> pd.DataFrame:
    model_data = ticker_data.copy()
    shift_periods = estimation_gap + 1
    rolling_market = model_data["global_market_return"].rolling(
        estimation_window,
        min_periods=min_estimation_obs,
    )
    rolling_return = model_data["return"].rolling(
        estimation_window,
        min_periods=min_estimation_obs,
    )
    model_data["_market_mean"] = rolling_market.mean().shift(shift_periods)
    model_data["_return_mean"] = rolling_return.mean().shift(shift_periods)
    model_data["_market_variance"] = rolling_market.var().shift(shift_periods)
    model_data["_market_covariance"] = rolling_return.cov(
        model_data["global_market_return"]
    ).shift(shift_periods)
    model_data["_market_beta"] = (
        model_data["_market_covariance"] / model_data["_market_variance"]
    )
    model_data.loc[model_data["_market_variance"] == 0, "_market_beta"] = pd.NA
    model_data["_market_alpha"] = (
        model_data["_return_mean"]
        - model_data["_market_beta"] * model_data["_market_mean"]
    )
    return model_data


def _forward_sum(values: pd.Series, horizon: int) -> pd.Series:
    forward_values = [values.shift(-offset) for offset in range(horizon + 1)]
    return pd.concat(forward_values, axis=1).sum(axis=1, min_count=horizon + 1)


def _fit_horizon_model(
    data: pd.DataFrame,
    include_controls: bool,
    cluster_by_ticker: bool,
    cluster_by_date: bool | None = None,
):
    control_terms = " + " + " + ".join(CONTROL_COLUMNS) if include_controls else ""
    formula = f"cumulative_abnormal_return ~ gpr_shock + gpr_shock:emerging_market{control_terms} + C(ticker)"

    if cluster_by_date is None:
        cluster_by_date = cluster_by_ticker

    model_columns = ["cumulative_abnormal_return", "gpr_shock", "emerging_market", "ticker"]
    if cluster_by_date:
        model_columns.append("date")
    if include_controls:
        model_columns.extend(CONTROL_COLUMNS)
    data = data.dropna(subset=model_columns)

    model = smf.ols(formula, data=data)
    if cluster_by_ticker or cluster_by_date:
        groups = {}
        if cluster_by_ticker:
            groups["ticker"] = pd.factorize(data["ticker"])[0]
        if cluster_by_date:
            groups["date"] = pd.factorize(pd.to_datetime(data["date"]))[0]
        cluster_groups = (
            next(iter(groups.values()))
            if len(groups) == 1
            else pd.DataFrame(groups, index=data.index)
        )
        return model.fit(cov_type="cluster", cov_kwds={"groups": cluster_groups})
    return model.fit()


def _response_rows(result, horizon: int) -> list[dict]:
    developed_estimate = result.params.get("gpr_shock", 0.0)
    developed_var = _covariance_value(result, "gpr_shock", "gpr_shock")
    developed_se = math.sqrt(max(developed_var, 0.0))

    interaction_term = "gpr_shock:emerging_market"
    interaction_estimate = result.params.get(interaction_term, 0.0)
    emerging_estimate = developed_estimate + interaction_estimate
    emerging_var = (
        developed_var
        + _covariance_value(result, interaction_term, interaction_term)
        + 2 * _covariance_value(result, "gpr_shock", interaction_term)
    )
    emerging_se = math.sqrt(max(emerging_var, 0.0))

    return [
        _format_response_row(
            horizon,
            "developed",
            developed_estimate,
            developed_se,
            result.pvalues.get("gpr_shock", float("nan")),
        ),
        _format_response_row(
            horizon,
            "emerging",
            emerging_estimate,
            emerging_se,
            _two_sided_normal_p_value(emerging_estimate, emerging_se),
        ),
    ]


def _covariance_value(result, first_term: str, second_term: str) -> float:
    covariance = result.cov_params()
    if first_term not in covariance.index or second_term not in covariance.columns:
        return 0.0
    return float(covariance.loc[first_term, second_term])


def _two_sided_normal_p_value(estimate: float, std_error: float) -> float:
    if not math.isfinite(estimate) or not math.isfinite(std_error) or std_error <= 0:
        return float("nan")
    z_stat = abs(estimate / std_error)
    return math.erfc(z_stat / math.sqrt(2.0))


def _format_response_row(
    horizon: int,
    market_group: str,
    estimate: float,
    std_error: float,
    p_value: float,
) -> dict:
    return {
        "horizon": horizon,
        "market_group": market_group,
        "estimate": estimate,
        "std_error": std_error,
        "ci_low": estimate - 1.96 * std_error,
        "ci_high": estimate + 1.96 * std_error,
        "p_value": p_value,
    }
