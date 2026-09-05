"""
GDP Growth collector - a POSITIVE indicator for economic health.
When GDP ≥4% AND 10-yr Treasury <4% for 2 quarters, this is a GREEN flag.

This is different from other indicators - higher values are GOOD.
"""

from typing import Dict, Any, Optional
import requests
import logging
from datetime import datetime, timedelta
from .base import BaseCollector

class GDPGrowthCollector(BaseCollector):
    """Collects GDP growth data as a positive economic indicator."""
    
    def __init__(self, config):
        super().__init__(config)
        self._name = "GDP Growth"
        self.logger = logging.getLogger(__name__)
        
    def collect(self) -> Dict[str, Any]:
        """Collect GDP growth and check for green flag conditions."""
        try:
            # Fetch GDP and Treasury data
            gdp_treasury_data = self._fetch_gdp_and_treasury()
            
            if gdp_treasury_data:
                # Check green flag condition
                green_flag = (
                    gdp_treasury_data['gdp_growth'] >= 4.0 and 
                    gdp_treasury_data['treasury_10yr'] < 4.0 and
                    gdp_treasury_data['consecutive_quarters'] >= 2
                )
                
                return {
                    'name': self.name,
                    'value': gdp_treasury_data['gdp_growth'],
                    'metadata': {
                        'unit': 'percent',
                        'source': 'FRED_API',
                        'description': f'GDP: {gdp_treasury_data["gdp_growth"]:.1f}%, 10yr: {gdp_treasury_data["treasury_10yr"]:.2f}%',
                        'green_flag': green_flag,
                        'consecutive_quarters': gdp_treasury_data['consecutive_quarters'],
                        'treasury_10yr': gdp_treasury_data['treasury_10yr'],
                        'data_source': 'LIVE',
                        'indicator_type': 'POSITIVE'  # Higher is better
                    }
                }
            else:
                # Fallback to mock data
                return self._get_mock_data()
                
        except Exception as e:
            self.logger.error(f"Failed to collect GDP data: {e}")
            return self._get_mock_data()
    
    def _fetch_gdp_and_treasury(self) -> Optional[Dict[str, Any]]:
        """Fetch GDP growth and 10-year Treasury yield from FRED."""
        try:
            api_key = self.config.get_secrets().get('fred_api_key')
            if not api_key:
                self.logger.warning("No FRED API key configured")
                return None
            
            # Get real GDP growth (year-over-year)
            gdp_url = "https://api.stlouisfed.org/fred/series/observations"
            
            # A191RL1Q225SBEA = Real GDP growth rate (quarterly, annualized)
            gdp_params = {
                'series_id': 'A191RL1Q225SBEA',
                'api_key': api_key,
                'file_type': 'json',
                'limit': 8,  # Last 8 quarters
                'sort_order': 'desc'
            }
            
            gdp_response = requests.get(gdp_url, params=gdp_params, timeout=10)
            
            # Get 10-year Treasury yield
            treasury_params = {
                'series_id': 'DGS10',
                'api_key': api_key,
                'file_type': 'json',
                'limit': 1,
                'sort_order': 'desc'
            }
            
            treasury_response = requests.get(gdp_url, params=treasury_params, timeout=10)
            
            if gdp_response.status_code == 200 and treasury_response.status_code == 200:
                gdp_data = gdp_response.json()
                treasury_data = treasury_response.json()
                
                # Get latest GDP growth
                gdp_obs = gdp_data.get('observations', [])
                if gdp_obs:
                    latest_gdp = float(gdp_obs[0]['value'])
                    
                    # Count consecutive quarters with GDP ≥4%
                    consecutive = 0
                    for obs in gdp_obs:
                        if float(obs['value']) >= 4.0:
                            consecutive += 1
                        else:
                            break
                    
                    # Get latest 10-year yield
                    treasury_obs = treasury_data.get('observations', [])
                    latest_treasury = float(treasury_obs[0]['value']) if treasury_obs else 0.0
                    
                    return {
                        'gdp_growth': latest_gdp,
                        'treasury_10yr': latest_treasury,
                        'consecutive_quarters': consecutive
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching GDP/Treasury data: {e}")
            return None
    
    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock GDP growth data."""
        # Moderate growth scenario
        mock_gdp = 2.8
        mock_treasury = 4.5
        
        return {
            'name': self.name,
            'value': mock_gdp,
            'metadata': {
                'unit': 'percent',
                'source': 'Mock data - FRED unavailable',
                'description': f'GDP: {mock_gdp}%, 10yr: {mock_treasury}% (mock)',
                'green_flag': False,
                'consecutive_quarters': 0,
                'treasury_10yr': mock_treasury,
                'data_source': 'MOCK',
                'indicator_type': 'POSITIVE'
            }
        }
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate GDP growth data."""
        if not data or 'value' not in data:
            return False
            
        value = data['value']
        
        # GDP growth should be between -10% and +15%
        if not isinstance(value, (int, float)) or value < -10 or value > 15:
            self.logger.warning(f"Invalid GDP growth: {value}")
            return False
            
        return True