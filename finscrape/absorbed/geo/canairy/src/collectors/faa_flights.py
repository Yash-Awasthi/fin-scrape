"""
FAA Flight/Airspace Collectors
Fetches ground stops, delays, and TFR data from FAA.
Free data: https://www.fly.faa.gov/
"""

import requests
from typing import Any, Dict, List
from datetime import datetime
import logging
import xml.etree.ElementTree as ET
from .base import BaseCollector

logger = logging.getLogger(__name__)


class FAAGroundStopsCollector(BaseCollector):
    """Collector for FAA ground stops and ground delay programs."""

    FAA_STATUS_URL = "https://nasstatus.faa.gov/api/airport-status-information"
    FAA_XML_URL = "https://www.fly.faa.gov/flyfaa/xmlAirportStatus.jsp"

    def __init__(self, config=None):
        super().__init__(config or {})

    def collect(self) -> Dict[str, Any]:
        """Fetch current ground stops count."""
        try:
            # Try the JSON API first
            response = requests.get(
                self.FAA_STATUS_URL,
                timeout=15,
                headers={'Accept': 'application/json'}
            )

            if response.status_code == 200:
                data = response.json()
                ground_stops = []
                ground_delays = []

                # Parse airport advisories
                for airport in data.get('airports', []):
                    advisories = airport.get('advisories', [])
                    for adv in advisories:
                        adv_type = adv.get('type', '').lower()
                        if 'ground stop' in adv_type:
                            ground_stops.append({
                                'airport': airport.get('code'),
                                'reason': adv.get('reason'),
                                'end_time': adv.get('endTime')
                            })
                        elif 'ground delay' in adv_type:
                            ground_delays.append({
                                'airport': airport.get('code'),
                                'avg_delay': adv.get('avgDelay'),
                                'reason': adv.get('reason')
                            })

                return self._create_reading(
                    value=len(ground_stops),
                    metadata={
                        'ground_stops': ground_stops,
                        'ground_delays': len(ground_delays),
                        'source': 'FAA NAS Status',
                        'source_url': 'https://nasstatus.faa.gov/'
                    }
                )

            # Fallback to XML feed
            return self._get_xml_data()

        except Exception as e:
            logger.error(f"FAA ground stops collection failed: {e}")
            return self._get_xml_data()

    def _get_xml_data(self) -> Dict[str, Any]:
        """Fallback to XML airport status."""
        try:
            response = requests.get(self.FAA_XML_URL, timeout=10)
            if response.status_code == 200:
                root = ET.fromstring(response.content)

                ground_stops = 0
                for delay in root.findall('.//Delay'):
                    delay_type = delay.find('Type')
                    if delay_type is not None and 'Ground Stop' in delay_type.text:
                        ground_stops += 1

                return self._create_reading(
                    value=ground_stops,
                    metadata={'source': 'FAA XML Feed'}
                )
        except:
            pass

        return self._create_reading(value=0, metadata={'source': 'Fallback'})

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate ground stops data."""
        value = data.get('value')
        return value is not None and 0 <= value <= 100


class FAAFlightDelaysCollector(BaseCollector):
    """Collector for system-wide flight delay metrics."""

    BTS_API_URL = "https://www.transtats.bts.gov/ONTIME/Index.aspx"

    def __init__(self, config=None):
        super().__init__(config or {})

    def collect(self) -> Dict[str, Any]:
        """Fetch flight delay percentage."""
        try:
            # Use FAA airport status to estimate system delays
            response = requests.get(
                "https://nasstatus.faa.gov/api/airport-status-information",
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()

                delayed_airports = 0
                total_airports = 0

                for airport in data.get('airports', []):
                    total_airports += 1
                    if airport.get('advisories'):
                        delayed_airports += 1

                delay_pct = (delayed_airports / max(total_airports, 1)) * 100

                return self._create_reading(
                    value=round(delay_pct, 1),
                    metadata={
                        'delayed_airports': delayed_airports,
                        'total_monitored': total_airports,
                        'unit': 'percent',
                        'source': 'FAA NAS Status',
                        'source_url': 'https://nasstatus.faa.gov/'
                    }
                )

            return self._create_reading(value=5.0, metadata={'source': 'Estimated'})

        except Exception as e:
            logger.error(f"FAA delays collection failed: {e}")
            return self._create_reading(value=5.0, metadata={'source': 'Error fallback'})

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate delays data."""
        value = data.get('value')
        return value is not None and 0 <= value <= 100


class FAATFRCollector(BaseCollector):
    """Collector for Temporary Flight Restrictions (TFRs)."""

    TFR_URL = "https://tfr.faa.gov/tfr2/list.jsp"
    TFR_XML_URL = "https://tfr.faa.gov/tfr2/feed.xls"

    def __init__(self, config=None):
        super().__init__(config or {})

    def collect(self) -> Dict[str, Any]:
        """Fetch active TFR count."""
        try:
            response = requests.get(self.TFR_URL, timeout=15)

            if response.status_code == 200:
                text = response.text

                # Count TFR entries in the page
                # TFRs are listed in a table - count rows
                tfr_count = text.lower().count('notam')

                # Categorize by type (VIP, security, hazard, etc.)
                vip_tfrs = text.lower().count('vip') + text.lower().count('potus')
                security_tfrs = text.lower().count('security')
                hazard_tfrs = text.lower().count('hazard') + text.lower().count('fire')

                return self._create_reading(
                    value=max(tfr_count // 2, 1),  # Rough estimate
                    metadata={
                        'vip_tfrs': vip_tfrs,
                        'security_tfrs': security_tfrs,
                        'hazard_tfrs': hazard_tfrs,
                        'source': 'FAA TFR List',
                        'source_url': self.TFR_URL
                    }
                )

            return self._create_reading(value=10, metadata={'source': 'Estimated'})

        except Exception as e:
            logger.error(f"FAA TFR collection failed: {e}")
            return self._create_reading(value=10, metadata={'source': 'Error fallback'})

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate TFR data."""
        value = data.get('value')
        return value is not None and 0 <= value <= 500
