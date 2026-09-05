import numpy as np
import pandas as pd

from gprobs.features.gpr_terms import MONTHLY_DESCRIPTIVE_GPR_CHANGE_Z
from gprobs.validation.data_contracts import ensure_columns

MONTHLY_GPR_CHANGE_Z_CONTEXT = MONTHLY_DESCRIPTIVE_GPR_CHANGE_Z


def standardize_shocks(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    ensure_columns(df, cols)
    result = df.copy()

    for column in cols:
        values = pd.to_numeric(result[column], errors="raise")
        result[f"{column}_z"] = _zscore(values)

    return result


def make_gpr_shock_features(df: pd.DataFrame) -> pd.DataFrame:
    ensure_columns(df, ["date_month", "gpr_global", "gprt_global", "gpra_global"])
    result = df.copy()
    result["_original_order"] = range(len(result))
    result = result.sort_values("date_month").reset_index(drop=True)
    values = pd.to_numeric(result["gpr_global"], errors="raise").astype(float)
    if not np.isfinite(values.dropna()).all():
        raise ValueError("gpr_global must contain only finite values")
    if values.le(0).any():
        raise ValueError("gpr_global must be positive to compute log changes")

    result["gpr_level_z"] = _zscore(values)
    result["gpr_global_z"] = result["gpr_level_z"]
    result["gpr_change"] = values.diff()
    result["gpr_change_z"] = _zscore(result["gpr_change"])
    result["gpr_log_change"] = np.log(values).diff()
    result["gpr_log_change_z"] = _zscore(result["gpr_log_change"])
    result["gpr_ar1_residual"] = _ar1_residual(values)
    result["gpr_ar1_residual_z"] = _zscore(result["gpr_ar1_residual"])
    result["gprt_global_z"] = _zscore(result["gprt_global"])
    result["gpra_global_z"] = _zscore(result["gpra_global"])
    return result.sort_values("_original_order").drop(columns=["_original_order"]).reset_index(drop=True)


def expanding_standardize_shocks(
    df: pd.DataFrame,
    cols: list[str],
    date_col: str = "date_month",
    group_cols: list[str] | None = None,
    min_periods: int = 24,
) -> pd.DataFrame:
    ensure_columns(df, [date_col, *cols, *(group_cols or [])])
    result = df.copy()
    result["_original_order"] = range(len(result))

    sort_cols = [*(group_cols or []), date_col]
    result = result.sort_values(sort_cols)
    for column in cols:
        if group_cols:
            result[f"{column}_z"] = result.groupby(group_cols, group_keys=False)[column].transform(
                lambda series: _prior_expanding_zscore(series, min_periods)
            )
        else:
            result[f"{column}_z"] = _prior_expanding_zscore(result[column], min_periods)

    return result.sort_values("_original_order").drop(columns=["_original_order"]).reset_index(drop=True)


def _prior_expanding_zscore(series: pd.Series, min_periods: int) -> pd.Series:
    values = pd.to_numeric(series, errors="raise").astype(float)
    if not np.isfinite(values.dropna()).all():
        raise ValueError("shock values must contain only finite numeric values")
    prior_count = values.expanding(min_periods=1).count().shift(1)
    has_history = prior_count >= min_periods
    mean = values.expanding(min_periods=min_periods).mean().shift(1)
    std = values.expanding(min_periods=min_periods).std(ddof=0).shift(1)
    zscore = (values - mean) / std
    zscore = zscore.replace([float("inf"), float("-inf")], pd.NA)
    zero_std = has_history & std.eq(0) & values.notna()
    zscore = zscore.mask(zero_std, 0.0)
    return zscore.where(has_history)


def _zscore(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="raise").astype(float)
    if not np.isfinite(numeric.dropna()).all():
        raise ValueError("z-score inputs must contain only finite numeric values")
    std = numeric.std(ddof=0)
    if std == 0 or pd.isna(std):
        return numeric.where(numeric.isna(), 0.0)
    return (numeric - numeric.mean()) / std


def _ar1_residual(values: pd.Series) -> pd.Series:
    lagged = values.shift(1)
    data = pd.DataFrame({"value": values, "lagged": lagged}).dropna()
    residuals = pd.Series(np.nan, index=values.index, dtype=float)
    if len(data) < 2:
        return residuals

    x = np.column_stack([np.ones(len(data)), data["lagged"].to_numpy(dtype=float)])
    y = data["value"].to_numpy(dtype=float)
    beta = np.linalg.pinv(x.T @ x) @ x.T @ y
    residuals.loc[data.index] = y - x @ beta
    return residuals
