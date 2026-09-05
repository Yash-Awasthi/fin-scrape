"""
Water Infrastructure collectors.
Tracks reservoir levels, EPA water alerts, and drought conditions.

Sources:
- USBR (Bureau of Reclamation) reservoir data
- EPA SDWIS drinking water alerts
- USDA/UNL Drought Monitor
"""

import requests
import os
from datetime import datetime
from typing import Dict, Any, Optional
from .base import BaseCollector


class ReservoirLevelCollector(BaseCollector):
    """Collects major reservoir level data from Bureau of Reclamation."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "ReservoirLevel"
        # USBR Water Operations data
        self.base_url = "https://www.usbr.gov/uc/water/hydrodata/reservoir_data"

    def collect(self) -> Dict[str, Any]:
        """Collect reservoir level data."""
        try:
            data = self._fetch_reservoir_data()
            if data:
                return data
            return self._get_mock_data()

        except Exception as e:
            self.logger.error(f"Failed to collect reservoir data: {e}")
            return self._get_mock_data()

    def _fetch_reservoir_data(self) -> Optional[Dict[str, Any]]:
        """Fetch reservoir data from California DWR (major western reservoirs)."""
        try:
            import re

            # California DWR - Shasta, Oroville, Folsom (major reservoirs)
            reservoirs = ['SHA', 'ORO', 'FOL']  # Station codes
            capacities = []

            for station in reservoirs:
                try:
                    response = requests.get(
                        f"https://cdec.water.ca.gov/dynamicapp/QueryDaily?s={station}&d=2026-03-01&span=7",
                        headers={'User-Agent': 'Canairy/1.0'},
                        timeout=10
                    )

                    if response.status_code == 200:
                        text = response.text
                        # Look for storage percentage in the HTML table
                        pct_match = re.search(r'(\d+)\s*%', text)
                        if pct_match:
                            pct = float(pct_match.group(1))
                            if 0 < pct <= 150:  # Reasonable range
                                capacities.append(pct)
                except:
                    continue

            if capacities:
                avg_pct = sum(capacities) / len(capacities)
                self.logger.info(f"Reservoir levels: {avg_pct:.0f}% avg ({len(capacities)} reservoirs)")

                return {
                    'value': round(avg_pct, 1),
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'collector': self.name,
                    'metadata': {
                        'unit': 'percent_capacity',
                        'reservoirs_sampled': len(capacities),
                        'source': 'California DWR',
                        'data_source': 'LIVE'
                    }
                }

            return None

        except Exception as e:
            self.logger.error(f"Reservoir fetch error: {e}")
            return None

    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock data."""
        return {
            'value': 72.0,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {
                'unit': 'percent_capacity',
                'source': 'mock_data',
                'data_source': 'MOCK'
            }
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        if not data or 'value' not in data:
            return False
        return isinstance(data['value'], (int, float))


class EPAWaterAlertsCollector(BaseCollector):
    """Collects drinking water alerts from EPA SDWIS."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "EPAWaterAlerts"
        self.api_key = os.getenv('DATA_GOV_API_KEY', '')
        # EPA ECHO/SDWIS API
        self.base_url = "https://enviro.epa.gov/enviro/efservice"

    def collect(self) -> Dict[str, Any]:
        """Collect water quality alerts."""
        try:
            data = self._fetch_water_alerts()
            if data:
                return data
            return self._get_mock_data()

        except Exception as e:
            self.logger.error(f"Failed to collect EPA water data: {e}")
            return self._get_mock_data()

    def _fetch_water_alerts(self) -> Optional[Dict[str, Any]]:
        """Fetch water alerts from EPA."""
        try:
            # EPA Envirofacts SDWIS violations endpoint
            # Query recent violations
            response = requests.get(
                f"{self.base_url}/SDWIS_VIOLATION/VIOLATION_CATEGORY/HL/JSON",
                headers={
                    'User-Agent': 'Canairy/1.0',
                    'X-Api-Key': self.api_key
                } if self.api_key else {'User-Agent': 'Canairy/1.0'},
                timeout=15
            )

            if response.status_code == 200:
                try:
                    violations = response.json()
                    if isinstance(violations, list):
                        # Count recent health-related violations
                        alert_count = len(violations[:100])  # Cap at 100

                        self.logger.info(f"EPA Water: {alert_count} health violations")

                        return {
                            'value': alert_count,
                            'timestamp': datetime.utcnow().isoformat() + 'Z',
                            'collector': self.name,
                            'metadata': {
                                'unit': 'violations',
                                'category': 'Health-based',
                                'source': 'EPA SDWIS',
                                'data_source': 'LIVE'
                            }
                        }
                except:
                    pass

            # Alternative: check EPA water quality news
            news_response = requests.get(
                "https://www.epa.gov/ground-water-and-drinking-water",
                headers={'User-Agent': 'Canairy/1.0'},
                timeout=15
            )

            if news_response.status_code == 200:
                text = news_response.text.lower()
                alert_keywords = ['boil water', 'advisory', 'contamination', 'violation', 'emergency']
                count = sum(1 for kw in alert_keywords if kw in text)

                return {
                    'value': count,
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'collector': self.name,
                    'metadata': {
                        'unit': 'alerts',
                        'source': 'EPA Website',
                        'data_source': 'LIVE'
                    }
                }

            return None

        except Exception as e:
            self.logger.error(f"EPA water fetch error: {e}")
            return None

    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock data."""
        return {
            'value': 3,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {
                'unit': 'alerts',
                'source': 'mock_data',
                'data_source': 'MOCK'
            }
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        if not data or 'value' not in data:
            return False
        return isinstance(data['value'], (int, float))


class DroughtMonitorCollector(BaseCollector):
    """Collects drought severity data from US Drought Monitor."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "DroughtMonitor"
        # USDM has a public data API
        self.base_url = "https://droughtmonitor.unl.edu/DmData/DataDownload/WebServiceData.ashx"

    def collect(self) -> Dict[str, Any]:
        """Collect drought monitor data."""
        try:
            data = self._fetch_drought_data()
            if data:
                return data
            return self._get_mock_data()

        except Exception as e:
            self.logger.error(f"Failed to collect drought data: {e}")
            return self._get_mock_data()

    def _fetch_drought_data(self) -> Optional[Dict[str, Any]]:
        """Fetch drought data from USDM."""
        try:
            # Get statistics for US overall
            params = {
                'Area': 'CONUS',
                'statstype': 'GetDSCI',
                'format': 'json'
            }

            response = requests.get(
                self.base_url,
                params=params,
                headers={'User-Agent': 'Canairy/1.0'},
                timeout=15
            )

            if response.status_code == 200:
                try:
                    data = response.json()

                    if data and len(data) > 0:
                        latest = data[-1] if isinstance(data, list) else data

                        # DSCI ranges 0-500, higher = more drought
                        dsci = float(latest.get('DSCI', 0))

                        # Get D3+ percentage if available
                        d3_pct = float(latest.get('D3', 0)) + float(latest.get('D4', 0))

                        self.logger.info(f"Drought Monitor: DSCI={dsci:.0f}, D3+={d3_pct:.1f}%")

                        return {
                            'value': round(d3_pct, 1),
                            'timestamp': datetime.utcnow().isoformat() + 'Z',
                            'collector': self.name,
                            'metadata': {
                                'unit': 'percent_area_d3_plus',
                                'dsci': dsci,
                                'source': 'US Drought Monitor',
                                'data_source': 'LIVE'
                            }
                        }
                except:
                    pass

            # Fallback: scrape the main page for stats
            page_response = requests.get(
                "https://droughtmonitor.unl.edu/",
                headers={'User-Agent': 'Canairy/1.0'},
                timeout=15
            )

            if page_response.status_code == 200:
                import re
                text = page_response.text

                # Look for "X% in D3 or higher"
                d3_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*(?:in\s+)?D[34]', text)
                if d3_match:
                    d3_pct = float(d3_match.group(1))
                    return {
                        'value': d3_pct,
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                        'collector': self.name,
                        'metadata': {
                            'unit': 'percent_area_d3_plus',
                            'source': 'USDM Website',
                            'data_source': 'LIVE'
                        }
                    }

            return None

        except Exception as e:
            self.logger.error(f"Drought monitor fetch error: {e}")
            return None

    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock data."""
        return {
            'value': 8.5,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {
                'unit': 'percent_area_d3_plus',
                'source': 'mock_data',
                'data_source': 'MOCK'
            }
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        if not data or 'value' not in data:
            return False
        return isinstance(data['value'], (int, float))
