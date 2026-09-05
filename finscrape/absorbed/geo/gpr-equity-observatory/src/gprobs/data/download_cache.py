from collections.abc import Callable
from pathlib import Path
from socket import timeout as SocketTimeout
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from gprobs.config import (
    DEFAULT_DOWNLOAD_RETRIES,
    DEFAULT_DOWNLOAD_TIMEOUT_SECONDS,
    DEFAULT_RETRY_BACKOFF_SECONDS,
)

TRANSIENT_DOWNLOAD_ERRORS = (
    TimeoutError,
    ConnectionError,
    SocketTimeout,
    URLError,
)


def retry(
    operation: Callable[[], object],
    *,
    retries: int = DEFAULT_DOWNLOAD_RETRIES,
    backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
):
    """Run an operation with simple linear-backoff retries."""
    if retries < 1:
        raise ValueError("retries must be at least 1.")

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return operation()
        except Exception as error:
            if not _is_retryable_error(error):
                raise
            last_error = error
            if attempt == retries:
                break
            sleep(backoff_seconds * attempt)

    raise RuntimeError(f"Download failed after {retries} attempts.") from last_error


def _is_retryable_error(error: Exception) -> bool:
    if isinstance(error, HTTPError):
        return error.code == 429 or 500 <= error.code < 600
    return isinstance(error, TRANSIENT_DOWNLOAD_ERRORS)


def fetch_url_bytes(url: str, timeout: int = DEFAULT_DOWNLOAD_TIMEOUT_SECONDS) -> bytes:
    """Fetch a URL with an explicit timeout."""
    request = Request(url, headers={"User-Agent": "gpr-equity-observatory/0.1"})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def download_url_to_cache(
    url: str,
    cache_path: str | Path,
    *,
    refresh: bool = False,
    timeout: int = DEFAULT_DOWNLOAD_TIMEOUT_SECONDS,
    retries: int = DEFAULT_DOWNLOAD_RETRIES,
    retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
    fetcher: Callable[[str, int], bytes] = fetch_url_bytes,
) -> Path:
    """Download a URL to a local raw-data cache path and reuse it by default."""
    cache_path = Path(cache_path)
    if cache_path.exists() and not refresh:
        return cache_path

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    payload = retry(
        lambda: fetcher(url, timeout),
        retries=retries,
        backoff_seconds=retry_backoff_seconds,
    )

    temporary_path = cache_path.with_suffix(f"{cache_path.suffix}.tmp")
    temporary_path.write_bytes(payload)
    temporary_path.replace(cache_path)
    return cache_path
