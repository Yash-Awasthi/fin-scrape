import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from gprobs.data.datasets import MONTHLY_BENCHMARK_SAMPLE, dataset_files
from gprobs.data.source_metadata import source_manifest, write_source_collection_manifest
from gprobs.features.monthly_panel import build_monthly_analysis_panel
from gprobs.project_paths import get_project_paths

SAMPLE_SOURCE_DATE = "2026-06-15"


def build_monthly_benchmark_sample(root: Path | None = None) -> None:
    paths = get_project_paths(root)
    paths.ensure_output_dirs()
    files = dataset_files(MONTHLY_BENCHMARK_SAMPLE)

    sources = _sample_source_frames()
    for name, frame in sources.items():
        output_path = paths.data_processed / getattr(files, name)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(output_path, index=False)

    panel = build_monthly_analysis_panel(
        sources["market_returns"],
        sources["gpr"],
        sources["gdelt"],
        sources["macro"],
    )
    panel_path = paths.data_processed / files.analysis_panel
    panel_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(panel_path, index=False)

    _write_sample_manifests(
        paths.data_metadata / files.source_manifest,
        paths.data_metadata / files.analysis_manifest,
        panel,
    )


def _sample_source_frames() -> dict[str, pd.DataFrame]:
    dates = pd.date_range("2000-01-01", "2024-12-01", freq="MS")
    step = np.arange(len(dates))
    gpr = 100 + 18 * np.sin(step / 9) + np.where((step % 53) == 0, 35, 0)
    gprt = gpr * 0.62
    gpra = gpr * 0.38
    gpr_change = pd.Series(gpr).diff()
    gpr_change_z = ((gpr_change - gpr_change.mean()) / gpr_change.std(ddof=0)).to_numpy()
    predictive_gpr_shock = pd.Series(gpr_change_z).shift(1).fillna(0.0).to_numpy()

    gpr_monthly = pd.DataFrame(
        {
            "date_month": dates,
            "gpr_global": gpr.round(4),
            "gprt_global": gprt.round(4),
            "gpra_global": gpra.round(4),
            "source_download_date": SAMPLE_SOURCE_DATE,
        }
    )

    markets = []
    for market_id, market_class, sensitivity in [
        ("developed", "developed", -0.15),
        ("emerging", "emerging", -0.34),
    ]:
        cycle = 1.2 * np.sin(step / 6 + (0.4 if market_id == "emerging" else 0))
        returns = 0.55 + cycle + sensitivity * predictive_gpr_shock
        for date, value in zip(dates, returns, strict=True):
            markets.append(
                {
                    "date_month": date,
                    "market_id": market_id,
                    "market_class": market_class,
                    "return_usd": round(float(value), 4),
                    "risk_free_rate": 0.15,
                    "excess_return": round(float(value - 0.15), 4),
                    "source": "deterministic_sample",
                    "source_download_date": SAMPLE_SOURCE_DATE,
                }
            )
    market_returns = pd.DataFrame(markets)

    gpr_change_z_for_events = np.nan_to_num(gpr_change_z, nan=0.0)
    conflict_count = (10 + np.maximum(gpr_change_z_for_events, 0) * 6).round().astype(int)
    protest_count = (8 + np.maximum(np.sin(step / 5), 0) * 4).round().astype(int)
    sanction_count = (3 + (step % 17 == 0) * 2).astype(int)
    diplomatic_conflict_count = (5 + np.maximum(gpr_change_z_for_events, 0) * 3).round().astype(int)
    gdelt = pd.DataFrame(
        {
            "date_month": dates,
            "country_iso3": "GLB",
            "event_count": (80 + 15 * np.sin(step / 8)).round().astype(int),
            "conflict_count": conflict_count,
            "protest_count": protest_count,
            "sanction_count": sanction_count,
            "diplomatic_conflict_count": diplomatic_conflict_count,
            "avg_goldstein": (-1.5 - np.maximum(gpr_change_z_for_events, 0)).round(4),
            "avg_tone": (-2.0 - np.maximum(gpr_change_z_for_events, 0) * 0.8).round(4),
            "risk_index_raw": np.log1p(
                conflict_count + protest_count + sanction_count + diplomatic_conflict_count
            ).round(4),
            "filter_version": "sample-v1",
            "source_download_date": SAMPLE_SOURCE_DATE,
        }
    )
    gdelt["risk_index_zscore"] = (
        (gdelt["risk_index_raw"] - gdelt["risk_index_raw"].mean()) / gdelt["risk_index_raw"].std(ddof=0)
    ).round(4)

    macro = pd.DataFrame(
        {
            "date_month": dates,
            "country_iso3": "GLB",
            "indicator_code": "sample_global_cycle",
            "value": np.sin(step / 12).round(4),
            "frequency_original": "monthly",
            "frequency_converted": "monthly",
            "source": "deterministic_sample",
            "source_download_date": SAMPLE_SOURCE_DATE,
        }
    )

    return {
        "gpr": gpr_monthly,
        "market_returns": market_returns,
        "gdelt": gdelt,
        "macro": macro,
    }


def _write_sample_manifests(source_manifest_path: Path, analysis_manifest_path: Path, panel: pd.DataFrame) -> None:
    write_source_collection_manifest(
        source_manifest_path,
        sources=[
            source_manifest(
                source_name="Monthly benchmark deterministic sample",
                source_url="generated locally by scripts/build_monthly_benchmark_sample.py",
                raw_file_path="generated://monthly_benchmark_sample",
                license_or_terms_note="Synthetic sample data. Not empirical market data.",
                script_version="sample-v1",
            )
        ],
    )
    analysis_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "dataset_mode": MONTHLY_BENCHMARK_SAMPLE,
        "generated_timestamp_utc": datetime.now(UTC).isoformat(),
        "row_count": int(len(panel)),
        "start_date": str(pd.to_datetime(panel["date_month"]).min().date()),
        "end_date": str(pd.to_datetime(panel["date_month"]).max().date()),
        "markets": sorted(panel["market_id"].dropna().unique().tolist()),
        "sample_data_notice": "Deterministic sample data for software validation only.",
    }
    analysis_manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
