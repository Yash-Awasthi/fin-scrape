import pandas as pd
import statsmodels.formula.api as smf

from gprobs.analysis.panel_regression import CONTROL_COLUMNS, prepare_panel_regression_data

QUANTILE_COLUMNS = [
    "quantile",
    "term",
    "estimate",
    "std_error",
    "t_stat",
    "p_value",
    "inference",
]

BASE_FORMULA = "etf_return ~ gpr_change_z + gpr_change_z:emerging_market + C(ticker)"
CONTROLLED_FORMULA = (
    "etf_return ~ gpr_change_z + gpr_change_z:emerging_market + "
    "global_market_return + vix_change + oil_change + dollar_return + us10y_change + "
    "C(ticker)"
)


def run_quantile_regressions(
    panel: pd.DataFrame,
    quantiles: list[float],
    include_controls: bool = True,
) -> pd.DataFrame:
    """Estimate return sensitivity to GPR at different return quantiles."""
    if not quantiles:
        raise ValueError("At least one quantile is required.")
    for quantile in quantiles:
        if not 0 < quantile < 1:
            raise ValueError("Quantiles must be between 0 and 1.")

    data = prepare_panel_regression_data(panel, include_controls=include_controls)
    if include_controls:
        data = data.dropna(subset=CONTROL_COLUMNS)

    formula = CONTROLLED_FORMULA if include_controls else BASE_FORMULA
    model = smf.quantreg(formula, data=data)

    frames = []
    for quantile in quantiles:
        result = model.fit(q=quantile, max_iter=1000)
        table = _tidy_quantile_result(result, quantile)
        frames.append(table)

    return pd.concat(frames, ignore_index=True)


def _tidy_quantile_result(result, quantile: float) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "quantile": quantile,
            "term": result.params.index,
            "estimate": result.params.values,
            "std_error": result.bse.values,
            "t_stat": result.tvalues.values,
            "p_value": result.pvalues.values,
            "inference": "iid_asymptotic",
        }
    )[QUANTILE_COLUMNS]
