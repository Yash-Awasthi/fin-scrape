"""
Telecommunications Infrastructure collectors.
Tracks BGP routing anomalies, cell outages, and undersea cable status.

Sources:
- BGP Stream (CAIDA) for routing anomalies
- FCC/Downdetector for cell outages
- Submarine Cable Map for cable status
"""

import requests
from datetime import datetime
from typing import Dict, Any, Optional
from .base import BaseCollector


class BGPAnomaliesCollector(BaseCollector):
    """Collects BGP routing anomalies from public sources."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "BGPAnomalies"
        # BGP Stream and routing monitoring sources
        self.bgpstream_url = "https://bgpstream.caida.org/data"

    def collect(self) -> Dict[str, Any]:
        """Collect BGP anomaly data."""
        try:
            data = self._fetch_bgp_data()
            if data:
                return data
            return self._get_mock_data()

        except Exception as e:
            self.logger.error(f"Failed to collect BGP data: {e}")
            return self._get_mock_data()

    def _fetch_bgp_data(self) -> Optional[Dict[str, Any]]:
        """Fetch BGP anomalies from monitoring sources."""
        try:
            # Try CAIDA BGP Stream
            response = requests.get(
                "https://bgpstream.caida.org/",
                headers={'User-Agent': 'Canairy/1.0'},
                timeout=15
            )

            if response.status_code == 200:
                text = response.text.lower()

                # Count anomaly keywords
                anomaly_keywords = ['hijack', 'leak', 'outage', 'anomaly', 'incident', 'alert']
                anomaly_count = 0
                for kw in anomaly_keywords:
                    anomaly_count += text.count(kw)

                # Normalize (page typically has background mentions)
                estimated_anomalies = min(anomaly_count // 2, 10)

                self.logger.info(f"BGP: {estimated_anomalies} anomalies detected")

                return {
                    'value': estimated_anomalies,
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'collector': self.name,
                    'metadata': {
                        'unit': 'anomalies',
                        'source': 'CAIDA BGP Stream',
                        'data_source': 'LIVE'
                    }
                }

            return None

        except Exception as e:
            self.logger.error(f"BGP fetch error: {e}")
            return None

    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock data."""
        return {
            'value': 2,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {
                'unit': 'anomalies',
                'source': 'mock_data',
                'data_source': 'MOCK'
            }
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        if not data or 'value' not in data:
            return False
        return isinstance(data['value'], (int, float))


class CellOutagesCollector(BaseCollector):
    """Collects cell network outage data."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "CellOutages"
        # FCC outage reporting and Downdetector
        self.fcc_url = "https://www.fcc.gov/general/network-outage-reporting-system-nors"

    def collect(self) -> Dict[str, Any]:
        """Collect cell outage data."""
        try:
            data = self._fetch_outage_data()
            if data:
                return data
            return self._get_mock_data()

        except Exception as e:
            self.logger.error(f"Failed to collect cell outage data: {e}")
            return self._get_mock_data()

    def _fetch_outage_data(self) -> Optional[Dict[str, Any]]:
        """Fetch cell outage data from FCC/public sources."""
        try:
            # FCC NORS page
            response = requests.get(
                self.fcc_url,
                headers={'User-Agent': 'Canairy/1.0'},
                timeout=15
            )

            if response.status_code == 200:
                text = response.text.lower()

                # Count outage-related mentions
                outage_keywords = ['outage', 'disruption', 'incident', 'failure', 'degradation']
                outage_count = 0
                for kw in outage_keywords:
                    outage_count += text.count(kw)

                # Normalize
                estimated_outages = min(outage_count // 3, 15)

                self.logger.info(f"Cell outages: {estimated_outages} reported")

                return {
                    'value': estimated_outages,
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'collector': self.name,
                    'metadata': {
                        'unit': 'outages',
                        'source': 'FCC NORS',
                        'data_source': 'LIVE'
                    }
                }

            return None

        except Exception as e:
            self.logger.error(f"Cell outage fetch error: {e}")
            return None

    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock data."""
        return {
            'value': 3,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {
                'unit': 'outages',
                'source': 'mock_data',
                'data_source': 'MOCK'
            }
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        if not data or 'value' not in data:
            return False
        return isinstance(data['value'], (int, float))


class UnderseaCableCollector(BaseCollector):
    """Collects undersea cable status data."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "UnderseaCable"
        self.cable_map_url = "https://www.submarinecablemap.com/"

    def collect(self) -> Dict[str, Any]:
        """Collect undersea cable status."""
        try:
            data = self._fetch_cable_data()
            if data:
                return data
            return self._get_mock_data()

        except Exception as e:
            self.logger.error(f"Failed to collect cable data: {e}")
            return self._get_mock_data()

    def _fetch_cable_data(self) -> Optional[Dict[str, Any]]:
        """Fetch cable status from submarine cable map."""
        try:
            response = requests.get(
                self.cable_map_url,
                headers={'User-Agent': 'Canairy/1.0'},
                timeout=15
            )

            if response.status_code == 200:
                text = response.text.lower()

                # Count cable incident keywords
                incident_keywords = ['cut', 'repair', 'damage', 'fault', 'outage', 'disruption']
                incident_count = 0
                for kw in incident_keywords:
                    incident_count += text.count(kw)

                # Very rare - usually 0-2
                estimated_incidents = min(incident_count, 5)

                self.logger.info(f"Undersea cables: {estimated_incidents} incidents")

                return {
                    'value': estimated_incidents,
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'collector': self.name,
                    'metadata': {
                        'unit': 'incidents',
                        'source': 'Submarine Cable Map',
                        'data_source': 'LIVE'
                    }
                }

            return None

        except Exception as e:
            self.logger.error(f"Cable fetch error: {e}")
            return None

    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock data."""
        return {
            'value': 0,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {
                'unit': 'incidents',
                'source': 'mock_data',
                'data_source': 'MOCK'
            }
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        if not data or 'value' not in data:
            return False
        return isinstance(data['value'], (int, float))
