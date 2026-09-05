"""
Grocery CPI collector for household cost-of-living monitoring.
Uses BLS API to track food inflation as a household resilience indicator.

Green: <4% annualized
Amber: 4-8% annualized  
Red: >8% annualized
"""

from typing import Dict, Any, Optional
import requests
import logging
from datetime import datetime, timedelta
from .base import BaseCollector

class GroceryCPICollector(BaseCollector):
    """Collects grocery/food CPI data from Bureau of Labor Statistics."""
    
    def __init__(self, config):
        super().__init__(config)
        self._name = "Grocery CPI"
        self.logger = logging.getLogger(__name__)
        
    def collect(self) -> Dict[str, Any]:
        """Collect latest grocery CPI data and calculate 3-month annualized rate."""
        try:
            # Try to fetch from BLS API
            cpi_data = self._fetch_grocery_cpi()
            
            if cpi_data:
                return {
                    'name': self.name,
                    'value': cpi_data['annualized_rate'],
                    'metadata': {
                        'unit': 'percent',
                        'source': 'BLS_API',
                        'series': 'CUUR0000SAF11',
                        'description': f'Food at home CPI, 3-month annualized: {cpi_data["annualized_rate"]:.1f}%',
                        'latest_value': cpi_data['latest_value'],
                        'previous_value': cpi_data['previous_value'],
                        'data_source': 'LIVE'
                    }
                }
            else:
                # Fallback to mock data
                return self._get_mock_data()
                
        except Exception as e:
            self.logger.error(f"Failed to collect grocery CPI data: {e}")
            return self._get_mock_data()
    
    def _fetch_grocery_cpi(self) -> Optional[Dict[str, Any]]:
        """Fetch grocery CPI from BLS API."""
        try:
            # BLS API endpoint for "Food at home" CPI
            # CUUR0000SAF11 = Consumer Price Index - Urban, Food at home
            url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
            
            # Calculate date range for last 4 months
            end_date = datetime.now()
            start_date = end_date - timedelta(days=120)
            
            # BLS API request payload
            payload = {
                "seriesid": ["CUUR0000SAF11"],
                "startyear": str(start_date.year),
                "endyear": str(end_date.year),
                "registrationkey": self.config.get_secrets().get('api_keys', {}).get('bls', '')  # Optional
            }
            
            headers = {'Content-type': 'application/json'}
            
            # Make request
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data['status'] == 'REQUEST_SUCCEEDED':
                    series_data = data['Results']['series'][0]['data']

                    # Filter out entries with '-' or invalid values
                    valid_data = [d for d in series_data if d.get('value', '-') != '-']

                    # Get latest 4 months of valid data
                    if len(valid_data) >= 4:
                        latest = float(valid_data[0]['value'])
                        three_months_ago = float(valid_data[3]['value'])
                        
                        # Calculate 3-month change and annualize
                        three_month_change = ((latest / three_months_ago) - 1) * 100
                        annualized_rate = three_month_change * 4  # Annualize
                        
                        return {
                            'latest_value': latest,
                            'previous_value': three_months_ago,
                            'three_month_change': three_month_change,
                            'annualized_rate': round(annualized_rate, 2)
                        }
            
            self.logger.warning("BLS API returned no data or request failed")
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching BLS data: {e}")
            return None
    
    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock grocery CPI data."""
        # Typical grocery inflation scenario
        mock_value = 5.2  # 5.2% annualized (amber range)
        
        return {
            'name': self.name,
            'value': mock_value,
            'metadata': {
                'unit': 'percent',
                'source': 'Mock data - BLS API unavailable',
                'description': f'Food inflation (mock): {mock_value}% annualized',
                'data_source': 'MOCK'
            }
        }
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate grocery CPI data."""
        if not data or 'value' not in data:
            return False
            
        value = data['value']
        
        # CPI change should be between -20% and +50% annualized
        if not isinstance(value, (int, float)) or value < -20 or value > 50:
            self.logger.warning(f"Invalid grocery CPI value: {value}")
            return False
            
        return True