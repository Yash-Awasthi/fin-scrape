import math

import pandas as pd

from gprobs.config import EVIDENCE_EVENT_SHOCK_QUANTILE, EVIDENCE_EVENT_WINDOW_DAYS

SUMMARY_COLUMNS = [
    "method",
    "focus",
    "estimate",
    "unit",
    "p_value",
    "inference",
    "plain_english",
]


def _single_row(table: pd.DataFrame, mask: pd.Series, label: str) -> pd.Series:
    rows = table.loc[mask]
    if rows.empty:
        raise ValueError(f"Missing {label} in evidence summary inputs.")
    return rows.iloc[0]


def _term_row(table: pd.DataFrame, term: str, label: str) -> pd.Series:
    return _single_row(table, table["term"] == term, label)


def _quantile_row(
    table: pd.DataFrame,
    quantile: float,
    term: str,
    label: str,
) -> pd.Series:
    mask = (table["quantile"].sub(quantile).abs() < 1e-9) & (table["term"] == term)
    return _single_row(table, mask, label)


def _local_projection_row(
    table: pd.DataFrame,
    horizon: int,
    market_group: str,
) -> pd.Series:
    mask = (table["horizon"] == horizon) & (table["market_group"] == market_group)
    return _single_row(table, mask, f"{horizon}-day {market_group} local projection")


def _event_robustness_row(
    table: pd.DataFrame,
    shock_quantile: float,
    window: int,
    market_group: str,
) -> pd.Series:
    mask = (
        (table["shock_quantile"].sub(shock_quantile).abs() < 1e-9)
        & (table["window"] == window)
        & (table["market_group"] == market_group)
    )
    return _single_row(
        table,
        mask,
        f"{shock_quantile:.0%} shock {window}-day {market_group} event robustness",
    )


def _add_row(
    rows: list[dict],
    method: str,
    focus: str,
    estimate: float,
    unit: str,
    p_value: float,
    inference: str,
    plain_english: str,
) -> None:
    rows.append(
        {
            "method": method,
            "focus": focus,
            "estimate": float(estimate),
            "unit": unit,
            "p_value": p_value,
            "inference": inference,
            "plain_english": plain_english,
        }
    )


def _quantile_inference(row: pd.Series) -> str:
    if row.get("inference") == "iid_asymptotic":
        return "i.i.d. QuantReg asymptotic p-value"
    return str(row.get("inference", "QuantReg p-value"))


def build_evidence_summary(
    baseline_regression: pd.DataFrame,
    controlled_regression: pd.DataFrame,
    date_fe_regression: pd.DataFrame,
    quantile_regression: pd.DataFrame,
    local_projections: pd.DataFrame,
    event_robustness: pd.DataFrame,
    drawdown_metrics: pd.DataFrame,
) -> pd.DataFrame:
    """Build a compact plain-English table from existing model outputs."""
    rows: list[dict] = []

    baseline_gpr = _term_row(baseline_regression, "gpr_change_z", "gpr_change_z")
    _add_row(
        rows,
        "Baseline panel regression",
        "Developed-market GPR-change coefficient",
        baseline_gpr["estimate"],
        "basis_points",
        float(baseline_gpr["p_value"]),
        "two-way clustered by ticker/date",
        "Before market controls, this is the developed-market response to a one-SD GPR jump.",
    )

    controlled_gpr = _term_row(
        controlled_regression,
        "gpr_change_z",
        "controlled gpr_change_z",
    )
    _add_row(
        rows,
        "Controlled panel regression",
        "Developed-market GPR-change coefficient",
        controlled_gpr["estimate"],
        "basis_points",
        float(controlled_gpr["p_value"]),
        "two-way clustered by ticker/date",
        "After market controls, this is the developed-market response to a one-SD GPR jump.",
    )

    interaction = _term_row(
        controlled_regression,
        "gpr_change_z:emerging_market",
        "gpr_change_z:emerging_market",
    )
    _add_row(
        rows,
        "Controlled emerging interaction",
        "Extra emerging-market GPR-change coefficient",
        interaction["estimate"],
        "basis_points",
        float(interaction["p_value"]),
        "two-way clustered by ticker/date",
        "This is the extra emerging-market response to a one-SD GPR jump after controls.",
    )

    date_fe_interaction = _term_row(
        date_fe_regression,
        "gpr_change_z:emerging_market",
        "date fixed-effects gpr_change_z:emerging_market",
    )
    _add_row(
        rows,
        "Date fixed-effects emerging interaction",
        "Extra emerging-market GPR-change coefficient with date FE",
        date_fe_interaction["estimate"],
        "basis_points",
        float(date_fe_interaction["p_value"]),
        "two-way clustered by ticker/date",
        "This identifies the emerging-market differential after absorbing common date shocks.",
    )

    q10_gpr = _quantile_row(
        quantile_regression,
        0.10,
        "gpr_change_z",
        "10th-percentile gpr_change_z",
    )
    _add_row(
        rows,
        "Tail-risk quantile regression",
        "10th-percentile GPR coefficient",
        q10_gpr["estimate"],
        "basis_points",
        float(q10_gpr["p_value"]),
        _quantile_inference(q10_gpr),
        "This checks whether GPR matters on bad return days; its p-value is not cluster robust.",
    )

    horizon = int(local_projections["horizon"].max())
    for market_group in ["developed", "emerging"]:
        lp_row = _local_projection_row(local_projections, horizon, market_group)
        _add_row(
            rows,
            f"Local projection {market_group}",
            f"{horizon}-day cumulative abnormal response",
            lp_row["estimate"],
            "percent",
            float(lp_row["p_value"]),
            "two-way clustered by ticker/date",
            "This is the cumulative market-model abnormal return response after a GPR shock.",
        )

    for market_group in ["developed", "emerging"]:
        event_row = _event_robustness_row(
            event_robustness,
            EVIDENCE_EVENT_SHOCK_QUANTILE,
            EVIDENCE_EVENT_WINDOW_DAYS,
            market_group,
        )
        _add_row(
            rows,
            f"Event robustness {market_group}",
            f"{EVIDENCE_EVENT_SHOCK_QUANTILE:.0%} shock, {EVIDENCE_EVENT_WINDOW_DAYS}-day endpoint",
            event_row["cumulative_average_abnormal_return"],
            "percent",
            float(event_row.get("p_value", math.nan)),
            "cross-sectional t-test across event-ticker CARs",
            "This is the abnormal-return endpoint under a wider shock definition.",
        )

    if drawdown_metrics.empty:
        raise ValueError("Missing drawdown metrics in evidence summary inputs.")
    drawdown_headline = drawdown_metrics
    if "model_name" in drawdown_metrics.columns:
        drawdown_headline = drawdown_metrics.loc[
            drawdown_metrics["model_name"] == "full_features"
        ]
        if drawdown_headline.empty:
            raise ValueError("Missing full_features rows in drawdown metrics.")

    mean_auc = round(float(drawdown_headline["roc_auc"].mean()), 6)
    mean_ap = float(drawdown_headline["average_precision"].mean())
    mean_base_rate = float(drawdown_headline["base_rate"].mean())
    _add_row(
        rows,
        "Drawdown classifier",
        "Mean ROC AUC",
        mean_auc,
        "score",
        math.nan,
        "cross-validation metric",
        f"Average precision is {mean_ap:.3f} versus base rate {mean_base_rate:.1%}.",
    )

    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)
