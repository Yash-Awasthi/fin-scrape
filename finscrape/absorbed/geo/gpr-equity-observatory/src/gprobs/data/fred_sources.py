import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd

from gprobs.config import (
    DEFAULT_DOWNLOAD_RETRIES,
    DEFAULT_DOWNLOAD_TIMEOUT_SECONDS,
    DEFAULT_RETRY_BACKOFF_SECONDS,
)
from gprobs.data.download_cache import download_url_to_cache, fetch_url_bytes
from gprobs.data.source_metadata import source_manifest, write_source_collection_manifest
from gprobs.project_paths import get_project_paths

FRED_API_KEY_ENV = "FRED_API_KEY"
FRED_OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"
FRED_PROCESSED_FILENAME = "fred_macro_controls.csv"
FRED_SOURCE_MANIFEST_FILENAME = "fred_source_manifest.json"
FRED_SCRIPT_VERSION = "fred_macro_controls_v1"


@dataclass(frozen=True)
class FredSeries:
    series_id: str
    column_name: str
    description: str


DEFAULT_FRED_SERIES = (
    FredSeries(
        series_id="BAA10Y",
        column_name="credit_spread_baa_10y",
        description="Moody's Seasoned Baa Corporate Bond Yield less 10-Year Treasury",
    ),
    FredSeries(
        series_id="DFF",
        column_name="policy_rate_effective_fed_funds",
        description="Effective Federal Funds Rate",
    ),
    FredSeries(
        series_id="T10YIE",
        column_name="inflation_expectation_10y_breakeven",
        description="10-Year Breakeven Inflation Rate",
    ),
)
FRED_RAW_COLUMNS = [series.column_name for series in DEFAULT_FRED_SERIES]
FRED_LAG_COLUMNS = [f"{column}_lag1d" for column in FRED_RAW_COLUMNS]
FRED_OUTPUT_COLUMNS = ["date", *FRED_RAW_COLUMNS, *FRED_LAG_COLUMNS]


def get_fred_api_key(env: dict[str, str] | None = None) -> str:
    api_key = (env or os.environ).get(FRED_API_KEY_ENV)
    if not api_key:
        raise RuntimeError("FRED_API_KEY must be set to download FRED macro controls.")
    return api_key


