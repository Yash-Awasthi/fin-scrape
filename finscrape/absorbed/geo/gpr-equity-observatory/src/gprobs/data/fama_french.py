import zipfile
from io import BytesIO, StringIO
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import pandas as pd

from gprobs.validation.data_contracts import (
    assert_no_duplicate_keys,
    ensure_columns,
    standardize_month_start,
)

RETURN_COLUMNS = ["return_usd", "risk_free_rate", "excess_return"]
REQUIRED_COLUMNS = [
    "date_month",
    "market_id",
    "market_class",
    *RETURN_COLUMNS,
    "source",
    "source_download_date",
]
FAMA_FRENCH_MAX_ARCHIVE_BYTES = 10 * 1024 * 1024
FAMA_FRENCH_MAX_CSV_BYTES = 5 * 1024 * 1024


def load_fama_french_market_returns(source: str | Path) -> pd.DataFrame:
    return _normalize_market_returns(pd.read_csv(source))


def load_fama_french_factor_returns(
    source: str | Path,
    market_id: str,
    market_class: str,
    source_name: str = "kenneth_french",
) -> pd.DataFrame:
    text = _read_text_source(source)
    rows = _extract_fama_french_monthly_rows(text)
    frame = pd.DataFrame(rows, columns=["date_month", "excess_return", "risk_free_rate"])
    frame["market_id"] = market_id
    frame["market_class"] = market_class
    frame["return_usd"] = frame["excess_return"] + frame["risk_free_rate"]
    frame["source"] = source_name
    frame["source_download_date"] = ""
    return _normalize_market_returns(frame)


def _normalize_market_returns(df: pd.DataFrame) -> pd.DataFrame:
    ensure_columns(df, REQUIRED_COLUMNS)
    result = df.copy()
    result["date_month"] = standardize_month_start(result["date_month"])

    for column in RETURN_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="raise").astype(float)
        if (result[column] <= -99).any():
            raise ValueError(f"{column} contains Fama-French missing-value sentinel")

    expected_return = result["excess_return"] + result["risk_free_rate"]
    if not np.allclose(result["return_usd"], expected_return, atol=1e-8):
        raise ValueError("return_usd must equal excess_return + risk_free_rate")

    assert_no_duplicate_keys(result, ["date_month", "market_id"])
    return result[REQUIRED_COLUMNS].sort_values(["date_month", "market_id"]).reset_index(drop=True)


def _read_text_source(source: str | Path) -> str:
    source_text = str(source)
    if _is_zip_source(source_text):
        archive_bytes = _read_binary_source(source_text)
        with zipfile.ZipFile(BytesIO(archive_bytes)) as archive:
            csv_members = [
                info for info in archive.infolist() if not info.is_dir() and info.filename.lower().endswith(".csv")
            ]
            if not csv_members:
                raise ValueError("Fama-French zip file contains no CSV file")
            if len(csv_members) > 1:
                raise ValueError("Fama-French zip file must contain exactly one CSV member")
            csv_member = csv_members[0]
            if csv_member.file_size > FAMA_FRENCH_MAX_CSV_BYTES:
                raise ValueError("Fama-French CSV member is too large")
            return archive.read(csv_member).decode("utf-8-sig")

    with pd.io.common.get_handle(source_text, mode="r") as handle:
        return handle.handle.read()


def _is_zip_source(source: str) -> bool:
    parsed = urlparse(source)
    path = parsed.path if parsed.scheme else source
    return path.lower().endswith(".zip")


def _read_binary_source(source: str) -> bytes:
    chunks = []
    total = 0
    with pd.io.common.get_handle(source, mode="rb", is_text=False) as handle:
        while True:
            chunk = handle.handle.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > FAMA_FRENCH_MAX_ARCHIVE_BYTES:
                raise ValueError("Fama-French zip archive is too large")
            chunks.append(chunk)
    return b"".join(chunks)


def _extract_fama_french_monthly_rows(text: str) -> list[tuple[pd.Timestamp, float, float]]:
    lines = text.splitlines()
    header_index = next(
        (index for index, line in enumerate(lines) if "Mkt-RF" in line and "RF" in line.split(",")),
        None,
    )
    if header_index is None:
        raise ValueError("Fama-French file does not contain Mkt-RF and RF columns")

    table = pd.read_csv(StringIO("\n".join(lines[header_index:])))
    first_column = table.columns[0]
    rows = []
    for _, row in table.iterrows():
        raw_date = str(row[first_column]).strip()
        if not raw_date.isdigit() or len(raw_date) != 6:
            break
        excess_return = float(row["Mkt-RF"])
        risk_free_rate = float(row["RF"])
        if excess_return <= -99 or risk_free_rate <= -99:
            raise ValueError("Fama-French file contains missing-value sentinel")
        rows.append((pd.Timestamp(f"{raw_date[:4]}-{raw_date[4:]}-01"), excess_return, risk_free_rate))
    return rows
