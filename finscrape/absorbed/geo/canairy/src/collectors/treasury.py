"""
Treasury market stress collector.

Tracks 10-year Treasury yield volatility and spreads as indicators
of financial system stress. Using FRED data instead of auction API.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from .base import BaseCollector
import json
import statistics

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class TreasuryCollector(BaseCollector):
    """Collects Treasury market stress indicators via FRED."""
    
    def __init__(self, config):
        """Initialize the Treasury collector."""
        super().__init__(config)
        self.threshold_amber = 3.0  # 3 basis points daily volatility
        self.threshold_red = 7.0    # 7 basis points daily volatility
        
    def collect(self) -> Dict[str, Any]:
        """
        Collect 10-year Treasury yield volatility as stress indicator.
        
        Returns:
            Dictionary with volatility in basis points
        """
        if not HAS_REQUESTS:
            return self._get_mock_data()
            
        try:
            # Try to get FRED API key
            api_key = self.config.get_secrets().get('fred_api_key')
            
            if api_key and api_key != 'your-fred-api-key-here':
                volatility_bp = self._fetch_treasury_volatility(api_key)
                
                if volatility_bp is not None:
                    self.logger.info(f"Treasury volatility: {volatility_bp:.1f} bp")
                    
                    return self._create_reading(
                        value=volatility_bp,
                        metadata={
                            'unit': 'basis_points',
                            'source': 'FRED_API',
                            'threshold_amber': self.threshold_amber,
                            'threshold_red': self.threshold_red,
                            'indicator': '10Y_yield_volatility',
                            'note': 'Daily yield volatility (5-day std dev)'
                        }
                    )
            
            return self._get_mock_data()
                
        except Exception as e:
            self.logger.error(f"Failed to collect Treasury data: {e}")
            return self._get_mock_data()
    
    def _fetch_treasury_volatility(self, api_key: str) -> Optional[float]:
        """Calculate 10-year Treasury yield volatility using FRED data."""
        try:
            # Get 10-year Treasury yields for past 30 days
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': 'DGS10',  # 10-Year Treasury Constant Maturity Rate
                'api_key': api_key,
                'file_type': 'json',
                'limit': 30,
                'sort_order': 'desc',
                'units': 'lin'  # Levels, not change
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'observations' in data and len(data['observations']) > 5:
                    # Get yields for last 5 days
                    yields = []
                    for obs in data['observations'][:5]:
                        if obs['value'] != '.':
                            yields.append(float(obs['value']))
                    
                    if len(yields) >= 3:
                        # Calculate daily changes in basis points
                        daily_changes = []
                        for i in range(1, len(yields)):
                            change_bp = abs(yields[i-1] - yields[i]) * 100
                            daily_changes.append(change_bp)
                        
                        # Use average daily change as volatility proxy
                        volatility = statistics.mean(daily_changes)
                        
                        self.logger.debug(f"Yields: {yields}, Changes: {daily_changes}, Vol: {volatility:.2f}bp")
                        return volatility
                        
                self.logger.warning("Insufficient Treasury yield data")
                
        except Exception as e:
            self.logger.error(f"FRED API error: {e}")
            
        return None
    
    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock data when API is unavailable."""
        mock_tail = 2.5  # 2.5 basis points
        
        self.logger.info(f"Using mock Treasury tail: {mock_tail} bp")
        
        return self._create_reading(
            value=mock_tail,
            metadata={
                'unit': 'basis_points',
                'source': 'mock_data',
                'threshold_amber': self.threshold_amber,
                'threshold_red': self.threshold_red,
                'note': 'Real API unavailable, using mock data'
            }
        )
            
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate the collected Treasury data."""
        if not data or 'value' not in data:
            return False
            
        value = data['value']
        
        # Treasury tail should be between -50 and 50 basis points (reasonable bounds)
        if not isinstance(value, (int, float)) or value < -50 or value > 50:
            self.logger.warning(f"Invalid Treasury tail value: {value}")
            return False
            
        return True
        
    def format_reading(self, data: Dict[str, Any]) -> str:
        """Format the Treasury tail reading for display."""
        value = data.get('value', 0)
        return f"{value:.1f} bp"