def build_fred_observations_url(
    series_id: str,
    *,
    api_key: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> str:
    params = {
        "series_id": series_id,
        "file_type": "json",
    }
    if start:
        params["observation_start"] = start
    if end:
        params["observation_end"] = end
    if api_key:
        params["api_key"] = api_key
    return f"{FRED_OBSERVATIONS_URL}?{urlencode(params)}"


def parse_fred_observations(payload: bytes | str | dict, series: FredSeries) -> pd.DataFrame:
    data = _json_payload(payload)
    observations = data.get("observations", [])
    frame = pd.DataFrame(observations)
    if frame.empty:
        return pd.DataFrame(columns=["date", series.column_name])
    if not {"date", "value"}.issubset(frame.columns):
        raise ValueError("FRED observations payload must include date and value fields.")

    parsed = frame[["date", "value"]].copy()
    parsed["date"] = pd.to_datetime(parsed["date"], errors="raise")
    parsed[series.column_name] = pd.to_numeric(
        parsed["value"].replace(".", pd.NA),
        errors="coerce",
    )
    parsed = parsed[["date", series.column_name]].sort_values("date").reset_index(drop=True)
    if parsed["date"].duplicated().any():
        duplicates = parsed.loc[parsed["date"].duplicated(), "date"].dt.strftime("%Y-%m-%d").head(5).tolist()
        raise ValueError(f"FRED series {series.series_id} has duplicate observation dates: {duplicates}")
    return parsed


def add_lagged_fred_features(controls: pd.DataFrame) -> pd.DataFrame:
    data = controls.sort_values("date").reset_index(drop=True).copy()
    present_raw_columns = [column for column in FRED_RAW_COLUMNS if column in data.columns]
    for column in present_raw_columns:
        data[f"{column}_lag1d"] = data[column].shift(1)

    output_columns = ["date", *present_raw_columns, *[f"{column}_lag1d" for column in present_raw_columns]]
    return data[output_columns]


def build_fred_controls_frame(series_frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not series_frames:
        return pd.DataFrame(columns=FRED_OUTPUT_COLUMNS)

    controls = series_frames[0]
    for frame in series_frames[1:]:
        controls = controls.merge(frame, on="date", how="outer")
    controls = add_lagged_fred_features(controls)
    for column in FRED_OUTPUT_COLUMNS:
        if column not in controls.columns:
            controls[column] = pd.NA
    return controls[FRED_OUTPUT_COLUMNS].sort_values("date").reset_index(drop=True)


def download_fred_series(
    series: FredSeries,
    raw_dir: Path,
    *,
    api_key: str,
    refresh: bool = False,
    start: str | None = None,
    end: str | None = None,
    timeout: int = DEFAULT_DOWNLOAD_TIMEOUT_SECONDS,
    retries: int = DEFAULT_DOWNLOAD_RETRIES,
    retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
    fetcher: Callable[[str, int], bytes] = fetch_url_bytes,
) -> Path:
    raw_path = raw_dir / f"{series.series_id}_observations.json"
    url = build_fred_observations_url(series.series_id, api_key=api_key, start=start, end=end)
    return download_url_to_cache(
        url,
        raw_path,
        refresh=refresh,
        timeout=timeout,
        retries=retries,
        retry_backoff_seconds=retry_backoff_seconds,
        fetcher=fetcher,
    )


def build_fred_macro_controls(
    root: Path | None = None,
    *,
    api_key: str | None = None,
    refresh: bool = False,
    start: str | None = None,
    end: str | None = None,
    series_list: tuple[FredSeries, ...] = DEFAULT_FRED_SERIES,
    fetcher: Callable[[str, int], bytes] = fetch_url_bytes,
    retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
) -> pd.DataFrame:
    paths = get_project_paths(root)
    raw_dir = paths.data_raw / "fred"
    raw_dir.mkdir(parents=True, exist_ok=True)
    paths.data_processed.mkdir(parents=True, exist_ok=True)
    paths.data_metadata.mkdir(parents=True, exist_ok=True)

    download_key = api_key or get_fred_api_key()
    series_frames = []
    sources = []
    for series in series_list:
        raw_path = download_fred_series(
            series,
            raw_dir,
            api_key=download_key,
            refresh=refresh,
            start=start,
            end=end,
            fetcher=fetcher,
            retry_backoff_seconds=retry_backoff_seconds,
        )
        series_frames.append(parse_fred_observations(raw_path.read_bytes(), series))
        sources.append(_fred_source_manifest(series, raw_path, start=start, end=end))

    controls = build_fred_controls_frame(series_frames)
    controls.to_csv(paths.data_processed / FRED_PROCESSED_FILENAME, index=False)
    write_source_collection_manifest(
        paths.data_metadata / FRED_SOURCE_MANIFEST_FILENAME,
        sources,
    )
    return controls


def _json_payload(payload: bytes | str | dict) -> dict:
    if isinstance(payload, bytes):
        return json.loads(payload.decode("utf-8"))
    if isinstance(payload, str):
        return json.loads(payload)
    return payload


def _fred_source_manifest(
    series: FredSeries,
    raw_path: Path,
    *,
    start: str | None = None,
    end: str | None = None,
) -> dict:
    public_raw_path = Path("data") / "raw" / "fred" / raw_path.name
    return source_manifest(
        source_name=f"FRED {series.series_id}",
        source_url=build_fred_observations_url(series.series_id, start=start, end=end),
        raw_file_path=str(raw_path),
        public_raw_file_path=public_raw_path.as_posix(),
        license_or_terms_note="Federal Reserve Economic Data API response. Do not commit API keys.",
        script_version=FRED_SCRIPT_VERSION,
    )
