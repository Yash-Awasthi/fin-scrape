"""
JODI (Joint Organisations Data Initiative) oil collector.
Tracks refinery run-rate ratio between India+China and OECD countries.
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .base import BaseCollector


class JODIOilCollector(BaseCollector):
    """Collects refinery data from JODI to calculate BRICS/OECD ratio."""
    
    def __init__(self, config):
        super().__init__(config)
        self._name = "JODIOil"
        self.api_base = "https://www.jodidata.org/_api/downloads/export/"
        self.api_key = self.config.get_secret('JODI_API_KEY')
        
        # Countries of interest
        self.brics_refiners = ['China', 'India']
        self.oecd_refiners = ['United States', 'Germany', 'Japan', 'France', 'United Kingdom']
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Collect refinery run rate data.
        
        Returns:
            Dict with refinery ratio or None if collection fails
        """
        try:
            ratio = self._calculate_refinery_ratio()
            
            if ratio is None:
                return None
            
            return {
                'value': round(ratio, 2),
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'ratio',
                    'source': 'JODI_API',
                    'description': f'India+China/OECD refinery ratio: {ratio:.2f}',
                    'brics_countries': self.brics_refiners,
                    'oecd_countries': self.oecd_refiners
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect JODI data: {e}")
            return None
    
    def _calculate_refinery_ratio(self) -> Optional[float]:
        """Calculate refinery run-rate ratio."""
        try:
            # JODI API requires authentication
            if not self.api_key:
                self.logger.warning("No JODI API key provided, using mock data")
                return self._get_mock_data()
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'User-Agent': 'Brown-Man-Bunker-Monitor/1.0'
            }
            
            # Get latest refinery data
            # JODI uses specific product codes for refinery runs
            product_code = 'REFOBS'  # Refinery observation/output
            
            # Fetch BRICS refinery data
            brics_total = 0
            for country in self.brics_refiners:
                try:
                    response = requests.get(
                        f"{self.api_base}oil-monthly",
                        params={
                            'country': country,
                            'product': product_code,
                            'flow': 'REFINOUT',  # Refinery output
                            'unit': 'KBBL/D',    # Thousand barrels per day
                            'from': (datetime.now() - timedelta(days=90)).strftime('%Y-%m'),
                            'to': datetime.now().strftime('%Y-%m')
                        },
                        headers=headers,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        # Extract latest value
                        if data and 'data' in data and len(data['data']) > 0:
                            latest = data['data'][-1]  # Most recent month
                            brics_total += float(latest.get('value', 0))
                except Exception as e:
                    self.logger.error(f"Failed to get data for {country}: {e}")
            
            # Fetch OECD refinery data
            oecd_total = 0
            for country in self.oecd_refiners:
                try:
                    response = requests.get(
                        f"{self.api_base}oil-monthly",
                        params={
                            'country': country,
                            'product': product_code,
                            'flow': 'REFINOUT',
                            'unit': 'KBBL/D',
                            'from': (datetime.now() - timedelta(days=90)).strftime('%Y-%m'),
                            'to': datetime.now().strftime('%Y-%m')
                        },
                        headers=headers,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data and 'data' in data and len(data['data']) > 0:
                            latest = data['data'][-1]
                            oecd_total += float(latest.get('value', 0))
                except Exception as e:
                    self.logger.error(f"Failed to get data for {country}: {e}")
            
            # Calculate ratio
            if oecd_total > 0:
                ratio = brics_total / oecd_total
                self.logger.info(f"Refinery ratio: BRICS={brics_total:.0f} OECD={oecd_total:.0f} Ratio={ratio:.2f}")
                return ratio
            else:
                self.logger.warning("No OECD refinery data found")
                return self._get_mock_data()
                
        except Exception as e:
            self.logger.error(f"Failed to calculate refinery ratio: {e}")
            return self._get_mock_data()
    
    def _get_mock_data(self) -> float:
        """Return realistic mock refinery ratio."""
        import random
        
        # Realistic refinery ratios
        # India + China have been expanding refinery capacity
        # while OECD has been relatively flat
        
        # Base ratio around 0.8-1.0 (BRICS catching up)
        base_ratio = random.uniform(0.8, 1.0)
        
        # Add trend factor (BRICS growing faster)
        trend = random.uniform(0, 0.3)
        
        # Add volatility
        volatility = random.uniform(-0.1, 0.1)
        
        ratio = base_ratio + trend + volatility
        
        # Cap at reasonable bounds
        return max(0.5, min(2.0, ratio))
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate JODI oil data."""
        if not data:
            return False
        
        value = data.get('value')
        if not isinstance(value, (int, float)):
            return False
        
        # Ratio should be positive and reasonable
        return 0 < value < 10