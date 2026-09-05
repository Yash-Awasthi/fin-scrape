"""
Supply Chain Collectors
Fetches port congestion, shipping delays, and freight index data.
"""

import requests
from typing import Any, Dict, List
from datetime import datetime
import logging
from .base import BaseCollector

logger = logging.getLogger(__name__)


class PortCongestionCollector(BaseCollector):
    """Collector for port congestion and vessel queue data."""

    # MarineTraffic has limited free data, we'll use news-based estimation
    PORTS_URL = "https://www.portoflosangeles.org/"

    def __init__(self, config=None):
        super().__init__(config or {})

    def collect(self) -> Dict[str, Any]:
        """Fetch port congestion metrics."""
        try:
            # Try to get data from Port of LA/Long Beach
            response = requests.get(self.PORTS_URL, timeout=15)

            if response.status_code == 200:
                text = response.text.lower()

                # Look for vessel counts or congestion indicators
                import re

                # Look for numbers near "vessels" or "ships"
                pattern = r'(\d+)\s*(?:vessels?|ships?|containers?)'
                matches = re.findall(pattern, text)

                if matches:
                    vessel_count = int(matches[0])

                    # Estimate congestion: >20 vessels waiting = amber, >40 = red
                    return self._create_reading(
                        value=vessel_count,
                        metadata={
                            'unit': 'vessels_waiting',
                            'port': 'LA/Long Beach',
                            'source': 'Port of Los Angeles',
                            'source_url': self.PORTS_URL
                        }
                    )

            return self._get_estimated_congestion()

        except Exception as e:
            logger.error(f"Port congestion collection failed: {e}")
            return self._get_estimated_congestion()

    def _get_estimated_congestion(self) -> Dict[str, Any]:
        """Fallback with estimated congestion level."""
        return self._create_reading(
            value=15,
            metadata={
                'source': 'Estimated',
                'unit': 'vessels_waiting',
                'note': 'Based on typical West Coast conditions'
            }
        )

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate port congestion data."""
        value = data.get('value')
        return value is not None and 0 <= value <= 200


class FreightIndexCollector(BaseCollector):
    """Collector for container freight rates (proxy via news/estimates)."""

    FREIGHTOS_URL = "https://fbx.freightos.com/"

    def __init__(self, config=None):
        super().__init__(config or {})

    def collect(self) -> Dict[str, Any]:
        """Fetch freight index data."""
        try:
            # Freightos Baltic Index - try to get current rate
            response = requests.get(self.FREIGHTOS_URL, timeout=15)

            if response.status_code == 200:
                text = response.text

                import re
                # Look for dollar amounts that look like container rates
                # Typical format: $X,XXX per FEU
                pattern = r'\$(\d{1,2}[,.]?\d{3})'
                matches = re.findall(pattern, text)

                if matches:
                    rate = int(matches[0].replace(',', '').replace('.', ''))

                    return self._create_reading(
                        value=rate,
                        metadata={
                            'unit': 'usd_per_feu',
                            'source': 'Freightos Baltic Index',
                            'source_url': self.FREIGHTOS_URL
                        }
                    )

            # Return estimated based on recent market conditions
            return self._create_reading(
                value=2500,
                metadata={
                    'source': 'Estimated',
                    'unit': 'usd_per_feu',
                    'note': 'Based on recent market rates'
                }
            )

        except Exception as e:
            logger.error(f"Freight index collection failed: {e}")
            return self._create_reading(value=2500, metadata={'source': 'Error fallback'})

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate freight index data."""
        value = data.get('value')
        return value is not None and 0 < value < 50000


class SemiconductorLeadTimeCollector(BaseCollector):
    """Collector for semiconductor lead time estimates."""

    def __init__(self, config=None):
        super().__init__(config or {})

    def collect(self) -> Dict[str, Any]:
        """Fetch semiconductor lead time data."""
        try:
            # Use news aggregation to estimate lead times
            # Susquehanna publishes monthly data, but behind paywall
            # We'll estimate based on industry reports

            # Try to scrape recent news for lead time mentions
            news_url = "https://www.reuters.com/technology/"
            response = requests.get(news_url, timeout=15)

            if response.status_code == 200:
                text = response.text.lower()

                import re
                # Look for "X weeks" near semiconductor/chip keywords
                if 'semiconductor' in text or 'chip' in text:
                    pattern = r'(\d+)\s*weeks?\s*(?:lead|delivery|wait)'
                    matches = re.findall(pattern, text)

                    if matches:
                        lead_time = int(matches[0])
                        return self._create_reading(
                            value=lead_time,
                            metadata={
                                'unit': 'weeks',
                                'source': 'News aggregation',
                                'note': 'Estimated from industry reports'
                            }
                        )

            # Return industry average estimate
            return self._create_reading(
                value=18,
                metadata={
                    'unit': 'weeks',
                    'source': 'Industry estimate',
                    'note': 'Average chip lead time ~18 weeks'
                }
            )

        except Exception as e:
            logger.error(f"Semiconductor lead time collection failed: {e}")
            return self._create_reading(value=18, metadata={'source': 'Error fallback'})

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate lead time data."""
        value = data.get('value')
        return value is not None and 0 < value < 100
