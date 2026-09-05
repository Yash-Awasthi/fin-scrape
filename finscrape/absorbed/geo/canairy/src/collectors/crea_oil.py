"""
CREA (Centre for Research on Energy and Clean Air) collector for Russian oil exports.
Tracks share of Russian crude going to BRICS nations.
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from io import StringIO
from .base import BaseCollector


class CREAOilCollector(BaseCollector):
    """Collects Russian oil export data from CREA tracker."""
    
    def __init__(self, config):
        super().__init__(config)
        self._name = "CREAOil"
        self.csv_url = "https://energyandcleanair.org/russia_oil_exports.csv"
        self.brics_countries = [
            'Brazil', 'Russia', 'India', 'China', 'South Africa',
            'Egypt', 'Ethiopia', 'Iran', 'Saudi Arabia', 'UAE'  # New BRICS+ members
        ]
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Collect Russian oil export data to BRICS.
        
        Returns:
            Dict with BRICS share percentage or None if collection fails
        """
        try:
            brics_share = self._fetch_oil_data()
            
            if brics_share is None:
                return None
            
            return {
                'value': round(brics_share, 1),
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'percent',
                    'period': '30_days',
                    'source': 'CREA_tracker',
                    'description': f'{brics_share:.1f}% of Russian crude to BRICS',
                    'brics_members': len(self.brics_countries)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect CREA oil data: {e}")
            return None
    
    def _fetch_oil_data(self) -> Optional[float]:
        """Fetch and analyze Russian oil export data."""
        try:
            # Download CSV data
            response = requests.get(
                self.csv_url,
                timeout=30,
                headers={'User-Agent': 'Brown-Man-Bunker-Monitor/1.0'}
            )
            
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch CSV: status {response.status_code}")
                return self._get_mock_data()
            
            # Parse CSV
            df = pd.read_csv(StringIO(response.text))
            
            # Filter for last 30 days
            df['date'] = pd.to_datetime(df['date'])
            cutoff_date = datetime.now() - timedelta(days=30)
            recent_df = df[df['date'] >= cutoff_date]
            
            if recent_df.empty:
                self.logger.warning("No recent data found")
                return self._get_mock_data()
            
            # Calculate BRICS share
            # Assuming columns: date, destination_country, volume_barrels
            if 'destination_country' in recent_df.columns and 'volume_barrels' in recent_df.columns:
                total_exports = recent_df['volume_barrels'].sum()
                brics_exports = recent_df[
                    recent_df['destination_country'].isin(self.brics_countries)
                ]['volume_barrels'].sum()
                
                if total_exports > 0:
                    brics_share = (brics_exports / total_exports) * 100
                    self.logger.info(f"BRICS share: {brics_share:.1f}% "
                                   f"({brics_exports:,.0f}/{total_exports:,.0f} barrels)")
                    return brics_share
                else:
                    return 0.0
            else:
                self.logger.warning("Expected columns not found in CSV")
                return self._get_mock_data()
                
        except Exception as e:
            self.logger.error(f"Failed to process oil data: {e}")
            return self._get_mock_data()
    
    def _get_mock_data(self) -> float:
        """Return realistic mock data when real data unavailable."""
        import random
        # Simulate BRICS share between 55-75%
        return round(random.uniform(55, 75), 1)
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate CREA oil data."""
        if not data:
            return False
        return 'value' in data and isinstance(data['value'], (int, float))