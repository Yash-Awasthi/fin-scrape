"""
OpenStates API collector for state-level legislation tracking.

Tracks AI surveillance bills advancing in state legislatures.
API: https://v3.openstates.org/

Requires OPENSTATES_API_KEY in environment.
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

from .base import BaseCollector


class OpenStatesAISurveillanceCollector(BaseCollector):
    """Tracks AI/surveillance-related bills in state legislatures."""

    BASE_URL = "https://v3.openstates.org/bills"

    # Keywords to identify AI surveillance bills
    SURVEILLANCE_KEYWORDS = [
        "artificial intelligence", "facial recognition", "biometric",
        "surveillance", "predictive policing", "automated decision",
        "algorithm accountability", "AI governance", "machine learning"
    ]

    def __init__(self, config):
        super().__init__(config)
        self._name = "OpenStatesAISurveillance"
        self.api_key = os.getenv('OPENSTATES_API_KEY', '')
        self.logger = logging.getLogger(__name__)

    def collect(self) -> Dict[str, Any]:
        if not self.api_key:
            self.logger.warning("OPENSTATES_API_KEY not set")
            return self._get_mock_data()

        try:
            data = self._fetch_surveillance_bills()
            if data:
                return data
        except Exception as e:
            self.logger.error(f"OpenStates collection failed: {e}")

        return self._get_mock_data()

    def _fetch_surveillance_bills(self) -> Optional[Dict[str, Any]]:
        """Fetch AI/surveillance bills from OpenStates."""
        try:
            headers = {"X-API-KEY": self.api_key}

            # Search for bills with surveillance-related keywords
            # Look at bills from current session
            total_bills = 0
            advancing_bills = 0

            for keyword in ["artificial intelligence", "facial recognition", "surveillance", "biometric"]:
                params = {
                    "q": keyword,
                    "sort": "updated_desc",
                    "per_page": 50,
                }

                response = requests.get(
                    self.BASE_URL,
                    headers=headers,
                    params=params,
                    timeout=15
                )

                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])

                    for bill in results:
                        # Check if bill is recent (last 30 days)
                        updated = bill.get("updated_at", "")
                        if updated:
                            try:
                                update_date = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                                if update_date > datetime.now(update_date.tzinfo) - timedelta(days=30):
                                    total_bills += 1

                                    # Check if bill is advancing (has recent action)
                                    latest_action = bill.get("latest_action_description", "").lower()
                                    if any(word in latest_action for word in ["passed", "approved", "adopted", "referred", "committee"]):
                                        advancing_bills += 1
                            except:
                                continue
                elif response.status_code == 401:
                    self.logger.error("OpenStates API key invalid")
                    return None

            self.logger.info(f"OpenStates: {advancing_bills} AI/surveillance bills advancing (of {total_bills} total)")

            return self._create_reading(
                value=advancing_bills,
                metadata={
                    "unit": "bills",
                    "source": "OpenStates",
                    "total_bills": total_bills,
                    "threshold_amber": 3,
                    "threshold_red": 10,
                    "data_source": "LIVE",
                }
            )

        except Exception as e:
            self.logger.error(f"OpenStates API error: {e}")
            return None

    def _get_mock_data(self) -> Dict[str, Any]:
        return self._create_reading(
            value=6,
            metadata={
                "unit": "bills",
                "source": "mock_data",
                "threshold_amber": 3,
                "threshold_red": 10,
                "data_source": "MOCK",
            }
        )

    def validate_data(self, data: Dict[str, Any]) -> bool:
        if not data or "value" not in data:
            return False
        return isinstance(data["value"], (int, float)) and data["value"] >= 0
