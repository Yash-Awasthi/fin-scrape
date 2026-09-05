"""
CourtListener API collector for civil liberties litigation tracking.

Tracks major civil liberty cases in federal courts.
API: https://www.courtlistener.com/api/

Requires COURTLISTENER_API_KEY in environment.
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

from .base import BaseCollector


class CourtListenerLibertyCollector(BaseCollector):
    """Tracks civil liberties cases in federal courts."""

    BASE_URL = "https://www.courtlistener.com/api/rest/v3"

    # Keywords for civil liberty cases
    LIBERTY_KEYWORDS = [
        "first amendment", "fourth amendment", "civil rights",
        "habeas corpus", "due process", "equal protection",
        "voting rights", "free speech", "privacy", "surveillance"
    ]

    def __init__(self, config):
        super().__init__(config)
        self._name = "CourtListenerLiberty"
        self.api_key = os.getenv('COURTLISTENER_API_KEY', '')
        self.logger = logging.getLogger(__name__)

    def collect(self) -> Dict[str, Any]:
        if not self.api_key:
            self.logger.warning("COURTLISTENER_API_KEY not set")
            return self._get_mock_data()

        try:
            data = self._fetch_liberty_cases()
            if data:
                return data
        except Exception as e:
            self.logger.error(f"CourtListener collection failed: {e}")

        return self._get_mock_data()

    def _fetch_liberty_cases(self) -> Optional[Dict[str, Any]]:
        """Fetch civil liberty cases from CourtListener."""
        try:
            headers = {"Authorization": f"Token {self.api_key}"}

            # Search for recent opinions with civil liberty keywords
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

            total_cases = 0
            high_profile_cases = 0

            for keyword in ["civil rights", "first amendment", "fourth amendment", "due process"]:
                params = {
                    "q": keyword,
                    "filed_after": thirty_days_ago,
                    "order_by": "-dateFiled",
                    "court": "scotus ca1 ca2 ca3 ca4 ca5 ca6 ca7 ca8 ca9 ca10 ca11 cadc cafc",  # Federal appellate
                }

                response = requests.get(
                    f"{self.BASE_URL}/search/",
                    headers=headers,
                    params=params,
                    timeout=15
                )

                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    total_cases += len(results)

                    # Count high-profile cases (SCOTUS or circuit courts)
                    for case in results:
                        court = case.get("court", "").lower()
                        if "scotus" in court or "supreme" in court:
                            high_profile_cases += 2  # Weight SCOTUS higher
                        elif "ca" in court:  # Circuit courts
                            high_profile_cases += 1

                elif response.status_code == 401:
                    self.logger.error("CourtListener API key invalid")
                    return None

            # Deduplicate rough estimate
            active_cases = min(total_cases // 2, 50)

            self.logger.info(f"CourtListener: {active_cases} civil liberty cases active")

            return self._create_reading(
                value=active_cases,
                metadata={
                    "unit": "cases",
                    "source": "CourtListener",
                    "high_profile": high_profile_cases,
                    "threshold_amber": 5,
                    "threshold_red": 20,
                    "data_source": "LIVE",
                }
            )

        except Exception as e:
            self.logger.error(f"CourtListener API error: {e}")
            return None

    def _get_mock_data(self) -> Dict[str, Any]:
        return self._create_reading(
            value=8,
            metadata={
                "unit": "cases",
                "source": "mock_data",
                "threshold_amber": 5,
                "threshold_red": 20,
                "data_source": "MOCK",
            }
        )

    def validate_data(self, data: Dict[str, Any]) -> bool:
        if not data or "value" not in data:
            return False
        return isinstance(data["value"], (int, float)) and data["value"] >= 0
