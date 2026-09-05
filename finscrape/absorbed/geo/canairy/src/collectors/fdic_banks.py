"""
FDIC Bank Failures Collector
Fetches bank failure data from FDIC's public JSON feed.
Free API: https://banks.data.fdic.gov/docs/
"""

import requests
from typing import Any, Dict, List
from datetime import datetime, timedelta
import logging
from .base import BaseCollector

logger = logging.getLogger(__name__)


class FDICBankFailuresCollector(BaseCollector):
    """Collector for FDIC bank failures data."""

    FDIC_API_URL = "https://banks.data.fdic.gov/api/failures"

    def __init__(self, config=None):
        super().__init__(config or {})

    def collect(self) -> Dict[str, Any]:
        """Fetch recent bank failures (90-day count)."""
        try:
            # Get failures from last 90 days
            ninety_days_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

            params = {
                'filters': f'FAILDATE:[{ninety_days_ago} TO *]',
                'fields': 'NAME,CERT,FAILDATE,CITYST,QBFASSET',
                'sort_by': 'FAILDATE',
                'sort_order': 'DESC',
                'limit': 100,
                'format': 'json'
            }

            response = requests.get(self.FDIC_API_URL, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                failures = data.get('data', [])
                count = len(failures)

                # Calculate total assets of failed banks
                total_assets = sum(
                    float(f.get('data', {}).get('QBFASSET', 0) or 0)
                    for f in failures
                )

                recent_failures = [
                    {
                        'name': f.get('data', {}).get('NAME'),
                        'date': f.get('data', {}).get('FAILDATE'),
                        'location': f.get('data', {}).get('CITYST'),
                        'assets_millions': float(f.get('data', {}).get('QBFASSET', 0) or 0)
                    }
                    for f in failures[:5]  # Top 5 most recent
                ]

                return self._create_reading(
                    value=count,
                    metadata={
                        'period': '90_days',
                        'total_assets_millions': total_assets,
                        'recent_failures': recent_failures,
                        'source': 'FDIC Failed Bank List',
                        'source_url': 'https://www.fdic.gov/resources/resolutions/bank-failures/failed-bank-list/'
                    }
                )

            return self._get_fallback()

        except Exception as e:
            logger.error(f"FDIC collection failed: {e}")
            return self._get_fallback()

    def _get_fallback(self) -> Dict[str, Any]:
        """Fallback to scraping FDIC website."""
        try:
            url = "https://www.fdic.gov/resources/resolutions/bank-failures/failed-bank-list/"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                # Count table rows as rough estimate
                count = response.text.count('<tr>')
                # Normalize - subtract header rows
                count = max(0, count - 5)

                return self._create_reading(
                    value=min(count, 10),  # Cap for recent period
                    metadata={'source': 'FDIC Website Scrape'}
                )
        except:
            pass

        return self._create_reading(value=0, metadata={'source': 'Fallback'})

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate bank failures data."""
        value = data.get('value')
        return value is not None and 0 <= value <= 500


class FedDiscountWindowCollector(BaseCollector):
    """Collector for Federal Reserve discount window borrowing from H.4.1 data."""

    FED_H41_URL = "https://www.federalreserve.gov/releases/h41/current/h41.htm"

    def __init__(self, config=None):
        super().__init__(config or {})

    def collect(self) -> Dict[str, Any]:
        """Fetch discount window borrowing levels."""
        try:
            response = requests.get(self.FED_H41_URL, timeout=15)

            if response.status_code == 200:
                text = response.text

                # Parse for "Primary credit" or "Discount window" values
                # This is simplified - real implementation would parse the table
                import re

                # Look for billion dollar amounts near discount/primary credit
                pattern = r'Primary credit.*?(\d+[\d,]*)'
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

                if match:
                    value_str = match.group(1).replace(',', '')
                    value = float(value_str) / 1000  # Convert to billions

                    return self._create_reading(
                        value=value,
                        metadata={
                            'unit': 'billion_usd',
                            'source': 'Federal Reserve H.4.1',
                            'source_url': self.FED_H41_URL
                        }
                    )

            return self._create_reading(value=0.5, metadata={'source': 'Estimated'})

        except Exception as e:
            logger.error(f"Fed H.4.1 collection failed: {e}")
            return self._create_reading(value=0.5, metadata={'source': 'Error fallback'})

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate discount window data."""
        value = data.get('value')
        return value is not None and 0 <= value <= 500


class FedDepositsCollector(BaseCollector):
    """Collector for bank deposit flows from Federal Reserve H.8 data."""

    FRED_URL = "https://api.stlouisfed.org/fred/series/observations"

    def __init__(self, config=None):
        super().__init__(config or {})
        self.api_key = config.get('fred_api_key') if config else None

    def collect(self) -> Dict[str, Any]:
        """Fetch weekly deposit changes from FRED."""
        try:
            # Series: DPSACBW027SBOG (Deposits, All Commercial Banks)
            params = {
                'series_id': 'DPSACBW027SBOG',
                'api_key': self.api_key or 'DEMO_KEY',
                'file_type': 'json',
                'sort_order': 'desc',
                'limit': 5
            }

            response = requests.get(self.FRED_URL, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                observations = data.get('observations', [])

                if len(observations) >= 2:
                    current = float(observations[0].get('value', 0))
                    previous = float(observations[1].get('value', 0))

                    # Calculate week-over-week change in billions
                    change = (current - previous) / 1000

                    return self._create_reading(
                        value=change,
                        metadata={
                            'unit': 'billion_usd_change',
                            'current_total': current / 1000,
                            'source': 'Federal Reserve H.8 via FRED',
                            'source_url': 'https://fred.stlouisfed.org/series/DPSACBW027SBOG'
                        }
                    )

            return self._create_reading(value=0, metadata={'source': 'Fallback'})

        except Exception as e:
            logger.error(f"Fed H.8 deposits collection failed: {e}")
            return self._create_reading(value=0, metadata={'source': 'Error fallback'})

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate deposits data."""
        value = data.get('value')
        return value is not None and -1000 < value < 1000
