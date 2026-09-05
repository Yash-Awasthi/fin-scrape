import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st

from gprobs.dashboard.charts import (
    build_monthly_forecast_chart,
    build_monthly_gpr_shock_chart,
    build_monthly_spread_chart,
)
from gprobs.dashboard.components import (
    DASHBOARD_MODES,
    is_beginner_mode,
    render_beginner_intro,
    render_beginner_takeaways,
    render_csv_download,
    render_how_to_read,
    technical_details,
)
from gprobs.dashboard.contracts import PROJECT_ROOT, OutputSpec, validate_output_schema

MONTHLY_SAMPLE_NOTICE = "Sample mode is not empirical evidence. It only validates the monthly benchmark workflow."
MONTHLY_REAL_NOTICE = "Real monthly aggregate mode is a benchmark, not a country-panel proof."
MONTHLY_CLUSTER_NOTICE = "The two-market aggregate design cannot support country-clustered inference."
MONTHLY_MODE_PRIORITY_NOTICE = (
    "No mode selector is shown; if real monthly outputs are present, "
    "the dashboard shows real mode before sample mode."
)
MONTHLY_EMPTY_STATE_COMMANDS = [
    "python scripts/run_task.py monthly-sample --min-train-months 24",
    "python scripts/run_task.py monthly-real",
]
MONTHLY_EMPTY_STATE_NOTE = (
    "Real monthly mode requires config/sources.yml and local-only source files. "
    "The dashboard prefers real monthly outputs when both real and sample outputs are present."
)


@dataclass(frozen=True)
class MonthlyModeConfig:
    root: Path = PROJECT_ROOT
    mode_label: str = "Sample"
    dataset_mode: str = "monthly_benchmark_sample"
    panel: str = "data/processed/monthly_benchmark/sample_analysis_panel.csv"
    source_manifest: str = "data/metadata/monthly_benchmark/source_manifest.json"
    analysis_manifest: str = "data/metadata/monthly_benchmark/analysis_panel_manifest.json"
    regressions: str = "reports/tables/monthly_benchmark/sample_table_02_baseline_regressions.csv"
    forecasts: str = "reports/tables/monthly_benchmark/sample_table_03_forecast_comparison.csv"

    def path(self, relative_path: str) -> Path:
        return self.root / relative_path


@dataclass(frozen=True)
class MonthlyOutputBundle:
    mode: str
    mode_label: str
    panel: pd.DataFrame
    source_manifest: dict
    analysis_manifest: dict
    source_names: list[str]
    regressions: pd.DataFrame | None = None
    forecasts: pd.DataFrame | None = None


MONTHLY_MODES = {
    "real": MonthlyModeConfig(
        mode_label="Real",
        dataset_mode="monthly_benchmark_real",
        panel="data/processed/monthly_benchmark/analysis_panel.csv",
        source_manifest="data/metadata/monthly_benchmark/source_manifest_real.json",
        analysis_manifest="data/metadata/monthly_benchmark/analysis_panel_manifest_real.json",
        regressions="reports/tables/monthly_benchmark/table_02_baseline_regressions_real.csv",
        forecasts="reports/tables/monthly_benchmark/table_03_forecast_comparison_real.csv",
    ),
    "sample": MonthlyModeConfig(),
}

MONTHLY_OUTPUT_SPECS = {
    "monthly_panel": OutputSpec(
        Path("monthly_benchmark_analysis_panel.csv"),
        date_columns=("date_month",),
        required_columns=(
            "date_month",
            "market_id",
            "market_class",
            "excess_return",
            "ret_fwd_1m",
            "gpr_global",
            "gpr_change_z",
            "spread_em_dev",
            "gdelt_risk_raw",
            "gdelt_risk_z",
        ),
    ),
    "monthly_regressions": OutputSpec(
        Path("monthly_benchmark_regressions.csv"),
        required_columns=(
            "horizon",
            "term",
            "estimate",
            "std_error",
            "t_value",
            "p_value",
            "se_type",
            "nobs",
            "adjusted_r2",
        ),
    ),
    "monthly_forecasts": OutputSpec(
        Path("monthly_benchmark_forecasts.csv"),
        required_columns=(
            "model",
            "rmse",
            "mae",
            "oos_r2",
            "n_forecasts",
            "first_forecast_date",
            "last_forecast_date",
            "forecast_window_aligned",
        ),
    ),
}


