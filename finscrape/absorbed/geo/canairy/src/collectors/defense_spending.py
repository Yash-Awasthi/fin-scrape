"""
Global defense spending tracker using SIPRI data.
Annual indicator updated each April.
"""

import requests
from datetime import datetime
from typing import Dict, Any, Optional
from .base import BaseCollector


class DefenseSpendingCollector(BaseCollector):
    """Tracks global military spending trends from SIPRI."""
    
    def __init__(self, config):
        super().__init__(config)
        self._name = "DefenseSpending"
        
        # SIPRI publishes annual data in April
        self.sipri_url = "https://www.sipri.org/databases/milex"
        
        # Historical data (in trillions USD)
        self.historical_data = {
            2020: 2.113,
            2021: 2.213,
            2022: 2.311,
            2023: 2.489,
            2024: 2.72   # Latest: $2.72T, +9.4% YoY
        }
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Collect defense spending data.
        
        Returns:
            Dict with YoY percentage change
        """
        try:
            # Get latest two years of data
            current_year = datetime.now().year
            
            # If it's after April, check if new data available
            if datetime.now().month >= 4:
                # In production, would scrape SIPRI for updates
                pass
            
            # Calculate YoY change
            latest_year = max(self.historical_data.keys())
            if latest_year > current_year:
                latest_year = current_year - 1
            
            current_spend = self.historical_data.get(latest_year, 2.72)
            previous_spend = self.historical_data.get(latest_year - 1, 2.489)
            
            yoy_change = ((current_spend - previous_spend) / previous_spend) * 100
            
            # Check for sustained high growth
            two_year_growth = self._check_sustained_growth()
            
            return {
                'value': round(yoy_change, 1),
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'percent_yoy',
                    'source': 'SIPRI',
                    'description': f'{yoy_change:.1f}% YoY military spending growth',
                    'latest_total': f'${current_spend}T',
                    'data_year': latest_year,
                    'sustained_growth': two_year_growth,
                    'update_month': 'April',
                    'is_context': True  # This is context, not real-time alert
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect defense spending data: {e}")
            return None
    
    def _check_sustained_growth(self) -> bool:
        """Check if growth >8% for two consecutive years."""
        years = sorted(self.historical_data.keys())
        if len(years) < 3:
            return False
        
        # Check last two YoY changes
        growth_rates = []
        for i in range(len(years) - 2, len(years)):
            current = self.historical_data[years[i]]
            previous = self.historical_data[years[i-1]]
            growth = ((current - previous) / previous) * 100
            growth_rates.append(growth)
        
        # Both years >8%?
        return all(rate > 8.0 for rate in growth_rates)
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate defense spending data."""
        if not data:
            return False
        
        value = data.get('value')
        return isinstance(value, (int, float)) and -50 <= value <= 100