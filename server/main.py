"""Uvicorn entrypoint: `python -m server.main` or `uvicorn server.main:app`."""

from __future__ import annotations

import uvicorn

from finscrape.logging_config import setup_logging
from server.app import create_app
from server.settings import get_settings

setup_logging(level=get_settings().log_level, json_format=get_settings().log_json)
app = create_app()


def main() -> None:
    s = get_settings()
    uvicorn.run("server.main:app", host=s.host, port=s.port, log_level="info")


if __name__ == "__main__":
    main()
