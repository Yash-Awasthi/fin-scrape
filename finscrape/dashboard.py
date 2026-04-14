"""
Dashboard integration — push pipeline events to the FinScrape web dashboard.

The dashboard runs as a Cloudflare Worker and accepts events via POST /api/events.
Configure via environment variables:
    FINSCRAPE_DASHBOARD_URL — Base URL of the dashboard (e.g., https://finscrape-dashboard.camelai.app)
    FINSCRAPE_API_KEY       — API key for authentication
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class DashboardClient:
    """Push events to the FinScrape web dashboard."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
    ):
        self.base_url = (base_url or os.getenv("FINSCRAPE_DASHBOARD_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("FINSCRAPE_API_KEY", "")
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def push_events(self, events: list[dict]) -> dict:
        """Push a list of event dicts to the dashboard.

        Returns the API response dict or an error dict.
        """
        if not self.is_configured:
            logger.debug("Dashboard not configured — skipping push")
            return {"skipped": True, "reason": "not configured"}

        if not events:
            return {"skipped": True, "reason": "no events"}

        try:
            resp = requests.post(
                f"{self.base_url}/api/events",
                json={"events": events},
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": self.api_key,
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            result = resp.json()
            logger.info("Pushed %d events to dashboard: %s", len(events), result)
            return result
        except requests.RequestException as e:
            logger.warning("Failed to push events to dashboard: %s", e)
            return {"error": str(e)}

    def get_stats(self) -> dict:
        """Fetch dashboard stats."""
        if not self.is_configured:
            return {"error": "not configured"}

        try:
            resp = requests.get(
                f"{self.base_url}/api/stats",
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {"error": str(e)}
