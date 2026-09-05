from dataclasses import dataclass
from pathlib import Path

DAILY_ETF = "daily_etf"
MONTHLY_BENCHMARK_SAMPLE = "monthly_benchmark_sample"
MONTHLY_BENCHMARK_REAL = "monthly_benchmark_real"


@dataclass(frozen=True)
class DatasetFiles:
    gpr: str
    market_returns: str
    gdelt: str
    macro: str
    analysis_panel: str
    source_manifest: str
    analysis_manifest: str


DAILY_ETF_FILES = DatasetFiles(
    gpr="gpr_daily.csv",
    market_returns="returns_panel.csv",
    gdelt="",
    macro="market_controls.csv",
    analysis_panel="analysis_panel.csv",
    source_manifest="daily_source_manifest.json",
    analysis_manifest="daily_analysis_panel_manifest.json",
)

MONTHLY_BENCHMARK_SAMPLE_FILES = DatasetFiles(
    gpr="monthly_benchmark/sample_gpr_monthly.csv",
    market_returns="monthly_benchmark/sample_market_returns_monthly.csv",
    gdelt="monthly_benchmark/sample_gdelt_country_monthly.csv",
    macro="monthly_benchmark/sample_macro_controls_monthly.csv",
    analysis_panel="monthly_benchmark/sample_analysis_panel.csv",
    source_manifest="monthly_benchmark/source_manifest.json",
    analysis_manifest="monthly_benchmark/analysis_panel_manifest.json",
)

MONTHLY_BENCHMARK_REAL_FILES = DatasetFiles(
    gpr="monthly_benchmark/gpr_monthly.csv",
    market_returns="monthly_benchmark/market_returns_monthly.csv",
    gdelt="monthly_benchmark/gdelt_country_monthly.csv",
    macro="monthly_benchmark/macro_controls_monthly.csv",
    analysis_panel="monthly_benchmark/analysis_panel.csv",
    source_manifest="monthly_benchmark/source_manifest_real.json",
    analysis_manifest="monthly_benchmark/analysis_panel_manifest_real.json",
)


def dataset_files(dataset: str) -> DatasetFiles:
    if dataset == DAILY_ETF:
        return DAILY_ETF_FILES
    if dataset == MONTHLY_BENCHMARK_SAMPLE:
        return MONTHLY_BENCHMARK_SAMPLE_FILES
    if dataset == MONTHLY_BENCHMARK_REAL:
        return MONTHLY_BENCHMARK_REAL_FILES
    raise ValueError(f"unknown dataset mode: {dataset}")


def dataset_output_filename(filename: str, dataset: str) -> str:
    if dataset == DAILY_ETF:
        return filename

    path = Path(filename)
    if dataset == MONTHLY_BENCHMARK_SAMPLE:
        return (Path("monthly_benchmark") / f"sample_{path.stem}{path.suffix}").as_posix()
    if dataset == MONTHLY_BENCHMARK_REAL:
        return (Path("monthly_benchmark") / f"{path.stem}_real{path.suffix}").as_posix()
    raise ValueError(f"unknown dataset mode: {dataset}")
