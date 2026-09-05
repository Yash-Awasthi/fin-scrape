import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


def write_source_manifest(
    path: Path,
    source_name: str,
    source_url: str,
    raw_file_path: str,
    license_or_terms_note: str,
    script_version: str,
    public_raw_file_path: str | None = None,
) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = source_manifest(
        source_name=source_name,
        source_url=source_url,
        raw_file_path=raw_file_path,
        license_or_terms_note=license_or_terms_note,
        script_version=script_version,
        public_raw_file_path=public_raw_file_path,
    )
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def write_source_collection_manifest(path: Path, sources: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "manifest_type": "source_collection",
        "download_timestamp_utc": datetime.now(UTC).isoformat(),
        "sources": sources,
    }
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def source_manifest(
    source_name: str,
    source_url: str,
    raw_file_path: str,
    license_or_terms_note: str,
    script_version: str,
    public_raw_file_path: str | None = None,
) -> dict:
    return {
        "source_name": source_name,
        "source_url": source_url,
        "download_timestamp_utc": datetime.now(UTC).isoformat(),
        "file_hash_sha256": _sha256_if_local(raw_file_path),
        "raw_file_path": public_raw_file_path or raw_file_path,
        "license_or_terms_note": license_or_terms_note,
        "script_version": script_version,
    }


def _sha256_if_local(path_or_url: str) -> str:
    if "://" in path_or_url:
        return ""
    path = Path(path_or_url)
    if not path.exists():
        return ""

    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
