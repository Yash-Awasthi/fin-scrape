import pandas as pd

ML_VALIDATION_HEADING = "Purged Chronological Validation"
ML_VALIDATION_CAPTION = (
    "Splits are purged chronological, so the model trains only on earlier dates "
    "and excludes dates immediately before the test fold to reduce forward-label leakage."
)
FEATURE_IMPORTANCE_CAPTION = (
    "Feature importance is a full-sample interpretive diagnostic for the fitted "
    "drawdown-risk classifier, not out-of-sample evidence by itself."
)
PREDICTION_LAB_CONCLUSION = (
    "Prediction Lab currently shows modest drawdown-risk ranking signal, mostly from volatility and broad market "
    "features; GPR alone is weak and should not be read as a price forecast or trading signal."
)
MODEL_DESCRIPTIONS = {
    "constant_baseline": "Average historical event rate only",
    "volatility_only": "Recent ETF volatility",
    "gpr_only": "GPR features only",
    "market_controls_only": "Global market, VIX, oil, dollar, and rates",
    "volatility_plus_gpr": "Volatility plus GPR",
    "full_features": "All available features",
}
BEGINNER_MODEL_COMPARISON_COLUMNS = [
    "model_name",
    "what_it_uses",
    "mean_roc_auc",
    "delta_auc_vs_constant_baseline",
    "mean_average_precision",
    "delta_ap_vs_constant_baseline",
    "top_decile_lift",
    "mean_brier_score",
    "delta_brier_vs_constant_baseline",
    "model_verdict",
]


def build_model_summary(drawdown_metrics: pd.DataFrame, drawdown_lift: pd.DataFrame) -> pd.DataFrame:
    model_summary = (
        drawdown_metrics.groupby("model_name", as_index=False)
        .agg(
            mean_roc_auc=("roc_auc", "mean"),
            mean_average_precision=("average_precision", "mean"),
            mean_brier_score=("brier_score", "mean"),
            mean_base_rate=("base_rate", "mean"),
            observation_count=("observation_count", "sum"),
        )
        .sort_values("mean_roc_auc", ascending=False)
    )
    top_decile_lift = (
        drawdown_lift.loc[
            drawdown_lift["bucket"] == "top_10_percent",
            ["model_name", "lift"],
        ]
        .groupby("model_name", as_index=False)
        .agg(top_decile_lift=("lift", "mean"))
    )
    model_summary = model_summary.merge(top_decile_lift, on="model_name", how="left")
    baseline_auc = _constant_baseline_value(model_summary, "mean_roc_auc")
    baseline_ap = _constant_baseline_value(model_summary, "mean_average_precision")
    baseline_brier = _constant_baseline_value(model_summary, "mean_brier_score")
    model_summary["what_it_uses"] = model_summary["model_name"].map(
        lambda model_name: MODEL_DESCRIPTIONS.get(model_name, "Model-specific feature group")
    )
    model_summary["delta_auc_vs_constant_baseline"] = model_summary["mean_roc_auc"] - baseline_auc
    model_summary["delta_ap_vs_constant_baseline"] = (
        model_summary["mean_average_precision"] - baseline_ap
    )
    model_summary["delta_brier_vs_constant_baseline"] = (
        baseline_brier - model_summary["mean_brier_score"]
    )
    model_summary["model_verdict"] = model_summary.apply(
        lambda row: model_verdict_label(
            row["mean_roc_auc"],
            row["delta_auc_vs_constant_baseline"],
            row["top_decile_lift"],
        ),
        axis=1,
    )
    return model_summary[
        [
            "model_name",
            "what_it_uses",
            "mean_roc_auc",
            "delta_auc_vs_constant_baseline",
            "mean_average_precision",
            "delta_ap_vs_constant_baseline",
            "mean_brier_score",
            "delta_brier_vs_constant_baseline",
            "mean_base_rate",
            "observation_count",
            "top_decile_lift",
            "model_verdict",
        ]
    ]


def model_verdict_label(
    mean_roc_auc: float,
    delta_auc_vs_constant_baseline: float,
    top_decile_lift: float,
) -> str:
    if (
        pd.isna(mean_roc_auc)
        or pd.isna(delta_auc_vs_constant_baseline)
        or pd.isna(top_decile_lift)
        or mean_roc_auc < 0.53
        or delta_auc_vs_constant_baseline < 0.02
        or top_decile_lift < 1.05
    ):
        return "No useful ranking signal"
    if mean_roc_auc < 0.58 or delta_auc_vs_constant_baseline < 0.08 or top_decile_lift < 1.25:
        return "Weak ranking signal"
    if mean_roc_auc < 0.65 or delta_auc_vs_constant_baseline < 0.15 or top_decile_lift < 1.75:
        return "Modest ranking signal"
    return "Useful signal, not trading-grade"


def _constant_baseline_value(model_summary: pd.DataFrame, column: str) -> float:
    baseline = model_summary.loc[model_summary["model_name"] == "constant_baseline", column]
    if baseline.empty:
        return float("nan")
    return float(baseline.iloc[0])


def best_model_metric_labels(model_summary: pd.DataFrame) -> dict[str, tuple[str, str]]:
    return {
        "auc": _best_metric_label(model_summary, "mean_roc_auc", "Best model AUC", "{:.3f}"),
        "ap": _best_metric_label(model_summary, "mean_average_precision", "Best model AP", "{:.3f}"),
        "lift": _best_metric_label(model_summary, "top_decile_lift", "Top-decile lift", "{:.2f}x"),
    }


def _best_metric_label(
    model_summary: pd.DataFrame,
    metric_col: str,
    label: str,
    value_format: str,
) -> tuple[str, str]:
    metric_values = pd.to_numeric(model_summary[metric_col], errors="coerce")
    if metric_values.isna().all():
        return label, "n/a"
    best_row = model_summary.loc[metric_values.idxmax()]
    model_name = best_row["model_name"]
    return f"{label} ({model_name})", value_format.format(float(best_row[metric_col]))
