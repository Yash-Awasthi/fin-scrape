import numpy as np
import pandas as pd

from gprobs.features.monthly_returns import make_forward_returns
from gprobs.features.shocks import make_gpr_shock_features
from gprobs.validation.data_contracts import ensure_columns


def build_monthly_analysis_panel(
    market_returns: pd.DataFrame,
    gpr: pd.DataFrame,
    gdelt: pd.DataFrame,
    macro_controls: pd.DataFrame,
) -> pd.DataFrame:
    ensure_columns(market_returns, ["date_month", "market_id", "market_class", "excess_return"])
    ensure_columns(gpr, ["date_month", "gpr_global", "gprt_global", "gpra_global"])
    ensure_columns(gdelt, ["date_month", "risk_index_raw", "risk_index_zscore"])
    ensure_columns(macro_controls, ["date_month", "indicator_code", "value"])

    panel = make_forward_returns(market_returns, [1, 3, 6])
    gpr_features = make_gpr_shock_features(gpr)
    gdelt_monthly = _aggregate_month_level_gdelt(gdelt)
    gdelt_features = gdelt_monthly[["date_month", "risk_index_raw", "risk_index_zscore"]].rename(
        columns={"risk_index_raw": "gdelt_risk_raw", "risk_index_zscore": "gdelt_risk_z"}
    )
    macro_monthly = _aggregate_month_level_macro_controls(
        macro_controls,
        pd.Series(panel["date_month"].drop_duplicates().sort_values()),
    )
    macro_wide = (
        macro_monthly.pivot_table(
            index="date_month",
            columns="indicator_code",
            values="value",
            aggfunc="first",
        )
        .reset_index()
        .rename_axis(columns=None)
    )

    spread = (
        panel.pivot_table(index="date_month", columns="market_id", values="excess_return")
        .assign(spread_em_dev=lambda df: df["emerging"] - df["developed"])
        [["spread_em_dev"]]
        .reset_index()
    )

    panel = (
        panel.merge(
            gpr_features[
                [
                    "date_month",
                    "gpr_global",
                    "gprt_global",
                    "gpra_global",
                    "gpr_level_z",
                    "gpr_global_z",
                    "gpr_change",
                    "gpr_change_z",
                    "gpr_log_change",
                    "gpr_log_change_z",
                    "gpr_ar1_residual",
                    "gpr_ar1_residual_z",
                    "gprt_global_z",
                    "gpra_global_z",
                ]
            ],
            on="date_month",
            how="left",
        )
        .merge(gdelt_features, on="date_month", how="left")
        .merge(macro_wide, on="date_month", how="left")
        .merge(spread, on="date_month", how="left")
    )
    panel["neg_ret_1m"] = _downside_indicator(panel["ret_fwd_1m"], threshold=0.0)
    tail_cutoff = panel["ret_fwd_1m"].quantile(0.1)
    panel["left_tail_1m"] = _downside_indicator(panel["ret_fwd_1m"], threshold=tail_cutoff)

    return panel.sort_values(["date_month", "market_id"]).reset_index(drop=True)


def _aggregate_month_level_gdelt(gdelt: pd.DataFrame) -> pd.DataFrame:
    if not gdelt["date_month"].duplicated().any():
        return gdelt.copy()

    risk_columns = [
        "conflict_count",
        "protest_count",
        "sanction_count",
        "diplomatic_conflict_count",
    ]
    if all(column in gdelt.columns for column in risk_columns):
        monthly = gdelt.groupby("date_month", as_index=False)[risk_columns].sum()
        monthly["risk_index_raw"] = np.log1p(monthly[risk_columns].sum(axis=1))
    else:
        monthly = gdelt.groupby("date_month", as_index=False).agg(risk_index_raw=("risk_index_raw", "mean"))

    monthly["risk_index_zscore"] = _zscore(monthly["risk_index_raw"])
    return monthly[["date_month", "risk_index_raw", "risk_index_zscore"]]


def _aggregate_month_level_macro_controls(
    macro_controls: pd.DataFrame,
    panel_months: pd.Series,
) -> pd.DataFrame:
    monthly = (
        macro_controls.groupby(["date_month", "indicator_code"], as_index=False)
        .agg(value=("value", "mean"))
        .sort_values(["indicator_code", "date_month"])
    )
    panel_dates = pd.DataFrame({"date_month": pd.to_datetime(panel_months).sort_values().unique()})
    frames = []
    for indicator_code, group in monthly.groupby("indicator_code", sort=False):
        aligned = panel_dates.merge(group, on="date_month", how="left")
        aligned["indicator_code"] = indicator_code
        aligned["value"] = aligned["value"].ffill()
        frames.append(aligned)
    if not frames:
        return monthly
    return pd.concat(frames, ignore_index=True)


def _zscore(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="raise").astype(float)
    std = numeric.std(ddof=0)
    if std == 0 or pd.isna(std):
        return numeric.where(numeric.isna(), 0.0)
    return (numeric - numeric.mean()) / std


def _downside_indicator(values: pd.Series, threshold: float) -> pd.Series:
    result = pd.Series(pd.NA, index=values.index, dtype="Int64")
    observed = values.notna()
    result.loc[observed] = (values.loc[observed] < threshold).astype("Int64")
    return result
