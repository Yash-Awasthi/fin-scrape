"""
Structured logging for FinScrape pipeline.
"""
import logging
import sys
from datetime import datetime, timezone


class FinScrapeFormatter(logging.Formatter):
    """Custom formatter with structured context."""

    def format(self, record):
        # Base format
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname

        # Extract context from record extras
        source = getattr(record, 'source', '')
        ticker = getattr(record, 'ticker', '')
        stage = getattr(record, 'stage', '')

        # Build context string
        ctx_parts = []
        if source:
            ctx_parts.append(f"src={source}")
        if ticker:
            ctx_parts.append(f"tick={ticker}")
        if stage:
            ctx_parts.append(f"stage={stage}")
        ctx = " | ".join(ctx_parts)

        if ctx:
            return f"{ts} | {level:8s} | {ctx} | {record.getMessage()}"
        else:
            return f"{ts} | {level:8s} | {record.getMessage()}"


def setup_logging(level: str = "INFO", log_file: str | None = None) -> None:
    """Configure logging for the pipeline."""
    root = logging.getLogger("finscrape")
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Console handler
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(FinScrapeFormatter())
    root.addHandler(console)

    # File handler (optional)
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(FinScrapeFormatter())
        root.addHandler(fh)

    # Suppress noisy third-party loggers
    for name in ("urllib3", "curl_cffi", "httpx", "yfinance"):
        logging.getLogger(name).setLevel(logging.WARNING)


class PipelineLogger:
    """Context-aware logger for pipeline stages."""

    def __init__(self, source: str = "", stage: str = ""):
        self._logger = logging.getLogger("finscrape.pipeline")
        self.source = source
        self.stage = stage

    def _extra(self, ticker: str = "") -> dict:
        return {"source": self.source, "stage": self.stage, "ticker": ticker}

    def info(self, msg: str, ticker: str = "", *args):
        self._logger.info(msg, *args, extra=self._extra(ticker))

    def warning(self, msg: str, ticker: str = "", *args):
        self._logger.warning(msg, *args, extra=self._extra(ticker))

    def error(self, msg: str, ticker: str = "", *args):
        self._logger.error(msg, *args, extra=self._extra(ticker))

    def debug(self, msg: str, ticker: str = "", *args):
        self._logger.debug(msg, *args, extra=self._extra(ticker))

    def with_source(self, source: str) -> PipelineLogger:
        return PipelineLogger(source=source, stage=self.stage)

    def with_stage(self, stage: str) -> PipelineLogger:
        return PipelineLogger(source=self.source, stage=stage)
