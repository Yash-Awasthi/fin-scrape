"""
USDA Crop Conditions collector.
Tracks major US crop conditions from NASS (National Agricultural Statistics Service).

API: https://quickstats.nass.usda.gov/api
"""

import requests
import os
from datetime import datetime
from typing import Dict, Any, Optional
from .base import BaseCollector


class USDACropConditionCollector(BaseCollector):
    """Collects crop condition data from USDA NASS."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "USDACropCondition"
        self.api_key = os.getenv('DATA_GOV_API_KEY', '')
        self.base_url = "https://quickstats.nass.usda.gov/api/api_GET/"

    def collect(self) -> Dict[str, Any]:
        """Collect crop condition data."""
        try:
            if not self.api_key:
                return self._get_mock_data()

            data = self._fetch_crop_conditions()
            if data:
                return data
            return self._get_mock_data()

        except Exception as e:
            self.logger.error(f"Failed to collect USDA crop data: {e}")
            return self._get_mock_data()

    def _fetch_crop_conditions(self) -> Optional[Dict[str, Any]]:
        """Fetch crop conditions from USDA NASS API."""
        try:
            # Get corn crop condition as representative (major US crop)
            params = {
                'key': self.api_key,
                'commodity_desc': 'CORN',
                'statisticcat_desc': 'CONDITION',
                'unit_desc': 'PCT GOOD',
                'year': datetime.now().year,
                'source_desc': 'SURVEY',
                'format': 'JSON'
            }

            response = requests.get(self.base_url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                records = data.get('data', [])

                if records:
                    # Get most recent week
                    sorted_records = sorted(records, key=lambda x: x.get('week_ending', ''), reverse=True)
                    latest = sorted_records[0]

                    good_pct = float(latest.get('Value', 0))

                    # Also try to get EXCELLENT rating
                    excellent_pct = 0
                    for r in sorted_records:
                        if r.get('week_ending') == latest.get('week_ending'):
                            if 'EXCELLENT' in r.get('unit_desc', '').upper():
                                excellent_pct = float(r.get('Value', 0))
                                break

                    combined_pct = good_pct + excellent_pct

                    self.logger.info(f"USDA Crops: {combined_pct:.0f}% Good/Excellent")

                    return {
                        'value': round(combined_pct, 1),
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                        'collector': self.name,
                        'metadata': {
                            'unit': 'percent_good_excellent',
                            'good_pct': good_pct,
                            'excellent_pct': excellent_pct,
                            'week_ending': latest.get('week_ending'),
                            'crop': 'CORN',
                            'source': 'USDA NASS',
                            'data_source': 'LIVE'
                        }
                    }

            self.logger.warning(f"USDA NASS API returned {response.status_code}")
            return None

        except Exception as e:
            self.logger.error(f"USDA crop fetch error: {e}")
            return None

    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock data."""
        return {
            'value': 68.0,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {
                'unit': 'percent_good_excellent',
                'source': 'mock_data',
                'data_source': 'MOCK'
            }
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        if not data or 'value' not in data:
            return False
        return isinstance(data['value'], (int, float))


class USDALivestockDiseaseCollector(BaseCollector):
    """Collects livestock disease alert data from USDA APHIS."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "USDALivestockDisease"
        self.aphis_url = "https://www.aphis.usda.gov/aphis/ourfocus/animalhealth/animal-disease-information"

    def collect(self) -> Dict[str, Any]:
        """Collect livestock disease alerts."""
        try:
            data = self._fetch_disease_alerts()
            if data:
                return data
            return self._get_mock_data()

        except Exception as e:
            self.logger.error(f"Failed to collect USDA APHIS data: {e}")
            return self._get_mock_data()

    def _fetch_disease_alerts(self) -> Optional[Dict[str, Any]]:
        """Fetch disease alerts from APHIS."""
        try:
            # APHIS doesn't have a direct API - scrape their RSS or alert page
            response = requests.get(
                self.aphis_url,
                headers={'User-Agent': 'Canairy/1.0 (household-resilience-monitor)'},
                timeout=15
            )

            if response.status_code == 200:
                text = response.text.lower()

                # Count active disease keywords
                disease_keywords = ['outbreak', 'confirmed', 'emergency', 'hpai', 'avian influenza',
                                   'african swine fever', 'foot and mouth', 'vesicular stomatitis']

                alert_count = 0
                for kw in disease_keywords:
                    if kw in text:
                        alert_count += 1

                self.logger.info(f"USDA APHIS: {alert_count} disease keywords found")

                return {
                    'value': alert_count,
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'collector': self.name,
                    'metadata': {
                        'unit': 'active_alerts',
                        'source': 'USDA APHIS',
                        'data_source': 'LIVE'
                    }
                }

            return None

        except Exception as e:
            self.logger.error(f"APHIS fetch error: {e}")
            return None

    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock data."""
        return {
            'value': 2,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {
                'unit': 'active_alerts',
                'source': 'mock_data',
                'data_source': 'MOCK'
            }
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        if not data or 'value' not in data:
            return False
        return isinstance(data['value'], (int, float))


class USDAMeatProcessingCollector(BaseCollector):
    """Collects meat processing capacity data from USDA AMS."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "USDAMeatProcessing"
        self.api_key = os.getenv('DATA_GOV_API_KEY', '')
        # USDA AMS Market News API
        self.base_url = "https://marsapi.ams.usda.gov/services/v1.2/reports"

    def collect(self) -> Dict[str, Any]:
        """Collect meat processing capacity data."""
        try:
            data = self._fetch_processing_data()
            if data:
                return data
            return self._get_mock_data()

        except Exception as e:
            self.logger.error(f"Failed to collect USDA AMS data: {e}")
            return self._get_mock_data()

    def _fetch_processing_data(self) -> Optional[Dict[str, Any]]:
        """Fetch processing data from USDA AMS."""
        try:
            # Get cattle slaughter report
            headers = {'User-Agent': 'Canairy/1.0'}
            if self.api_key:
                headers['X-Api-Key'] = self.api_key

            # Try LM_CT150 (Daily Cattle Slaughter)
            response = requests.get(
                f"{self.base_url}/LM_CT150",
                headers=headers,
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])

                if results:
                    # Get latest slaughter numbers
                    latest = results[0]

                    # Calculate capacity utilization (estimated)
                    # Normal daily cattle slaughter ~125,000 head
                    daily_slaughter = float(latest.get('head_count', 125000))
                    normal_capacity = 125000
                    capacity_pct = (daily_slaughter / normal_capacity) * 100

                    self.logger.info(f"USDA AMS: {capacity_pct:.0f}% processing capacity")

                    return {
                        'value': round(capacity_pct, 1),
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                        'collector': self.name,
                        'metadata': {
                            'unit': 'percent_capacity',
                            'daily_head': daily_slaughter,
                            'source': 'USDA AMS',
                            'data_source': 'LIVE'
                        }
                    }

            # Fallback - return estimated normal
            return None

        except Exception as e:
            self.logger.error(f"USDA AMS fetch error: {e}")
            return None

    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock data."""
        return {
            'value': 95.0,
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
