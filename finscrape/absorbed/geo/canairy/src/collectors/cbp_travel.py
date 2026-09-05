"""
CBP Border Wait Times & Travel Collectors
Fetches border crossing wait times from CBP.
Free API: https://bwt.cbp.gov/
"""

import requests
from typing import Any, Dict, List
from datetime import datetime
import logging
from .base import BaseCollector

logger = logging.getLogger(__name__)


class CBPBorderWaitCollector(BaseCollector):
    """Collector for CBP border crossing wait times."""

    CBP_API_URL = "https://bwt.cbp.gov/api/bwtresults"

    def __init__(self, config=None):
        super().__init__(config or {})

    def collect(self) -> Dict[str, Any]:
        """Fetch average border wait times across major crossings."""
        try:
            response = requests.get(self.CBP_API_URL, timeout=15)

            if response.status_code == 200:
                data = response.json()

                wait_times = []
                critical_delays = []

                for port in data.get('results', []):
                    port_name = port.get('port_name', '')
                    crossing_name = port.get('crossing_name', '')

                    # Get passenger vehicle wait time
                    passenger_wait = port.get('passenger_vehicle_lanes', {})
                    wait_mins = passenger_wait.get('delay_minutes', 0)

                    if wait_mins:
                        wait_times.append(wait_mins)

                        # Track critical delays (>60 mins)
                        if wait_mins > 60:
                            critical_delays.append({
                                'port': port_name,
                                'crossing': crossing_name,
                                'wait_minutes': wait_mins
                            })

                avg_wait = sum(wait_times) / len(wait_times) if wait_times else 0

                return self._create_reading(
                    value=round(avg_wait, 1),
                    metadata={
                        'unit': 'minutes',
                        'ports_monitored': len(wait_times),
                        'critical_delays': critical_delays[:5],
                        'max_wait': max(wait_times) if wait_times else 0,
                        'source': 'CBP Border Wait Times',
                        'source_url': 'https://bwt.cbp.gov/'
                    }
                )

            return self._get_fallback()

        except Exception as e:
            logger.error(f"CBP border wait collection failed: {e}")
            return self._get_fallback()

    def _get_fallback(self) -> Dict[str, Any]:
        """Fallback border wait estimate."""
        return self._create_reading(
            value=25.0,
            metadata={'source': 'Estimated', 'unit': 'minutes'}
        )

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate border wait data."""
        value = data.get('value')
        return value is not None and 0 <= value <= 500


class TSAThroughputCollector(BaseCollector):
    """Collector for TSA checkpoint throughput data."""

    TSA_URL = "https://www.tsa.gov/travel/passenger-volumes"

    def __init__(self, config=None):
        super().__init__(config or {})

    def collect(self) -> Dict[str, Any]:
        """Fetch TSA throughput compared to baseline."""
        try:
            response = requests.get(self.TSA_URL, timeout=15)

            if response.status_code == 200:
                text = response.text

                # Parse for throughput numbers
                # TSA publishes daily numbers - look for recent figures
                import re

                # Look for numbers that look like passenger counts (millions)
                pattern = r'(\d{1,2}[,.]?\d{3}[,.]?\d{3})'
                matches = re.findall(pattern, text)

                if matches:
                    # Get the most recent figure
                    recent = matches[0].replace(',', '')
                    throughput = int(recent)

                    # Compare to 2019 baseline (~2.5M/day)
                    baseline = 2500000
                    pct_of_baseline = (throughput / baseline) * 100

                    return self._create_reading(
                        value=round(pct_of_baseline, 1),
                        metadata={
                            'unit': 'percent_of_2019',
                            'daily_throughput': throughput,
                            'source': 'TSA Passenger Volumes',
                            'source_url': self.TSA_URL
                        }
                    )

            return self._create_reading(value=95.0, metadata={'source': 'Estimated'})

        except Exception as e:
            logger.error(f"TSA throughput collection failed: {e}")
            return self._create_reading(value=95.0, metadata={'source': 'Error fallback'})

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate TSA data."""
        value = data.get('value')
        return value is not None and 0 <= value <= 150