def load_monthly_outputs() -> MonthlyOutputBundle | None:
    for mode, config in MONTHLY_MODES.items():
        bundle = _load_monthly_output_mode(mode, config)
        if bundle is not None:
            return bundle
    return None


def _load_monthly_output_mode(mode: str, config: MonthlyModeConfig) -> MonthlyOutputBundle | None:
    panel_path = config.path(config.panel)
    source_manifest_path = config.path(config.source_manifest)
    analysis_manifest_path = config.path(config.analysis_manifest)
    if not all(path.exists() for path in [panel_path, source_manifest_path, analysis_manifest_path]):
        return None

    panel = pd.read_csv(panel_path, parse_dates=["date_month"])
    validate_output_schema(panel, MONTHLY_OUTPUT_SPECS["monthly_panel"])
    source_manifest = _read_json(source_manifest_path)
    analysis_manifest = _read_json(analysis_manifest_path)
    source_names = [
        source.get("source_name", "Unknown source")
        for source in source_manifest.get("sources", [])
    ]

    regressions = _read_optional_monthly_csv(
        config.path(config.regressions),
        MONTHLY_OUTPUT_SPECS["monthly_regressions"],
    )
    forecasts = _read_optional_monthly_csv(
        config.path(config.forecasts),
        MONTHLY_OUTPUT_SPECS["monthly_forecasts"],
    )
    return MonthlyOutputBundle(
        mode=mode,
        mode_label=config.mode_label,
        panel=panel,
        source_manifest=source_manifest,
        analysis_manifest=analysis_manifest,
        source_names=source_names,
        regressions=regressions,
        forecasts=forecasts,
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_optional_monthly_csv(path: Path, spec: OutputSpec) -> pd.DataFrame | None:
    if not path.exists():
        return None
    output = pd.read_csv(path)
    validate_output_schema(output, spec)
    return output


def monthly_provenance_rows(bundle: MonthlyOutputBundle) -> pd.DataFrame:
    manifest = bundle.analysis_manifest
    rows = [
        ("mode", bundle.mode_label),
        ("dataset_mode", str(manifest.get("dataset_mode") or manifest.get("dataset") or "")),
        ("source_count", str(len(bundle.source_names))),
        ("row_count", str(manifest.get("row_count", ""))),
        ("sample_start", str(manifest.get("sample_start") or manifest.get("start_date") or "")),
        ("sample_end", str(manifest.get("sample_end") or manifest.get("end_date") or "")),
        ("used_placeholder_gdelt", str(manifest.get("used_placeholder_gdelt", ""))),
        ("used_placeholder_macro", str(manifest.get("used_placeholder_macro", ""))),
    ]
    return pd.DataFrame(rows, columns=["field", "value"])


def render_monthly_benchmark_tab(
    bundle: MonthlyOutputBundle | None,
    mode: str = DASHBOARD_MODES[1],
) -> None:
    if is_beginner_mode(mode):
        render_beginner_intro("monthly_benchmark")
    else:
        render_how_to_read("monthly_benchmark")
    if bundle is None:
        st.info("Monthly benchmark outputs are not available yet.")
        st.code("\n".join(MONTHLY_EMPTY_STATE_COMMANDS))
        if is_beginner_mode(mode):
            render_beginner_takeaways("monthly_benchmark")
        st.caption(MONTHLY_EMPTY_STATE_NOTE)
        st.caption(f"{MONTHLY_SAMPLE_NOTICE} {MONTHLY_REAL_NOTICE} {MONTHLY_CLUSTER_NOTICE}")
        return

    panel = bundle.panel.copy()
    panel["date_month"] = pd.to_datetime(panel["date_month"])
    month_level = panel.drop_duplicates("date_month").sort_values("date_month")
    start_date = panel["date_month"].min().date()
    end_date = panel["date_month"].max().date()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Mode", bundle.mode_label)
    col2.metric("Start month", str(start_date))
    col3.metric("End month", str(end_date))
    col4.metric("Sources", len(bundle.source_names))

    if bundle.mode == "sample":
        st.warning(MONTHLY_SAMPLE_NOTICE)
    else:
        st.info(MONTHLY_REAL_NOTICE)
    st.caption(MONTHLY_CLUSTER_NOTICE)
    st.caption(MONTHLY_MODE_PRIORITY_NOTICE)

    if not is_beginner_mode(mode):
        st.subheader("Source and Provenance Status")
        provenance = monthly_provenance_rows(bundle)
        st.dataframe(provenance, use_container_width=True, hide_index=True)
        render_csv_download(provenance, "Download Monthly Provenance CSV", "monthly_provenance.csv")
        if bundle.source_names:
            sources = pd.DataFrame({"source_name": bundle.source_names})
            st.dataframe(sources, use_container_width=True, hide_index=True)
            render_csv_download(sources, "Download Monthly Sources CSV", "monthly_sources.csv")

        st.plotly_chart(build_monthly_gpr_shock_chart(month_level), use_container_width=True)
        st.plotly_chart(build_monthly_spread_chart(month_level), use_container_width=True)

        st.subheader("Benchmark Regression Table")
        if bundle.regressions is None:
            st.info("Monthly benchmark regression output is not available yet.")
        else:
            st.dataframe(bundle.regressions, use_container_width=True, hide_index=True)
            render_csv_download(
                bundle.regressions,
                "Download Monthly Regressions CSV",
                "monthly_benchmark_regressions.csv",
            )

        st.subheader("Forecast Comparison")
        if bundle.forecasts is None:
            st.info("Monthly benchmark forecast output is not available yet.")
        else:
            st.plotly_chart(build_monthly_forecast_chart(bundle.forecasts), use_container_width=True)
            st.dataframe(bundle.forecasts, use_container_width=True, hide_index=True)
            render_csv_download(
                bundle.forecasts,
                "Download Monthly Forecasts CSV",
                "monthly_benchmark_forecasts.csv",
            )
        return

    st.plotly_chart(build_monthly_gpr_shock_chart(month_level), use_container_width=True)
    render_beginner_takeaways("monthly_benchmark")

    with technical_details("monthly provenance and benchmark outputs", mode):
        st.subheader("Source and Provenance Status")
        provenance = monthly_provenance_rows(bundle)
        st.dataframe(provenance, use_container_width=True, hide_index=True)
        render_csv_download(provenance, "Download Monthly Provenance CSV", "monthly_provenance.csv")
        if bundle.source_names:
            sources = pd.DataFrame({"source_name": bundle.source_names})
            st.dataframe(sources, use_container_width=True, hide_index=True)
            render_csv_download(sources, "Download Monthly Sources CSV", "monthly_sources.csv")

        st.plotly_chart(build_monthly_spread_chart(month_level), use_container_width=True)

        st.subheader("Benchmark Regression Table")
        if bundle.regressions is None:
            st.info("Monthly benchmark regression output is not available yet.")
        else:
            st.dataframe(bundle.regressions, use_container_width=True, hide_index=True)
            render_csv_download(
                bundle.regressions,
                "Download Monthly Regressions CSV",
                "monthly_benchmark_regressions.csv",
            )

        st.subheader("Forecast Comparison")
        if bundle.forecasts is None:
            st.info("Monthly benchmark forecast output is not available yet.")
        else:
            st.plotly_chart(build_monthly_forecast_chart(bundle.forecasts), use_container_width=True)
            st.dataframe(bundle.forecasts, use_container_width=True, hide_index=True)
            render_csv_download(
                bundle.forecasts,
                "Download Monthly Forecasts CSV",
                "monthly_benchmark_forecasts.csv",
            )
