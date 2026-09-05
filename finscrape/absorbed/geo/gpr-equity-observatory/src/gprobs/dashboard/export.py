"""Export chart-ready JSON for the Next.js frontend.

The frontend is presentation-only. Every derived table that the dashboard
computes in Python is computed here too (reusing the same helpers) and written
as JSON so the TypeScript app never needs to reimplement analysis logic or
research-claim wording.
"""

from __future__ import annotations

import dataclasses
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from gprobs.config import DRAWDOWN_HORIZON_DAYS, DRAWDOWN_THRESHOLD
from gprobs.dashboard.components import (
    BEGINNER_TAB_GUIDES,
    CENTRAL_PROJECT_QUESTION,
    DASHBOARD_INTRO,
    DASHBOARD_MAIN_TAKEAWAY,
    DASHBOARD_USE_NOTE,
    GLOSSARY_TERMS,
    HOW_TO_READ_NOTES,
    METHOD_MAP_ROWS,
    OVERVIEW_CURRENT_ANSWER_POINTS,
    OVERVIEW_DOES_NOT_PROVE_POINTS,
    OVERVIEW_JOB_STATEMENTS,
    OVERVIEW_READER_PATH,
    PREDICTION_METRIC_EXPLANATIONS,
)
from gprobs.dashboard.contracts import (
    OUTPUT_SPECS,
    PROJECT_ROOT,
    OutputSpec,
    validate_output_schema,
)
from gprobs.dashboard.evidence import build_evidence_map
from gprobs.dashboard.metrics import build_country_coverage, select_key_regression_terms
from gprobs.dashboard.monthly import (
    MONTHLY_CLUSTER_NOTICE,
    MONTHLY_EMPTY_STATE_COMMANDS,
    MONTHLY_EMPTY_STATE_NOTE,
    MONTHLY_MODE_PRIORITY_NOTICE,
    MONTHLY_MODES,
    MONTHLY_REAL_NOTICE,
    MONTHLY_SAMPLE_NOTICE,
    _load_monthly_output_mode,
    monthly_provenance_rows,
)
from gprobs.dashboard.prediction import (
    FEATURE_IMPORTANCE_CAPTION,
    ML_VALIDATION_CAPTION,
    ML_VALIDATION_HEADING,
    PREDICTION_LAB_CONCLUSION,
    best_model_metric_labels,
    build_model_summary,
)

__all__ = ["build_frontend_payloads", "write_frontend_payloads", "export_frontend_data"]

DEFAULT_TARGET_DIR = PROJECT_ROOT / "frontend" / "public" / "data"

OUTPUT_FILE_MEANINGS = {
    "gpr": ("GPR Data", "Daily geopolitical risk values and shock flags."),
    "analysis_panel": ("Start Here", "The main daily dataset: country ETF returns merged with GPR and controls."),
    "group_returns": ("Market Reaction", "Average daily ETF returns by developed and emerging market group."),
    "abnormal_event_study": ("Market Reaction", "Average abnormal returns around GPR shock days."),
    "controlled_regression": ("Regression Results", "The panel regression after market controls are included."),
    "date_fe_regression": ("Regression Results", "The developed-versus-emerging comparison with date fixed effects."),
    "quantile_regression": ("Regression Results", "The downside-risk check across return percentiles."),
    "local_projections": ("Market Reaction", "The estimated response path after GPR shock days."),
    "drawdown_metrics": ("Prediction Lab", "Out-of-sample drawdown-risk classifier scores."),
    "drawdown_lift": ("Prediction Lab", "How concentrated bad outcomes are in high-risk buckets."),
    "drawdown_country_risk_summary": ("Prediction Lab", "Average predicted and realized drawdown risk by country."),
    "rolling_beta": ("Country Sensitivity", "Rolling country ETF sensitivity to GPR."),
    "large_returns": ("Data Quality", "Large daily ETF returns worth checking before over-interpreting results."),
    "evidence_summary": ("Start Here", "A compact cross-method evidence table."),
}


