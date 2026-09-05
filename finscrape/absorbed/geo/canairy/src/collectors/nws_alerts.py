"""
NWS Weather Alerts collector — zero auth required.

Fetches active extreme/severe weather alerts from the National Weather Service.
Tracks the number of active extreme+severe alerts nationwide as a
security/infrastructure resilience signal.

Green: 0–2 extreme alerts
Amber: 3–8 extreme alerts
Red:   >8 extreme alerts (widespread severe weather)

API: https://api.weather.gov/alerts/active?severity=extreme,severe
Requires User-Agent header but no API key.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from .base import BaseCollector


class NWSAlertsCollector(BaseCollector):
    """Collects severe weather alert counts from NWS."""

    ALERTS_URL = "https://api.weather.gov/alerts/active"
    # NWS requires a valid contact email in User-Agent
    USER_AGENT = "Canairy/1.0 (canairy.app; contact@canairy.app)"

    def __init__(self, config):
        super().__init__(config)
        self._name = "NWSAlerts"
        self.logger = logging.getLogger(__name__)

    def collect(self) -> Dict[str, Any]:
        if not HAS_REQUESTS:
            return self._get_mock_data()

        try:
            data = self._fetch_alerts()
            if data is not None:
                return data
        except Exception as e:
            self.logger.error(f"Failed to collect NWS alerts: {e}")

        return self._get_mock_data()

    def _fetch_alerts(self) -> Optional[Dict[str, Any]]:
        """Fetch active extreme+severe weather alerts."""
        try:
            headers = {"User-Agent": self.USER_AGENT, "Accept": "application/geo+json"}
            # NWS API only accepts status param, we filter severity in code
            params = {"status": "actual"}

            response = requests.get(
                self.ALERTS_URL, params=params, headers=headers, timeout=15
            )
            if response.status_code != 200:
                self.logger.warning(f"NWS API returned {response.status_code}")
                return None

            data = response.json()
            features = data.get("features", [])

            # Count by severity
            extreme_count = sum(
                1
                for f in features
                if f.get("properties", {}).get("severity") == "Extreme"
            )
            severe_count = sum(
                1
                for f in features
                if f.get("properties", {}).get("severity") == "Severe"
            )
            total = extreme_count + severe_count

            # Get most impactful alert headline
            top_headline = ""
            if features:
                top_headline = features[0].get("properties", {}).get("headline", "")

            self.logger.info(
                f"NWS: {total} active alerts ({extreme_count} extreme, {severe_count} severe)"
            )

            return self._create_reading(
                value=total,
                metadata={
                    "unit": "alerts",
                    "source": "NWS",
                    "extreme_count": extreme_count,
                    "severe_count": severe_count,
                    "top_headline": top_headline[:200],
                    "threshold_amber": 3,
                    "threshold_red": 8,
                    "data_source": "LIVE",
                },
            )

        except Exception as e:
            self.logger.error(f"NWS API error: {e}")
            return None

    def _get_mock_data(self) -> Dict[str, Any]:
        return self._create_reading(
            value=1,
            metadata={
                "unit": "alerts",
                "source": "mock_data",
                "threshold_amber": 3,
                "threshold_red": 8,
                "note": "NWS API unavailable, using mock",
                "data_source": "MOCK",
            },
        )

    def validate_data(self, data: Dict[str, Any]) -> bool:
        if not data or "value" not in data:
            return False
        value = data["value"]
        return isinstance(value, (int, float)) and value >= 0
