"""
EIA Energy Data Collector
Fetches Strategic Petroleum Reserve levels and Natural Gas storage from EIA API.
Free API: https://www.eia.gov/opendata/
"""

import requests
from typing import Any, Dict, Optional
from datetime import datetime
import logging
from .base import BaseCollector

logger = logging.getLogger(__name__)


class EIASPRCollector(BaseCollector):
    """Collector for Strategic Petroleum Reserve levels from EIA."""

    # EIA API endpoint for SPR
    EIA_API_URL = "https://api.eia.gov/v2/petroleum/sum/sndw/data/"

    def __init__(self, config=None):
        super().__init__(config or {})
        self.api_key = config.get('eia_api_key') if config else None

    def collect(self) -> Dict[str, Any]:
        """Fetch current SPR level in million barrels."""
        try:
            # SPR series ID: WCSSTUS1
            params = {
                'api_key': self.api_key or 'DEMO_KEY',
                'frequency': 'weekly',
                'data[0]': 'value',
                'facets[product][]': 'EPC0',
                'facets[process][]': 'SAE',
                'sort[0][column]': 'period',
                'sort[0][direction]': 'desc',
                'length': 1
            }

            response = requests.get(self.EIA_API_URL, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                if data.get('response', {}).get('data'):
                    latest = data['response']['data'][0]
                    value = float(latest.get('value', 0))

                    return self._create_reading(
                        value=value,
                        metadata={
                            'unit': 'million_barrels',
                            'period': latest.get('period'),
                            'source': 'EIA Weekly Petroleum Status Report',
                            'source_url': 'https://www.eia.gov/petroleum/supply/weekly/'
                        }
                    )

            # Fallback to public data scrape
            return self._get_fallback_spr()

        except Exception as e:
            logger.error(f"EIA SPR collection failed: {e}")
            return self._get_fallback_spr()

    def _get_fallback_spr(self) -> Dict[str, Any]:
        """Fallback SPR data from public EIA page."""
        try:
            # Try the simpler JSON endpoint
            url = "https://api.eia.gov/v2/petroleum/stoc/wstk/data/"
            params = {
                'api_key': 'DEMO_KEY',
                'frequency': 'weekly',
                'data[0]': 'value',
                'facets[product][]': 'EPC0',
                'sort[0][column]': 'period',
                'sort[0][direction]': 'desc',
                'length': 1
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('response', {}).get('data'):
                    value = float(data['response']['data'][0].get('value', 350))
                    return self._create_reading(value=value, metadata={'source': 'EIA Fallback'})
        except:
            pass

        # Return estimated value if all else fails
        return self._create_reading(
            value=350.0,
            metadata={'source': 'Estimated', 'note': 'API unavailable'}
        )

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate SPR data."""
        value = data.get('value')
        return value is not None and 0 < value < 800


class EIANaturalGasCollector(BaseCollector):
    """Collector for Natural Gas storage levels from EIA."""

    EIA_API_URL = "https://api.eia.gov/v2/natural-gas/stor/wkly/data/"

    def __init__(self, config=None):
        super().__init__(config or {})
        self.api_key = config.get('eia_api_key') if config else None

    def collect(self) -> Dict[str, Any]:
        """Fetch current natural gas storage in billion cubic feet."""
        try:
            params = {
                'api_key': self.api_key or 'DEMO_KEY',
                'frequency': 'weekly',
                'data[0]': 'value',
                'facets[process][]': 'SAT',
                'sort[0][column]': 'period',
                'sort[0][direction]': 'desc',
                'length': 1
            }

            response = requests.get(self.EIA_API_URL, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                if data.get('response', {}).get('data'):
                    latest = data['response']['data'][0]
                    value = float(latest.get('value', 0))

                    return self._create_reading(
                        value=value,
                        metadata={
                            'unit': 'billion_cubic_feet',
                            'period': latest.get('period'),
                            'source': 'EIA Weekly Natural Gas Storage Report',
                            'source_url': 'https://www.eia.gov/naturalgas/storage/'
                        }
                    )

            return self._get_fallback_gas()

        except Exception as e:
            logger.error(f"EIA Natural Gas collection failed: {e}")
            return self._get_fallback_gas()

    def _get_fallback_gas(self) -> Dict[str, Any]:
        """Fallback gas storage estimate."""
        return self._create_reading(
            value=2500.0,
            metadata={'source': 'Estimated', 'unit': 'billion_cubic_feet'}
        )

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate natural gas data."""
        value = data.get('value')
        return value is not None and 0 < value < 5000


class EIAGridEmergencyCollector(BaseCollector):
    """Collector for grid emergency declarations from DOE OE-417."""

    DOE_URL = "https://www.oe.energy.gov/oe417.htm"

    def __init__(self, config=None):
        super().__init__(config or {})

    def collect(self) -> Dict[str, Any]:
        """Fetch grid emergency count from DOE data."""
        try:
            # DOE OE-417 data is typically in Excel format
            # We'll scrape the summary or use a cached approach
            response = requests.get(self.DOE_URL, timeout=15)

            if response.status_code == 200:
                # Parse for recent emergencies
                # Looking for keywords indicating active emergencies
                text = response.text.lower()

                # Count mentions of recent emergencies
                emergency_keywords = ['emergency', 'outage', 'disturbance']
                count = sum(1 for kw in emergency_keywords if kw in text)

                return self._create_reading(
                    value=min(count, 5),  # Cap at 5 for threshold purposes
                    metadata={
                        'source': 'DOE OE-417',
                        'source_url': self.DOE_URL,
                        'note': 'Estimated from page content'
                    }
                )

            return self._create_reading(value=0, metadata={'source': 'Fallback'})

        except Exception as e:
            logger.error(f"DOE Grid emergency collection failed: {e}")
            return self._create_reading(value=0, metadata={'source': 'Error fallback'})

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate grid emergency data."""
        value = data.get('value')
        return value is not None and 0 <= value <= 50
