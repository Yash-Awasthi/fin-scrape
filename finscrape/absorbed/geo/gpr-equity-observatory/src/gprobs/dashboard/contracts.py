"""Dashboard output file contracts shared by renderers and exporters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data" / "processed"


@dataclass(frozen=True)
class OutputSpec:
    path: Path
    date_columns: tuple[str, ...] = ()
    required_columns: tuple[str, ...] = ()
    low_memory: bool | None = None


OUTPUT_SPECS = {
    "analysis_panel": OutputSpec(
        DATA_DIR / "analysis_panel.csv",
        date_columns=("date",),
        required_columns=(
            "date",
            "ticker",
            "country",
            "market_group",
            "region",
            "return",
            "gpr",
            "gpr_change",
            "gpr_change_z",
            "gpr_shock",
            "gpr_change_shock",
            "gpr_change_shock_full_sample",
            "gpr_change_shock_expanding",
        ),
        low_memory=False,
    ),
    "gpr": OutputSpec(
        DATA_DIR / "gpr_daily.csv",
        date_columns=("date",),
        required_columns=(
            "date",
            "gpr",
            "gpr_act",
            "gpr_threat",
            "gpr_change",
            "gpr_change_z",
            "gpr_shock",
            "gpr_shock_full_sample",
            "gpr_shock_expanding",
            "gpr_change_shock",
            "gpr_change_shock_full_sample",
            "gpr_change_shock_expanding",
            "event",
        ),
    ),
    "group_returns": OutputSpec(
        DATA_DIR / "group_return_summary.csv",
        date_columns=("date",),
        required_columns=("date", "market_group", "average_return", "country_count"),
    ),
    "event_study": OutputSpec(
        DATA_DIR / "event_study_summary.csv",
        required_columns=(
            "market_group",
            "relative_day",
            "average_return",
            "cumulative_average_return",
            "observation_count",
            "event_count",
        ),
    ),
    "abnormal_event_study": OutputSpec(
        DATA_DIR / "event_study_abnormal_summary.csv",
        required_columns=(
            "market_group",
            "relative_day",
            "average_abnormal_return",
            "cumulative_average_abnormal_return",
            "observation_count",
            "event_count",
            "std_error",
            "t_stat",
            "p_value",
        ),
    ),
    "event_robustness": OutputSpec(
        DATA_DIR / "event_robustness_summary.csv",
        required_columns=(
            "shock_quantile",
            "window",
            "market_group",
            "cumulative_average_abnormal_return",
            "event_count",
            "std_error",
            "t_stat",
            "p_value",
        ),
    ),
    "regression": OutputSpec(
        DATA_DIR / "panel_regression_baseline.csv",
        required_columns=("term", "estimate", "std_error", "t_stat", "p_value"),
    ),
    "controlled_regression": OutputSpec(
        DATA_DIR / "panel_regression_controlled.csv",
        required_columns=("term", "estimate", "std_error", "t_stat", "p_value"),
    ),
    "date_fe_regression": OutputSpec(
        DATA_DIR / "panel_regression_date_fe.csv",
        required_columns=("term", "estimate", "std_error", "t_stat", "p_value"),
    ),
    "panel_sample_robustness": OutputSpec(
        DATA_DIR / "panel_sample_robustness.csv",
        required_columns=(
            "scenario",
            "term",
            "estimate",
            "std_error",
            "t_stat",
            "p_value",
            "observation_count",
            "gpr_change_mean",
            "gpr_change_std",
        ),
    ),
    "quantile_regression": OutputSpec(
        DATA_DIR / "quantile_regression_results.csv",
        required_columns=(
            "quantile",
            "term",
            "estimate",
            "std_error",
            "t_stat",
            "p_value",
            "inference",
        ),
    ),
    "local_projections": OutputSpec(
        DATA_DIR / "local_projection_results.csv",
        required_columns=(
            "horizon",
            "market_group",
            "estimate",
            "std_error",
            "ci_low",
            "ci_high",
            "p_value",
        ),
    ),
    "drawdown_metrics": OutputSpec(
        DATA_DIR / "drawdown_model_metrics.csv",
        date_columns=("train_start", "train_end", "test_start", "test_end"),
        required_columns=(
            "fold",
            "model_name",
            "train_start",
            "train_end",
            "test_start",
            "test_end",
            "roc_auc",
            "average_precision",
            "brier_score",
            "base_rate",
            "observation_count",
        ),
    ),
    "drawdown_predictions": OutputSpec(
        DATA_DIR / "drawdown_model_predictions.csv",
        date_columns=("date", "train_start", "train_end", "test_start", "test_end"),
        required_columns=(
            "date",
            "ticker",
            "country",
            "market_group",
            "fold",
            "model_name",
            "train_start",
            "train_end",
            "test_start",
            "test_end",
            "drawdown_risk",
            "predicted_probability",
            "forward_min_return",
        ),
    ),
    "drawdown_threshold_metrics": OutputSpec(
        DATA_DIR / "drawdown_model_threshold_metrics.csv",
        required_columns=(
            "model_name",
            "threshold",
            "precision",
            "recall",
            "f1",
            "share_flagged",
            "event_rate_flagged",
            "observation_count",
        ),
    ),
    "drawdown_calibration": OutputSpec(
        DATA_DIR / "drawdown_model_calibration.csv",
        required_columns=(
            "model_name",
            "probability_decile",
            "mean_predicted_probability",
            "realized_event_rate",
            "observation_count",
        ),
    ),
    "drawdown_lift": OutputSpec(
        DATA_DIR / "drawdown_model_lift.csv",
        required_columns=(
            "model_name",
            "bucket",
            "event_rate",
            "base_event_rate",
            "lift",
            "observation_count",
        ),
    ),
    "drawdown_country_risk_summary": OutputSpec(
        DATA_DIR / "drawdown_country_risk_summary.csv",
        required_columns=(
            "country",
            "market_group",
            "model_name",
            "average_predicted_probability",
            "realized_event_rate",
            "observation_count",
        ),
    ),
    "drawdown_importance": OutputSpec(
        DATA_DIR / "drawdown_feature_importance.csv",
        required_columns=("feature", "coefficient", "abs_coefficient"),
    ),
    "evidence_summary": OutputSpec(
        DATA_DIR / "evidence_summary.csv",
        required_columns=(
            "method",
            "focus",
            "estimate",
            "unit",
            "p_value",
            "inference",
            "plain_english",
        ),
    ),
    "rolling_beta": OutputSpec(
        DATA_DIR / "rolling_gpr_beta.csv",
        date_columns=("date",),
        required_columns=("date", "ticker", "country", "market_group", "rolling_gpr_beta"),
    ),
    "large_returns": OutputSpec(
        DATA_DIR / "large_return_flags.csv",
        date_columns=("date",),
        required_columns=("date", "ticker", "country", "return", "abs_return"),
    ),
}

REQUIRED_FILES = {name: spec.path for name, spec in OUTPUT_SPECS.items()}


def validate_output_schema(output: pd.DataFrame, spec: OutputSpec) -> None:
    missing_columns = [
        column for column in spec.required_columns if column not in output.columns
    ]
    if missing_columns:
        raise ValueError(f"{spec.path.name} is missing required columns: {missing_columns}")


def missing_output_files() -> list[Path]:
    return [path for path in REQUIRED_FILES.values() if not path.exists()]
