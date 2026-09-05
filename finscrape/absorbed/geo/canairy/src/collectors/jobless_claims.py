"""
Jobless claims collector for unemployment surge detection.

Tracks weekly initial unemployment claims as an early economic warning signal.
"""

from typing import Dict, Any, Optional
import logging
import requests
from datetime import datetime
from .base import BaseCollector


class JoblessClaimsCollector(BaseCollector):
    """Collects weekly jobless claims data from Department of Labor."""
    
    def __init__(self, config):
        """Initialize the jobless claims collector."""
        super().__init__(config)
        self._name = "JoblessClaims"
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Collect current jobless claims data.
        
        Returns:
            Dictionary with claims data or None if collection fails
        """
        try:
            # Try to get real data from FRED API
            api_key = self.config.get_secrets().get('fred_api_key')
            
            if api_key and api_key != 'your-fred-api-key-here':
                # Use real FRED API
                url = "https://api.stlouisfed.org/fred/series/observations"
                params = {
                    'series_id': 'ICSA',  # Initial Claims Seasonally Adjusted
                    'api_key': api_key,
                    'file_type': 'json',
                    'limit': 1,
                    'sort_order': 'desc'
                }
                
                try:
                    response = requests.get(url, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if 'observations' in data and len(data['observations']) > 0:
                            latest = data['observations'][0]
                            claims_thousands = float(latest['value']) / 1000  # Convert to thousands
                            self.logger.info(f"Real jobless claims from FRED: {claims_thousands}k")
                            
                            return {
                                'value': claims_thousands,
                                'timestamp': datetime.utcnow().isoformat(),
                                'collector': self.name,
                                'metadata': {
                                    'unit': 'thousands',
                                    'period': 'weekly',
                                    'source': 'FRED_API',
                                    'date': latest['date'],
                                    'threshold_amber': 275,
                                    'threshold_red': 350,
                                    'note': 'Live data from Federal Reserve Economic Data'
                                }
                            }
                except Exception as api_error:
                    self.logger.warning(f"FRED API error, falling back to mock: {api_error}")
            
            # Fallback to mock data
            claims_thousands = 245
            self.logger.info(f"Using mock jobless claims: {claims_thousands}k")
            
            return {
                'value': claims_thousands,
                'timestamp': datetime.utcnow().isoformat(),
                'collector': self.name,
                'metadata': {
                    'unit': 'thousands',
                    'period': 'weekly',
                    'source': 'mock_data',
                    'threshold_amber': 275,
                    'threshold_red': 350,
                    'note': 'Mock data - add fred_api_key to secrets.yaml for real data'
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect jobless claims: {e}")
            return None
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate jobless claims data."""
        if not data:
            return False
        
        required_fields = ['value', 'timestamp', 'collector']
        for field in required_fields:
            if field not in data:
                return False
        
        # Value should be positive number
        if not isinstance(data['value'], (int, float)) or data['value'] < 0:
            return False
            
        return True