def _spec_path(spec: OutputSpec, root: Path) -> Path:
    return root / spec.path.relative_to(PROJECT_ROOT)


def _read_output(spec: OutputSpec, root: Path) -> pd.DataFrame:
    options: dict[str, Any] = {}
    if spec.date_columns:
        options["parse_dates"] = list(spec.date_columns)
    if spec.low_memory is not None:
        options["low_memory"] = spec.low_memory
    df = pd.read_csv(_spec_path(spec, root), **options)
    validate_output_schema(df, spec)
    return df


def _missing_spec_paths(root: Path) -> list[str]:
    missing: list[str] = []
    for spec in OUTPUT_SPECS.values():
        path = _spec_path(spec, root)
        if not path.exists():
            missing.append(str(path.relative_to(root)))
    return missing


def _scalar(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        v = float(value)
        return None if math.isnan(v) else v
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    return value


def _df_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime("%Y-%m-%d")
    records = df.to_dict(orient="records")
    return [{key: _scalar(value) for key, value in record.items()} for record in records]


def _direction_label(value: Any) -> str:
    if value is None or pd.isna(value):
        return "Unknown"
    numeric = float(value)
    if abs(numeric) < 1e-12:
        return "Near zero"
    return "Positive" if numeric > 0 else "Negative"


def _p_value_reader_label(value: Any) -> str:
    if value is None or pd.isna(value):
        return "Descriptive only"
    numeric = float(value)
    if numeric < 0.05:
        return "Conventional p < 0.05"
    if numeric < 0.10:
        return "Suggestive p < 0.10"
    return "Weak in this run"


def _market_group_label(value: Any) -> str:
    raw = str(value)
    if raw == "developed":
        return "Developed markets"
    if raw == "emerging":
        return "Emerging markets"
    return raw


def _load_monthly_bundle(root: Path):
    for mode, config in MONTHLY_MODES.items():
        bundle = _load_monthly_output_mode(mode, dataclasses.replace(config, root=root))
        if bundle is not None:
            return bundle
    return None


def _output_file_rows(outputs: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, (reader_page, meaning) in OUTPUT_FILE_MEANINGS.items():
        spec = OUTPUT_SPECS[key]
        rows.append(
            {
                "file": str(spec.path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "reader_page": reader_page,
                "rows": int(len(outputs[key])),
                "plain_meaning": meaning,
            }
        )
    return rows


def _event_study_reader_rows(abnormal: pd.DataFrame) -> list[dict[str, Any]]:
    wanted_days = [0, 1, 5, 10]
    key_days = abnormal.loc[abnormal["relative_day"].isin(wanted_days)].copy()
    if key_days.empty:
        key_days = abnormal.copy()
    key_days = key_days.sort_values(["market_group", "relative_day"])

    rows: list[dict[str, Any]] = []
    for row in key_days.to_dict(orient="records"):
        group = _market_group_label(row["market_group"])
        day = int(row["relative_day"])
        estimate = row["cumulative_average_abnormal_return"]
        direction = _direction_label(estimate)
        strength = _p_value_reader_label(row.get("p_value"))
        rows.append(
            {
                "market_group": group,
                "relative_day": day,
                "cumulative_average_abnormal_return": estimate,
                "direction": direction,
                "evidence_strength": strength,
                "plain_note": (
                    f"{group} average abnormal return was {direction.lower()} by day {day}. "
                    f"Treat this as {strength.lower()}, not as a one-day rule."
                ),
            }
        )
    return rows


def _first_term_row(df: pd.DataFrame, term: str) -> pd.Series | None:
    matches = df.loc[df["term"] == term]
    if matches.empty:
        return None
    return matches.iloc[0]


def _reader_regression_row(
    *,
    test: str,
    check: str,
    row: pd.Series | None,
    note: str,
) -> dict[str, Any]:
    if row is None:
        return {
            "test": test,
            "what_it_checks": check,
            "direction": "Missing",
            "estimate": None,
            "p_value": None,
            "evidence_strength": "Missing output",
            "plain_note": note,
        }
    return {
        "test": test,
        "what_it_checks": check,
        "direction": _direction_label(row.get("estimate")),
        "estimate": row.get("estimate"),
        "p_value": row.get("p_value"),
        "evidence_strength": _p_value_reader_label(row.get("p_value")),
        "plain_note": note,
    }


def _regression_translation_rows(outputs: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    controlled_gpr = _first_term_row(outputs["controlled_regression"], "gpr_change_z")
    emerging_extra = _first_term_row(outputs["date_fe_regression"], "gpr_change_z:emerging_market")

    quantile = outputs["quantile_regression"].sort_values("quantile")
    quantile_gpr = _first_term_row(quantile, "gpr_change_z")
    if quantile_gpr is None and not quantile.empty:
        quantile_gpr = quantile.iloc[0]

    return [
        _reader_regression_row(
            test="Controlled GPR association",
            check="Whether GPR jumps are associated with ETF returns after market controls.",
            row=controlled_gpr,
            note="Read this as conditional association, not cause and effect.",
        ),
        _reader_regression_row(
            test="Emerging-market extra response",
            check="Whether emerging-market ETFs have an extra GPR response versus developed-market ETFs.",
            row=emerging_extra,
            note="This is the cleanest daily-panel check for the emerging-market question.",
        ),
        _reader_regression_row(
            test="Downside-risk check",
            check="Whether lower-return days show a different GPR relationship.",
            row=quantile_gpr,
            note="This is a tail-risk diagnostic; it is not proof that the pattern is stable.",
        ),
    ]


def _static_copy() -> dict[str, Any]:
    return {
        "central_question": CENTRAL_PROJECT_QUESTION,
        "intro": DASHBOARD_INTRO,
        "main_takeaway": DASHBOARD_MAIN_TAKEAWAY,
        "use_note": DASHBOARD_USE_NOTE,
        "job_statements": [
            {"title": title, "body": body} for title, body in OVERVIEW_JOB_STATEMENTS
        ],
        "reader_path": [dict(row) for row in OVERVIEW_READER_PATH],
        "current_answer_points": list(OVERVIEW_CURRENT_ANSWER_POINTS),
        "does_not_prove_points": list(OVERVIEW_DOES_NOT_PROVE_POINTS),
        "method_map": [dict(row) for row in METHOD_MAP_ROWS],
        "glossary": dict(GLOSSARY_TERMS),
        "prediction_metric_explanations": dict(PREDICTION_METRIC_EXPLANATIONS),
        "how_to_read": dict(HOW_TO_READ_NOTES),
        "beginner_guides": {
            key: {
                "question": value["question"],
                "takeaways": [
                    {"title": title, "body": body} for title, body in value["takeaways"]
                ],
                "does_not_prove": value["does_not_prove"],
            }
            for key, value in BEGINNER_TAB_GUIDES.items()
        },
        "monthly_notices": {
            "sample": MONTHLY_SAMPLE_NOTICE,
            "real": MONTHLY_REAL_NOTICE,
            "cluster": MONTHLY_CLUSTER_NOTICE,
            "mode_priority": MONTHLY_MODE_PRIORITY_NOTICE,
            "empty_state_commands": list(MONTHLY_EMPTY_STATE_COMMANDS),
            "empty_state_note": MONTHLY_EMPTY_STATE_NOTE,
        },
        "prediction_lab": {
            "conclusion": PREDICTION_LAB_CONCLUSION,
            "validation_heading": ML_VALIDATION_HEADING,
            "validation_caption": ML_VALIDATION_CAPTION,
            "feature_importance_caption": FEATURE_IMPORTANCE_CAPTION,
            "drawdown_horizon_days": int(DRAWDOWN_HORIZON_DAYS),
            "drawdown_threshold": float(DRAWDOWN_THRESHOLD),
        },
    }


def _overview_payloads(outputs: dict[str, pd.DataFrame], panel: pd.DataFrame, gpr: pd.DataFrame) -> dict[str, Any]:
    start_date = panel["date"].min().date().isoformat()
    end_date = panel["date"].max().date().isoformat()
    country_count = int(panel["country"].nunique())
    shock_count = int(gpr["gpr_change_shock"].sum())

    gpr_window = gpr.loc[gpr["date"].between(panel["date"].min(), panel["date"].max())].sort_values("date")
    top_shocks = gpr.sort_values("gpr_change", ascending=False).head(25)

    group_chart = outputs["group_returns"].copy()
    group_chart["cumulative_average_return"] = group_chart.groupby("market_group")[
        "average_return"
    ].cumsum()

    evidence_map = build_evidence_map(outputs["evidence_summary"])

    return {
        "overview": {
            "headline": {
                "country_count": country_count,
                "start_date": start_date,
                "end_date": end_date,
                "shock_count": shock_count,
            },
        },
        "gpr_timeline": {
            "series": _df_records(
                gpr_window[["date", "gpr", "gpr_change", "gpr_act", "gpr_threat", "event"]]
            ),
            "top_shocks": _df_records(
                top_shocks[["date", "gpr", "gpr_change", "gpr_act", "gpr_threat", "event"]]
            ),
        },
        "group_returns": _df_records(
            group_chart[["date", "market_group", "average_return", "cumulative_average_return"]]
        ),
        "evidence_map": _df_records(evidence_map),
    }


def _explanation_payloads(outputs: dict[str, pd.DataFrame]) -> dict[str, Any]:
    abnormal = outputs["abnormal_event_study"]
    raw = outputs["event_study"]
    event_study = (
        abnormal[["relative_day", "market_group", "cumulative_average_abnormal_return"]]
        .merge(
            raw[["relative_day", "market_group", "cumulative_average_return"]],
            on=["relative_day", "market_group"],
            how="outer",
        )
        .sort_values(["market_group", "relative_day"])
    )

    robustness = outputs["event_robustness"].copy()
    robustness["shock_quantile_label"] = robustness["shock_quantile"].map(lambda value: f"{value:.0%}")

    return {
        "event_study": _df_records(event_study),
        "event_robustness": _df_records(robustness),
        "regression": {
            "baseline": _df_records(select_key_regression_terms(outputs["regression"])),
            "controlled": _df_records(select_key_regression_terms(outputs["controlled_regression"])),
            "date_fe": _df_records(select_key_regression_terms(outputs["date_fe_regression"])),
        },
        "panel_sample_robustness": _df_records(outputs["panel_sample_robustness"]),
        "quantile_regression": _df_records(outputs["quantile_regression"]),
        "local_projections": _df_records(outputs["local_projections"]),
        "rolling_beta": _df_records(outputs["rolling_beta"][["date", "country", "market_group", "rolling_gpr_beta"]]),
    }


def _prediction_payloads(outputs: dict[str, pd.DataFrame]) -> dict[str, Any]:
    model_summary = build_model_summary(outputs["drawdown_metrics"], outputs["drawdown_lift"])
    best_labels = best_model_metric_labels(model_summary)
    mean_base_rate = float(outputs["drawdown_metrics"]["base_rate"].mean())

    return {
        "prediction_summary": {
            "model_comparison": _df_records(model_summary),
            "best_metrics": {
                key: {"label": label, "value": value}
                for key, (label, value) in best_labels.items()
            },
            "mean_event_rate": mean_base_rate,
        },
        "drawdown_calibration": _df_records(outputs["drawdown_calibration"]),
        "drawdown_lift": _df_records(outputs["drawdown_lift"]),
        "drawdown_threshold_metrics": _df_records(outputs["drawdown_threshold_metrics"]),
        "drawdown_country_risk_summary": _df_records(outputs["drawdown_country_risk_summary"]),
        "drawdown_feature_importance": _df_records(outputs["drawdown_importance"]),
        "drawdown_metrics": _df_records(outputs["drawdown_metrics"]),
    }


def _data_methods_payloads(outputs: dict[str, pd.DataFrame], panel: pd.DataFrame, root: Path) -> dict[str, Any]:
    coverage = build_country_coverage(panel)
    monthly_bundle = _load_monthly_bundle(root)

    monthly: dict[str, Any]
    if monthly_bundle is None:
        monthly = {"available": False}
    else:
        panel_month = monthly_bundle.panel.copy()
        panel_month["date_month"] = pd.to_datetime(panel_month["date_month"])
        month_level = panel_month.drop_duplicates("date_month").sort_values("date_month")
        provenance = monthly_provenance_rows(monthly_bundle)
        monthly = {
            "available": True,
            "mode": monthly_bundle.mode,
            "mode_label": monthly_bundle.mode_label,
            "start_month": month_level["date_month"].min().date().isoformat(),
            "end_month": month_level["date_month"].max().date().isoformat(),
            "source_count": len(monthly_bundle.source_names),
            "source_names": list(monthly_bundle.source_names),
            "provenance": _df_records(provenance),
            "month_level": _df_records(
                month_level[["date_month", "gpr_change_z", "spread_em_dev"]]
            ),
            "regressions": _df_records(monthly_bundle.regressions) if monthly_bundle.regressions is not None else None,
            "forecasts": _df_records(monthly_bundle.forecasts) if monthly_bundle.forecasts is not None else None,
        }

    return {
        "country_coverage": _df_records(coverage),
        "large_returns": _df_records(outputs["large_returns"][["date", "ticker", "country", "return", "abs_return"]]),
        "monthly": monthly,
    }


def _reader_summary_payloads(outputs: dict[str, pd.DataFrame]) -> dict[str, Any]:
    return {
        "reader_summaries": {
            "output_files": _output_file_rows(outputs),
            "market_reaction": _event_study_reader_rows(outputs["abnormal_event_study"]),
            "regression_translation": _regression_translation_rows(outputs),
        }
    }


def build_frontend_payloads(root: Path | None = None) -> dict[str, Any]:
    """Build every JSON payload the frontend needs, rooted at ``root``.

    When processed data is missing, returns a minimal payload with
    ``available=False`` plus the static copy so the frontend can render an
    empty state.
    """
    root = Path(root) if root is not None else PROJECT_ROOT
    payloads: dict[str, Any] = {"copy": _static_copy()}

    missing = _missing_spec_paths(root)
    if missing:
        payloads["manifest"] = {
            "available": False,
            "missing_files": missing,
            "build_date": pd.Timestamp.now("UTC").date().isoformat(),
        }
        return payloads

    outputs = {name: _read_output(spec, root) for name, spec in OUTPUT_SPECS.items()}
    panel = outputs["analysis_panel"]
    gpr = outputs["gpr"]

    payloads.update(_overview_payloads(outputs, panel, gpr))
    payloads.update(_explanation_payloads(outputs))
    payloads.update(_prediction_payloads(outputs))
    payloads.update(_data_methods_payloads(outputs, panel, root))
    payloads.update(_reader_summary_payloads(outputs))

    payloads["manifest"] = {
        "available": True,
        "build_date": pd.Timestamp.now("UTC").date().isoformat(),
        "start_date": panel["date"].min().date().isoformat(),
        "end_date": panel["date"].max().date().isoformat(),
        "country_count": int(panel["country"].nunique()),
        "shock_count": int(gpr["gpr_change_shock"].sum()),
        "monthly_mode": (
            payloads["monthly"]["mode"] if payloads["monthly"].get("available") else None
        ),
    }
    return payloads


def write_frontend_payloads(payloads: dict[str, Any], target_dir: Path) -> Path:
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        path = target_dir / f"{name}.json"
        path.write_text(
            json.dumps(payload, indent=2, default=_json_default), encoding="utf-8"
        )
    return target_dir


def export_frontend_data(root: Path | None = None, target_dir: Path | None = None) -> Path:
    root = Path(root) if root is not None else PROJECT_ROOT
    target = Path(target_dir) if target_dir is not None else root / "frontend" / "public" / "data"
    payloads = build_frontend_payloads(root)
    return write_frontend_payloads(payloads, target)


def _json_default(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")
