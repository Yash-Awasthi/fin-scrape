"""
Labor market displacement collector - tracks AI-driven job displacement.

Monitors the rate at which AI/automation is displacing human workers across
different sectors, a critical indicator of societal disruption.
"""

from typing import Dict, Any, Optional
import logging
import requests
from datetime import datetime
from .base import BaseCollector


class LaborDisplacementCollector(BaseCollector):
    """Tracks AI-driven labor market displacement rates."""
    
    def __init__(self, config):
        """Initialize the labor displacement collector."""
        super().__init__(config)
        self._name = "LaborDisplacement"
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Collect labor displacement data.
        
        Monitors:
        - Tech sector layoffs attributed to AI
        - Call center/customer service automation rates
        - Legal/medical AI adoption metrics
        - Manufacturing automation acceleration
        
        Returns:
            Dictionary with displacement rate or None if collection fails
        """
        try:
            # Sector-specific displacement rates (% of workforce)
            sector_displacement = {
                'customer_service': {
                    'current_rate': 15,  # 15% already automated
                    'annual_growth': 8,   # Growing 8% per year
                    'workers_affected': 2_500_000
                },
                'data_entry': {
                    'current_rate': 25,
                    'annual_growth': 12,
                    'workers_affected': 1_200_000
                },
                'content_creation': {
                    'current_rate': 10,
                    'annual_growth': 15,  # Rapid growth
                    'workers_affected': 800_000
                },
                'programming': {
                    'current_rate': 5,
                    'annual_growth': 10,
                    'workers_affected': 500_000
                },
                'legal_research': {
                    'current_rate': 8,
                    'annual_growth': 7,
                    'workers_affected': 200_000
                },
                'financial_analysis': {
                    'current_rate': 12,
                    'annual_growth': 9,
                    'workers_affected': 600_000
                }
            }
            
            # Calculate weighted displacement rate
            total_workers = sum(s['workers_affected'] for s in sector_displacement.values())
            weighted_displacement = sum(
                s['current_rate'] * s['workers_affected'] / total_workers
                for s in sector_displacement.values()
            )
            
            # Calculate acceleration (how fast displacement is growing)
            weighted_growth = sum(
                s['annual_growth'] * s['workers_affected'] / total_workers
                for s in sector_displacement.values()
            )
            
            # Try to get real employment data from FRED
            api_key = self.config.get_secrets().get('fred_api_key')
            
            if api_key and api_key != 'your-fred-api-key-here':
                real_data = self._fetch_employment_trends(api_key)
                if real_data:
                    return real_data
            
            # Fallback to calculated index
            displacement_index = weighted_displacement + (weighted_growth * 0.5)
            
            self.logger.info(f"Labor displacement: {weighted_displacement:.1f}% current, {weighted_growth:.1f}% growth (mock)")
            
            return {
                'value': displacement_index,
                'timestamp': datetime.utcnow().isoformat(),
                'collector': self.name,
                'metadata': {
                    'unit': 'displacement_index',
                    'current_displacement_pct': weighted_displacement,
                    'annual_growth_pct': weighted_growth,
                    'sectors': sector_displacement,
                    'total_workers_monitored': total_workers,
                    'source': 'mock_data',
                    'threshold_amber': 20,
                    'threshold_red': 35,
                    'note': 'Mock data - enhanced FRED integration available'
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect labor displacement data: {e}")
            return None
    
    def _fetch_employment_trends(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Fetch employment trends from FRED to calculate displacement."""
        try:
            # Key employment series to track
            series = {
                'PAYEMS': 'Total Nonfarm Payrolls',
                'USINFO': 'Information Services Employment',
                'CES4422000001': 'Retail Trade Employment',
                'CES6562000001': 'Professional Services Employment'
            }
            
            url = "https://api.stlouisfed.org/fred/series/observations"
            
            # Get latest employment level for information sector
            params = {
                'series_id': 'USINFO',
                'api_key': api_key,
                'file_type': 'json',
                'limit': 13,  # Get 13 months for YoY
                'sort_order': 'desc'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'observations' in data and len(data['observations']) >= 13:
                    # Get current and year-ago values
                    current = float(data['observations'][0]['value'])
                    year_ago = float(data['observations'][12]['value'])
                    
                    # Calculate YoY change
                    yoy_change = ((current - year_ago) / year_ago) * 100
                    
                    # If employment is declining in tech/info sector, displacement is happening
                    # Convert to displacement index (negative growth = positive displacement)
                    displacement_index = max(0, -yoy_change * 5)  # Scale factor
                    
                    self.logger.info(f"Info sector employment YoY: {yoy_change:.1f}%, displacement index: {displacement_index:.1f}")
                    
                    return {
                        'value': displacement_index,
                        'timestamp': datetime.utcnow().isoformat(),
                        'collector': self.name,
                        'metadata': {
                            'unit': 'displacement_index',
                            'source': 'FRED_API',
                            'info_sector_yoy': round(yoy_change, 1),
                            'info_employment': int(current),
                            'threshold_amber': 20,
                            'threshold_red': 35,
                            'note': f'Based on information sector employment trends'
                        }
                    }
                    
        except Exception as e:
            self.logger.warning(f"FRED employment data error: {e}")
            
        return None
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate labor displacement data."""
        if not data:
            return False
        
        required_fields = ['value', 'timestamp', 'collector']
        for field in required_fields:
            if field not in data:
                return False
        
        # Value should be non-negative
        if not isinstance(data['value'], (int, float)) or data['value'] < 0:
            return False
            
        return True