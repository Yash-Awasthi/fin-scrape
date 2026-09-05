"""
Luxury collapse index collector - tracks high-end market indicators.

When rich people start liquidating luxury assets, they often know something
the general public doesn't. This is an early warning "smart money" indicator.
"""

from typing import Dict, Any, Optional
import logging
import requests
from datetime import datetime, timedelta
from .base import BaseCollector


class LuxuryCollapseCollector(BaseCollector):
    """Tracks luxury market indicators as early warning signals."""
    
    def __init__(self, config):
        """Initialize the luxury collapse collector."""
        super().__init__(config)
        self._name = "LuxuryCollapse"
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Collect luxury market indicators.
        
        Tracks:
        - Luxury goods stocks (via Alpha Vantage)
        - High-end retail performance
        - Wealth preservation indicators
        
        Returns:
            Dictionary with luxury index or None if collection fails
        """
        try:
            # Try to use Alpha Vantage API
            api_key = self.config.get_secrets().get('alpha_vantage_key')
            
            if api_key and api_key != 'your-alpha-vantage-key-here':
                luxury_data = self._fetch_luxury_indicators(api_key)
                if luxury_data:
                    return luxury_data
            
            # Fallback to mock data
            rolex_discount = 5      # % below MSRP
            jet_bookings_drop = 15  # % YoY decline
            estate_listings_up = 20  # % increase in $5M+ listings
            yacht_price_cuts = 10   # % with price reductions
            
            luxury_index = (
                rolex_discount * 0.3 +
                jet_bookings_drop * 0.3 +
                estate_listings_up * 0.2 +
                yacht_price_cuts * 0.2
            )
            
            self.logger.info(f"Luxury collapse index: {luxury_index:.1f} (mock)")
            
            return {
                'value': round(luxury_index, 1),
                'timestamp': datetime.utcnow().isoformat(),
                'collector': self.name,
                'metadata': {
                    'unit': 'index',
                    'scale': '0-100',
                    'components': {
                        'rolex_discount': rolex_discount,
                        'jet_bookings_drop': jet_bookings_drop,
                        'estate_listings_increase': estate_listings_up,
                        'yacht_price_cuts': yacht_price_cuts
                    },
                    'source': 'mock_data',
                    'threshold_amber': 25,
                    'threshold_red': 40,
                    'note': 'Mock data - add alpha_vantage_key for real data'
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect luxury collapse data: {e}")
            return None
    
    def _fetch_luxury_indicators(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Fetch luxury market indicators from Alpha Vantage."""
        try:
            # Track luxury goods companies as proxy
            luxury_stocks = {
                'LVMUY': {'name': 'LVMH', 'weight': 0.3},      # Louis Vuitton, Moet, Hennessy
                'RMS.PA': {'name': 'Hermes', 'weight': 0.2},   # Hermes (Paris)
                'CFR.SW': {'name': 'Richemont', 'weight': 0.2}, # Cartier, Van Cleef
                'RL': {'name': 'Ralph Lauren', 'weight': 0.15}, # Ralph Lauren
                'TPR': {'name': 'Tapestry', 'weight': 0.15}    # Coach, Kate Spade
            }
            
            # For US-listed stocks, get performance data
            us_stocks = ['RL', 'TPR']
            performances = {}
            
            for symbol in us_stocks:
                url = 'https://www.alphavantage.co/query'
                params = {
                    'function': 'GLOBAL_QUOTE',
                    'symbol': symbol,
                    'apikey': api_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'Global Quote' in data:
                        quote = data['Global Quote']
                        change_pct = float(quote.get('10. change percent', '0').rstrip('%'))
                        performances[symbol] = change_pct
                        
                # Be respectful of rate limits
                import time
                time.sleep(0.5)
            
            if performances:
                # Calculate index based on stock performance
                # More negative = more selling pressure
                avg_performance = sum(performances.values()) / len(performances)
                
                # Convert to 0-100 scale (more negative = higher index)
                # -10% daily loss = 100 on index, +5% gain = 0 on index
                luxury_index = max(0, min(100, ((-avg_performance + 5) / 15) * 100))
                
                self.logger.info(f"Luxury stocks avg: {avg_performance:.1f}%, index: {luxury_index:.1f}")
                
                return {
                    'value': round(luxury_index, 1),
                    'timestamp': datetime.utcnow().isoformat(),
                    'collector': self.name,
                    'metadata': {
                        'unit': 'index',
                        'scale': '0-100',
                        'source': 'alpha_vantage_api',
                        'stocks_tracked': list(performances.keys()),
                        'avg_performance': round(avg_performance, 2),
                        'threshold_amber': 25,
                        'threshold_red': 40,
                        'note': f'Based on luxury stock performance ({len(performances)} stocks)'
                    }
                }
                
        except Exception as e:
            self.logger.warning(f"Alpha Vantage error: {e}")
            
        return None
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate luxury collapse data."""
        if not data:
            return False
        
        required_fields = ['value', 'timestamp', 'collector']
        for field in required_fields:
            if field not in data:
                return False
        
        # Value should be between 0-100
        if not isinstance(data['value'], (int, float)) or data['value'] < 0 or data['value'] > 100:
            return False
            
        return True