from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm

from gprobs.validation.data_contracts import ensure_columns


@dataclass(frozen=True)
class RegressionResult:
    coefficients: pd.DataFrame
    metadata: dict
    nobs: int
    adjusted_r2: float
    se_type: str

    def to_frame(self) -> pd.DataFrame:
        frame = self.coefficients.copy()
        for key, value in self.metadata.items():
            frame[key] = value
        frame["nobs"] = self.nobs
        frame["adjusted_r2"] = self.adjusted_r2
        frame["se_type"] = self.se_type
        return frame


def run_spread_regression(
    panel: pd.DataFrame,
    horizon: int,
    shock_col: str = "gpr_change_z",
    controls: list[str] | None = None,
    maxlags: int | None = None,
) -> RegressionResult:
    controls = controls or []
    target_col = f"ret_fwd_{horizon}m"
    ensure_columns(panel, ["date_month", "market_id", target_col, shock_col, *controls])
    _ensure_developed_emerging_months(panel)

    spread = (
        panel.pivot_table(index="date_month", columns="market_id", values=target_col)
        .assign(spread_fwd=lambda frame: frame["emerging"] - frame["developed"])
        [["spread_fwd"]]
        .reset_index()
    )
    predictors = _month_level_frame(panel, [shock_col, *controls])
    data = spread.merge(predictors, on="date_month").dropna()
    if data.empty:
        raise ValueError("monthly spread regression has no complete observations")

    x = sm.add_constant(data[[shock_col, *controls]], has_constant="add")
    y = data["spread_fwd"]
    hac_maxlags = maxlags if maxlags is not None else max(1, horizon)
    fitted = sm.OLS(y, x).fit(cov_type="HAC", cov_kwds={"maxlags": int(hac_maxlags)})
    return _to_result(
        fitted,
        metadata={"horizon": horizon, "model": "spread", "maxlags": int(hac_maxlags)},
        se_type="HAC",
    )


def run_panel_interaction(
    panel: pd.DataFrame,
    horizon: int,
    shock_col: str = "gpr_change_z",
    controls: list[str] | None = None,
    cluster_min_groups: int = 3,
    market_fixed_effects: bool = False,
    time_fixed_effects: bool = False,
) -> RegressionResult:
    controls = controls or []
    target_col = f"ret_fwd_{horizon}m"
    ensure_columns(panel, ["date_month", "market_id", "market_class", target_col, shock_col, *controls])
    data = panel.dropna(subset=[target_col, shock_col, *controls]).copy()
    if data.empty:
        raise ValueError("monthly panel interaction has no complete observations")

    expected_classes = {"developed", "emerging"}
    bad_classes = sorted(set(data["market_class"].dropna()) - expected_classes)
    if bad_classes:
        raise ValueError(f"market_class contains unsupported labels: {bad_classes}")

    data["emerging"] = (data["market_class"] == "emerging").astype(float)
    interaction_col = f"emerging_x_{shock_col}"
    data[interaction_col] = data["emerging"] * data[shock_col]

    x = data[[shock_col, interaction_col, *controls]].astype(float)
    y = data[target_col].astype(float)
    fixed_effect_groups = []
    if market_fixed_effects:
        fixed_effect_groups.append(data["market_id"])
    if time_fixed_effects:
        fixed_effect_groups.append(data["date_month"])

    if fixed_effect_groups:
        x = _absorb_fixed_effects(x, fixed_effect_groups)
        y = _absorb_fixed_effects(y.to_frame(target_col), fixed_effect_groups)[target_col]
    else:
        x = sm.add_constant(x, has_constant="add")

    cluster_groups = data["market_id"]
    min_clusters = max(3, int(cluster_min_groups))
    n_clusters = int(cluster_groups.nunique())
    if n_clusters < min_clusters:
        raise ValueError(
            "clustered standard errors require at least "
            f"{min_clusters} unique market_id clusters; got {n_clusters}"
        )

    fitted = sm.OLS(y, x).fit(cov_type="cluster", cov_kwds={"groups": cluster_groups})
    return _to_result(
        fitted,
        metadata={"horizon": horizon, "model": "panel_interaction", "cluster_min_groups": min_clusters},
        se_type="clustered",
    )


def _ensure_developed_emerging_months(panel: pd.DataFrame) -> None:
    required_markets = {"developed", "emerging"}
    coverage = panel.groupby("date_month")["market_id"].agg(lambda values: set(values))
    bad_months = coverage[coverage != required_markets]
    if not bad_months.empty:
        raise ValueError("panel must contain developed and emerging markets for every month")


def _month_level_frame(panel: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    uniqueness = panel.groupby("date_month")[columns].nunique(dropna=False)
    varying = uniqueness.gt(1).any(axis=1)
    if varying.any():
        sample = [pd.Timestamp(value).strftime("%Y-%m-%d") for value in uniqueness.index[varying][:5]]
        raise ValueError(f"predictor columns must be unique within date_month; bad months: {sample}")
    return panel.drop_duplicates("date_month")[["date_month", *columns]]


def _absorb_fixed_effects(values: pd.DataFrame, groups: list[pd.Series], max_iter: int = 100) -> pd.DataFrame:
    residual = values.copy()
    for _ in range(max_iter):
        previous = residual.to_numpy(copy=True)
        for group in groups:
            residual = residual - residual.groupby(group, sort=False).transform("mean")
        if np.max(np.abs(residual.to_numpy() - previous)) < 1e-10:
            break
    return residual


def _to_result(fitted, metadata: dict, se_type: str) -> RegressionResult:
    coefficients = pd.DataFrame(
        {
            "term": fitted.params.index,
            "estimate": fitted.params.to_numpy(),
            "std_error": fitted.bse.to_numpy(),
            "t_value": fitted.tvalues.to_numpy(),
            "p_value": fitted.pvalues.to_numpy(),
        }
    )
    return RegressionResult(
        coefficients=coefficients,
        metadata=metadata,
        nobs=int(fitted.nobs),
        adjusted_r2=float(fitted.rsquared_adj),
        se_type=se_type,
    )
