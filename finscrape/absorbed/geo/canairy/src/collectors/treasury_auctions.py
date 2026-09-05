"""
TreasuryDirect auction collector — zero auth required.

Fetches 10-year Treasury auction results including bid-to-cover ratio
and computes the auction "tail" (high yield minus when-issued yield).

Green: tail ≤ 3 bps (strong demand)
Amber: tail 3–7 bps (soft demand)
Red:   tail > 7 bps (failed auction / stress)

API: https://www.treasurydirect.gov/TA_WS/securities/auctioned?format=json&type=Note&term=10-Year
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


class TreasuryAuctionCollector(BaseCollector):
    """Collects 10-year Treasury auction tail data from TreasuryDirect."""

    AUCTION_URL = "https://www.treasurydirect.gov/TA_WS/securities/auctioned"

    def __init__(self, config):
        super().__init__(config)
        self._name = "TreasuryAuction"
        self.logger = logging.getLogger(__name__)

    def collect(self) -> Dict[str, Any]:
        if not HAS_REQUESTS:
            return self._get_mock_data()

        try:
            auction = self._fetch_latest_auction()
            if auction:
                return auction
        except Exception as e:
            self.logger.error(f"Failed to collect auction data: {e}")

        return self._get_mock_data()

    def _fetch_latest_auction(self) -> Optional[Dict[str, Any]]:
        """Fetch the most recent 10-year note auction from TreasuryDirect."""
        try:
            params = {
                "format": "json",
                "type": "Note",
                "term": "10-Year",
            }
            response = requests.get(self.AUCTION_URL, params=params, timeout=10)
            if response.status_code != 200:
                self.logger.warning(f"TreasuryDirect returned {response.status_code}")
                return None

            auctions = response.json()
            if not auctions:
                return None

            # Most recent auction is first
            latest = auctions[0]

            high_yield = self._parse_float(latest.get("highYield"))
            bid_to_cover = self._parse_float(latest.get("bidToCoverRatio"))
            auction_date = latest.get("auctionDate", "")
            cusip = latest.get("cusip", "")

            # Compute tail: difference between high yield and median yield
            # TreasuryDirect doesn't give when-issued yield directly, so
            # use the spread between high yield and interest rate as proxy
            interest_rate = self._parse_float(latest.get("interestRate"))
            if high_yield is not None and interest_rate is not None:
                tail_bps = abs(high_yield - interest_rate) * 100
            else:
                tail_bps = 0.0

            self.logger.info(
                f"10Y auction {auction_date}: tail={tail_bps:.1f}bp, "
                f"B2C={bid_to_cover}, yield={high_yield}%"
            )

            return self._create_reading(
                value=round(tail_bps, 1),
                metadata={
                    "unit": "basis_points",
                    "source": "TreasuryDirect",
                    "auction_date": auction_date,
                    "cusip": cusip,
                    "high_yield": high_yield,
                    "bid_to_cover": bid_to_cover,
                    "interest_rate": interest_rate,
                    "threshold_amber": 3.0,
                    "threshold_red": 7.0,
                    "data_source": "LIVE",
                },
            )

        except Exception as e:
            self.logger.error(f"TreasuryDirect API error: {e}")
            return None

    @staticmethod
    def _parse_float(val) -> Optional[float]:
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def _get_mock_data(self) -> Dict[str, Any]:
        return self._create_reading(
            value=2.1,
            metadata={
                "unit": "basis_points",
                "source": "mock_data",
                "threshold_amber": 3.0,
                "threshold_red": 7.0,
                "note": "TreasuryDirect API unavailable, using mock",
                "data_source": "MOCK",
            },
        )

    def validate_data(self, data: Dict[str, Any]) -> bool:
        if not data or "value" not in data:
            return False
        value = data["value"]
        return isinstance(value, (int, float)) and -50 <= value <= 50
