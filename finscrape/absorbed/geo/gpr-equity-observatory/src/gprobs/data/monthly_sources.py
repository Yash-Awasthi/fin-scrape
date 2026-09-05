import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen

import pandas as pd
import yaml

from gprobs.data.datasets import MONTHLY_BENCHMARK_REAL, dataset_files
from gprobs.data.fama_french import load_fama_french_factor_returns
from gprobs.data.source_metadata import source_manifest, write_source_collection_manifest
from gprobs.features.monthly_panel import build_monthly_analysis_panel
from gprobs.project_paths import get_project_paths
from gprobs.validation.data_contracts import assert_no_duplicate_keys, ensure_columns, standardize_month_start

SCRIPT_VERSION = "real-monthly-v1"
MAX_URL_SOURCE_BYTES = 100 * 1024 * 1024
GPR_COLUMNS = ["gpr_global", "gprt_global", "gpra_global"]


def build_monthly_benchmark_real(config_path: Path, root: Path | None = None) -> None:
    paths = get_project_paths(root)
    paths.ensure_output_dirs()
    files = dataset_files(MONTHLY_BENCHMARK_REAL)
    config = load_monthly_source_config(config_path)
    period = config.get("sample_period", {})
    download_dir = paths.data_raw / "_downloads"
    source_download_date = datetime.now(UTC).date().isoformat()

    if config["gpr"].get("loader") != "caldara_iacoviello":
        raise ValueError("gpr.loader must be 'caldara_iacoviello'")

    gpr_source = resolve_monthly_source(
        config["gpr"]["path_or_url"],
        paths.root,
        expected_sha256=config["gpr"].get("sha256"),
        download_dir=download_dir,
    )
    gpr = _filter_period(load_caldara_iacoviello_gpr(gpr_source), period)
    gpr["source_download_date"] = source_download_date

    ff_config = config["fama_french"]
    developed_source = resolve_monthly_source(
        ff_config["developed_zip"],
        paths.root,
        expected_sha256=ff_config.get("developed_sha256"),
        download_dir=download_dir,
    )
    emerging_source = resolve_monthly_source(
        ff_config["emerging_zip"],
        paths.root,
        expected_sha256=ff_config.get("emerging_sha256"),
        download_dir=download_dir,
    )
    market_returns = _filter_period(
        pd.concat(
            [
                load_fama_french_factor_returns(developed_source, "developed", "developed"),
                load_fama_french_factor_returns(emerging_source, "emerging", "emerging"),
            ],
            ignore_index=True,
        ),
        period,
    )
    market_returns["source_download_date"] = source_download_date
    _validate_developed_emerging_coverage(market_returns)

    gpr, market_returns = _align_common_monthly_sample(gpr, market_returns)
    gdelt = _placeholder_gdelt(gpr["date_month"])
    macro = _placeholder_macro(gpr["date_month"])
    panel = build_monthly_analysis_panel(market_returns, gpr, gdelt, macro)

    _write_frame(paths.data_processed / files.gpr, gpr)
    _write_frame(paths.data_processed / files.market_returns, market_returns)
    _write_frame(paths.data_processed / files.gdelt, gdelt)
    _write_frame(paths.data_processed / files.macro, macro)
    panel_path = paths.data_processed / files.analysis_panel
    _write_frame(panel_path, panel)

    write_source_collection_manifest(
        paths.data_metadata / files.source_manifest,
        [
            _real_source_manifest(
                "Caldara-Iacoviello GPR",
                config["gpr"]["path_or_url"],
                gpr_source,
                "Public benchmark index. Do not redistribute raw source files.",
            ),
            _real_source_manifest(
                "Kenneth French Developed Factors",
                ff_config["developed_zip"],
                developed_source,
                "Kenneth French data library file. Do not redistribute raw source files.",
            ),
            _real_source_manifest(
                "Kenneth French Emerging Factors",
                ff_config["emerging_zip"],
                emerging_source,
                "Kenneth French data library file. Do not redistribute raw source files.",
            ),
        ],
    )
    _write_real_analysis_manifest(
        paths.data_metadata / files.analysis_manifest,
        panel,
        gpr_path=paths.data_processed / files.gpr,
        market_returns_path=paths.data_processed / files.market_returns,
        panel_path=panel_path,
    )


