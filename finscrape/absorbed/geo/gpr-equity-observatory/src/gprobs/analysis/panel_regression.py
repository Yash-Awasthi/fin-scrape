import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from linearmodels.panel import PanelOLS

from gprobs.features.gpr_terms import PANEL_REGRESSION_GPR_CHANGE_Z

PANEL_GPR_CHANGE_Z_CONTEXT = PANEL_REGRESSION_GPR_CHANGE_Z
PANEL_GPR_CHANGE_Z_COLUMN = PANEL_GPR_CHANGE_Z_CONTEXT.column
BASELINE_FORMULA = f"etf_return ~ {PANEL_GPR_CHANGE_Z_COLUMN} + {PANEL_GPR_CHANGE_Z_COLUMN}:emerging_market + C(ticker)"
CONTROL_COLUMNS = [
    "global_market_return",
    "vix_change",
    "oil_change",
    "dollar_return",
    "us10y_change",
]
CONTROLLED_FORMULA = (
    f"etf_return ~ {PANEL_GPR_CHANGE_Z_COLUMN} + {PANEL_GPR_CHANGE_Z_COLUMN}:emerging_market + "
    "global_market_return + vix_change + oil_change + dollar_return + us10y_change + "
    "C(ticker)"
)
DATE_FE_TERM = f"{PANEL_GPR_CHANGE_Z_COLUMN}:emerging_market"


def _add_gpr_change_from_level(panel: pd.DataFrame) -> pd.DataFrame:
    if "gpr_change" in panel.columns:
        return panel.copy()
    if "gpr" not in panel.columns:
        raise ValueError("Panel data is missing gpr_change and gpr columns.")

    data = panel.copy()
    gpr_by_date = data[["date", "gpr"]].dropna().drop_duplicates()
    conflicting_dates = gpr_by_date.groupby("date")["gpr"].nunique()
    if conflicting_dates.gt(1).any():
        raise ValueError("GPR level must be unique within each date.")

    gpr_by_date = gpr_by_date.sort_values("date").reset_index(drop=True)
    gpr_by_date["gpr_change"] = gpr_by_date["gpr"].diff()
    return data.merge(gpr_by_date[["date", "gpr_change"]], on="date", how="left")


def _fit_with_clustered_covariance(
    model,
    data: pd.DataFrame,
    cluster_by_ticker: bool,
    cluster_by_date: bool | None,
):
    if cluster_by_date is None:
        cluster_by_date = cluster_by_ticker
    if not cluster_by_ticker and not cluster_by_date:
        return model.fit()

    groups = {}
    if cluster_by_ticker:
        groups["ticker"] = pd.factorize(data["ticker"])[0]
    if cluster_by_date:
        groups["date"] = pd.factorize(pd.to_datetime(data["date"]))[0]

    cluster_groups = next(iter(groups.values())) if len(groups) == 1 else pd.DataFrame(groups, index=data.index)
    return model.fit(cov_type="cluster", cov_kwds={"groups": cluster_groups})


def prepare_panel_regression_data(
    panel: pd.DataFrame,
    include_controls: bool = False,
    gpr_change_mean: float | None = None,
    gpr_change_std: float | None = None,
) -> pd.DataFrame:
    """Prepare the return panel for the baseline fixed-effects regression."""
    panel = _add_gpr_change_from_level(panel)
    columns = ["date", "ticker", "market_group", "return", "gpr_change"]
    if include_controls:
        columns = columns + CONTROL_COLUMNS

    data = panel[columns].dropna().copy()

    data["etf_return"] = data["return"]
    data["emerging_market"] = (data["market_group"] == "emerging").astype(int)

    if gpr_change_mean is None:
        gpr_change_mean = data["gpr_change"].mean()
    if gpr_change_std is None:
        gpr_change_std = data["gpr_change"].std(ddof=0)
    if not np.isfinite(1 / gpr_change_std):
        raise ValueError("GPR change has no (or near-zero) variation, so it cannot be standardized.")

    data[PANEL_GPR_CHANGE_Z_COLUMN] = (data["gpr_change"] - gpr_change_mean) / gpr_change_std
    return data


def run_baseline_panel_regression(
    panel: pd.DataFrame,
    cluster_by_ticker: bool = True,
    cluster_by_date: bool | None = None,
    gpr_change_mean: float | None = None,
    gpr_change_std: float | None = None,
):
    """Estimate return sensitivity to GPR with ticker fixed effects."""
    data = prepare_panel_regression_data(
        panel,
        gpr_change_mean=gpr_change_mean,
        gpr_change_std=gpr_change_std,
    )
    model = smf.ols(BASELINE_FORMULA, data=data)
    return _fit_with_clustered_covariance(
        model,
        data,
        cluster_by_ticker=cluster_by_ticker,
        cluster_by_date=cluster_by_date,
    )


def run_controlled_panel_regression(
    panel: pd.DataFrame,
    cluster_by_ticker: bool = True,
    cluster_by_date: bool | None = None,
    gpr_change_mean: float | None = None,
    gpr_change_std: float | None = None,
):
    """Estimate GPR sensitivity after adding public market controls."""
    data = prepare_panel_regression_data(
        panel,
        include_controls=True,
        gpr_change_mean=gpr_change_mean,
        gpr_change_std=gpr_change_std,
    )
    model = smf.ols(CONTROLLED_FORMULA, data=data)
    return _fit_with_clustered_covariance(
        model,
        data,
        cluster_by_ticker=cluster_by_ticker,
        cluster_by_date=cluster_by_date,
    )


def run_date_fe_panel_regression(
    panel: pd.DataFrame,
    cluster_by_ticker: bool = True,
    cluster_by_date: bool | None = None,
    gpr_change_mean: float | None = None,
    gpr_change_std: float | None = None,
):
    """Estimate the emerging-market differential after absorbing date shocks."""
    data = prepare_panel_regression_data(
        panel,
        gpr_change_mean=gpr_change_mean,
        gpr_change_std=gpr_change_std,
    )

    if cluster_by_date is None:
        cluster_by_date = cluster_by_ticker

    model_data = data.copy()
    model_data[DATE_FE_TERM] = model_data[PANEL_GPR_CHANGE_Z_COLUMN] * model_data["emerging_market"]
    model_data = model_data.set_index(["ticker", "date"])
    model = PanelOLS(
        model_data["etf_return"],
        model_data[[DATE_FE_TERM]],
        entity_effects=True,
        time_effects=True,
    )
    if cluster_by_ticker or cluster_by_date:
        return model.fit(
            cov_type="clustered",
            cluster_entity=cluster_by_ticker,
            cluster_time=cluster_by_date,
        )
    return model.fit()


def tidy_regression_results(result) -> pd.DataFrame:
    """Convert a regression result into a small readable coefficient table."""
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="invalid value encountered in sqrt",
            category=RuntimeWarning,
        )
        std_errors = _result_values(result, "bse", "std_errors")
        t_stats = _result_values(result, "tvalues", "tstats")
        p_values = result.pvalues.values

    return pd.DataFrame(
        {
            "term": result.params.index,
            "estimate": result.params.values,
            "std_error": std_errors,
            "t_stat": t_stats,
            "p_value": p_values,
        }
    )


def _result_values(result, statsmodels_name: str, linearmodels_name: str):
    values = getattr(result, statsmodels_name, None)
    if values is None:
        values = getattr(result, linearmodels_name)
    return values.values
