"""
Freddie Mac Primary Mortgage Market Survey (PMMS) collector.

Tracks 30-year fixed mortgage rates.
Data published weekly on Thursdays.

Source: https://www.freddiemac.com/pmms
"""

import requests
from datetime import datetime
from typing import Dict, Any, Optional
import logging
import re

from .base import BaseCollector


class FreddieMacPMMSCollector(BaseCollector):
    """Collects 30-year fixed mortgage rates from Freddie Mac PMMS."""

    # Freddie Mac PMMS page
    PMMS_URL = "https://www.freddiemac.com/pmms"

    def __init__(self, config):
        super().__init__(config)
        self._name = "FreddieMacPMMS"
        self.logger = logging.getLogger(__name__)

    def collect(self) -> Dict[str, Any]:
        try:
            data = self._fetch_rates()
            if data:
                return data
        except Exception as e:
            self.logger.error(f"Freddie Mac collection failed: {e}")

        return self._get_mock_data()

    def _fetch_rates(self) -> Optional[Dict[str, Any]]:
        """Fetch current mortgage rates from Freddie Mac."""
        try:
            response = requests.get(
                self.PMMS_URL,
                headers={"User-Agent": "Canairy/1.0"},
                timeout=15
            )

            if response.status_code != 200:
                self.logger.warning(f"Freddie Mac returned {response.status_code}")
                return None

            text = response.text

            # Look for 30-year rate pattern
            # The page typically shows something like "6.89%" for 30-year
            patterns = [
                r'30[- ]?[Yy]ear[^0-9]*(\d+\.?\d*)\s*%',
                r'(\d+\.\d+)%[^0-9]*30[- ]?[Yy]ear',
                r'class="[^"]*rate[^"]*"[^>]*>(\d+\.\d+)%',
                r'>(\d\.\d{2})%<',  # Simple rate in HTML
            ]

            rate_30yr = None
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    try:
                        rate = float(match.group(1))
                        if 2.0 <= rate <= 15.0:  # Reasonable mortgage rate range
                            rate_30yr = rate
                            break
                    except:
                        continue

            # Alternative: Try the FRED API for MORTGAGE30US
            if not rate_30yr:
                rate_30yr = self._fetch_from_fred()

            if rate_30yr:
                self.logger.info(f"Freddie Mac PMMS: 30yr rate = {rate_30yr}%")

                return self._create_reading(
                    value=rate_30yr,
                    metadata={
                        "unit": "percent",
                        "source": "Freddie Mac PMMS",
                        "rate_type": "30-year fixed",
                        "threshold_amber": 6.5,
                        "threshold_red": 7.5,
                        "data_source": "LIVE",
                    }
                )

            return None

        except Exception as e:
            self.logger.error(f"Freddie Mac scrape error: {e}")
            return None

    def _fetch_from_fred(self) -> Optional[float]:
        """Fallback: fetch from FRED API."""
        try:
            import os
            api_key = os.getenv("FRED_API_KEY")
            if not api_key:
                return None

            response = requests.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params={
                    "series_id": "MORTGAGE30US",
                    "api_key": api_key,
                    "file_type": "json",
                    "sort_order": "desc",
                    "limit": 1,
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                obs = data.get("observations", [])
                if obs:
                    return float(obs[0]["value"])

        except:
            pass

        return None

    def _get_mock_data(self) -> Dict[str, Any]:
        return self._create_reading(
            value=7.1,
            metadata={
                "unit": "percent",
                "source": "mock_data",
                "rate_type": "30-year fixed",
                "threshold_amber": 6.5,
                "threshold_red": 7.5,
                "data_source": "MOCK",
            }
        )

    def validate_data(self, data: Dict[str, Any]) -> bool:
        if not data or "value" not in data:
            return False
        val = data["value"]
        return isinstance(val, (int, float)) and 0 < val < 20