def load_monthly_source_config(config_path: Path) -> dict:
    with Path(config_path).open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    if not isinstance(config, dict):
        raise ValueError("source config must be a mapping")
    ensure_config_keys(config)
    return config


def ensure_config_keys(config: dict) -> None:
    for section in ["gpr", "fama_french"]:
        if section not in config or not isinstance(config[section], dict):
            raise ValueError(f"source config must include a {section} mapping")
    if "path_or_url" not in config["gpr"]:
        raise ValueError("source config gpr.path_or_url is required")
    for key in ["developed_zip", "emerging_zip"]:
        if key not in config["fama_french"]:
            raise ValueError(f"source config fama_french.{key} is required")


def load_caldara_iacoviello_gpr(path_or_url: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path_or_url).rename(
        columns={
            "month": "date_month",
            "GPR": "gpr_global",
            "GPRT": "gprt_global",
            "GPRA": "gpra_global",
        }
    )
    return _normalize_monthly_gpr(frame)


def resolve_monthly_source(
    path_or_url: str | Path,
    root: Path,
    *,
    expected_sha256: str | None = None,
    download_dir: Path | None = None,
) -> Path:
    value = str(path_or_url)
    if "://" in value:
        scheme = urlparse(value).scheme.lower()
        if scheme != "https":
            raise ValueError(f"unsupported source URL scheme: {scheme}")
        if not expected_sha256:
            raise ValueError("HTTPS real-data sources must include an expected SHA-256 hash")
        return _download_https_source(value, download_dir or root / "data" / "raw" / "_downloads", expected_sha256)

    path = Path(value)
    resolved = path if path.is_absolute() else root / path
    if not resolved.exists():
        raise FileNotFoundError(f"real monthly source file not found: {redact_source_reference(value)}")
    if expected_sha256 and _file_sha256(resolved).lower() != expected_sha256.lower():
        raise ValueError("real-data local source SHA-256 does not match the source config")
    return resolved


def redact_source_reference(value: str | Path) -> str:
    text = str(value)
    if "://" not in text:
        return f"local://{Path(text).name}"

    parsed = urlparse(text)
    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"
    return urlunparse((parsed.scheme, host, parsed.path, "", "", ""))


def _normalize_monthly_gpr(df: pd.DataFrame) -> pd.DataFrame:
    ensure_columns(df, ["date_month", *GPR_COLUMNS])
    result = df.copy()
    result["date_month"] = standardize_month_start(result["date_month"])
    for column in GPR_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="raise").astype(float)
    assert_no_duplicate_keys(result, ["date_month"])
    return result[["date_month", *GPR_COLUMNS]].sort_values("date_month").reset_index(drop=True)


def _filter_period(df: pd.DataFrame, period: dict) -> pd.DataFrame:
    result = df.copy()
    if period.get("start"):
        result = result[result["date_month"] >= pd.Timestamp(period["start"])]
    if period.get("end"):
        result = result[result["date_month"] <= pd.Timestamp(period["end"])]
    return result.reset_index(drop=True)


def _validate_developed_emerging_coverage(returns: pd.DataFrame) -> None:
    required_markets = ["developed", "emerging"]
    coverage = (
        returns.assign(_present=1)
        .pivot_table(index="date_month", columns="market_id", values="_present", aggfunc="max")
        .reindex(columns=required_markets)
    )
    incomplete_months = coverage.isna().any(axis=1)
    if coverage.empty or incomplete_months.any():
        missing_months = [
            pd.Timestamp(date_month).strftime("%Y-%m-%d") for date_month in coverage.index[incomplete_months]
        ]
        detail = f" Incomplete months: {', '.join(missing_months[:5])}." if missing_months else ""
        raise ValueError(
            "filtered real returns must contain both developed and emerging markets "
            f"for every retained month.{detail}"
        )


def _align_common_monthly_sample(gpr: pd.DataFrame, market_returns: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    common_months = sorted(set(pd.to_datetime(gpr["date_month"])) & set(pd.to_datetime(market_returns["date_month"])))
    if not common_months:
        raise ValueError("real monthly GPR and Fama-French returns have no common monthly sample")
    gpr_common = gpr[gpr["date_month"].isin(common_months)].reset_index(drop=True)
    returns_common = market_returns[market_returns["date_month"].isin(common_months)].reset_index(drop=True)
    _validate_developed_emerging_coverage(returns_common)
    return gpr_common, returns_common


def _placeholder_gdelt(months: pd.Series) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date_month": pd.to_datetime(months).sort_values().unique(),
            "risk_index_raw": 0.0,
            "risk_index_zscore": 0.0,
        }
    )


def _placeholder_macro(months: pd.Series) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date_month": pd.to_datetime(months).sort_values().unique(),
            "country_iso3": "GLB",
            "indicator_code": "placeholder_macro_zero",
            "value": 0.0,
            "frequency_original": "placeholder",
            "frequency_converted": "monthly",
            "source": "placeholder",
            "source_download_date": datetime.now(UTC).date().isoformat(),
        }
    )


def _real_source_manifest(
    source_name: str,
    source_reference: str | Path,
    resolved_source: Path,
    license_or_terms_note: str,
) -> dict:
    return source_manifest(
        source_name=source_name,
        source_url=redact_source_reference(source_reference),
        raw_file_path=str(resolved_source),
        public_raw_file_path=redact_source_reference(source_reference),
        license_or_terms_note=license_or_terms_note,
        script_version=SCRIPT_VERSION,
    )


def _write_real_analysis_manifest(
    path: Path,
    panel: pd.DataFrame,
    *,
    gpr_path: Path,
    market_returns_path: Path,
    panel_path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "dataset": MONTHLY_BENCHMARK_REAL,
        "dataset_mode": MONTHLY_BENCHMARK_REAL,
        "generated_timestamp_utc": datetime.now(UTC).isoformat(),
        "row_count": int(len(panel)),
        "sample_start": str(pd.to_datetime(panel["date_month"]).min().date()),
        "sample_end": str(pd.to_datetime(panel["date_month"]).max().date()),
        "markets": sorted(panel["market_id"].dropna().unique().tolist()),
        "used_placeholder_gdelt": True,
        "used_placeholder_macro": True,
        "aligned_to_common_gpr_returns_sample": True,
        "common_sample_start": str(pd.to_datetime(panel["date_month"]).min().date()),
        "common_sample_end": str(pd.to_datetime(panel["date_month"]).max().date()),
        "common_sample_n_months": int(pd.to_datetime(panel["date_month"]).nunique()),
        "processed_input_hashes": {
            "gpr": _file_sha256(gpr_path),
            "market_returns": _file_sha256(market_returns_path),
        },
        "analysis_panel_hash_sha256": _file_sha256(panel_path),
        "research_note": (
            "Real monthly benchmark uses user-supplied GPR and Fama-French sources. "
            "GDELT and macro columns are explicit placeholders until validated real inputs exist."
        ),
    }
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _write_frame(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _download_https_source(url: str, download_dir: Path, expected_sha256: str) -> Path:
    download_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    chunks = []
    total = 0
    with urlopen(Request(url, headers={"User-Agent": "gpr-equity-observatory"}), timeout=30) as response:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_URL_SOURCE_BYTES:
                raise ValueError("real-data URL source is too large")
            digest.update(chunk)
            chunks.append(chunk)

    actual_sha256 = digest.hexdigest()
    if actual_sha256.lower() != expected_sha256.lower():
        raise ValueError("real-data URL source SHA-256 does not match the source config")

    source_name = Path(urlparse(url).path).name or "source.bin"
    output_path = download_dir / f"{actual_sha256[:12]}_{source_name}"
    output_path.write_bytes(b"".join(chunks))
    return output_path


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
