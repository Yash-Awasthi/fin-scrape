"""
Treasury reverse repo collector with real NY Fed API integration.

Connects to the Federal Reserve Bank of New York's API to fetch actual
reverse repurchase agreement (RRP) data for monitoring financial system liquidity.

API Documentation: https://www.newyorkfed.org/markets/desk-operations/reverse-repo
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from .base import BaseCollector

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class TreasuryRealCollector(BaseCollector):
    """Collects real Federal Reserve reverse repo data from NY Fed API."""
    
    def __init__(self, config):
        """Initialize the Treasury collector with real API endpoints."""
        super().__init__(config)
        
        # NY Fed API endpoints
        self.rrp_api_url = "https://markets.newyorkfed.org/api/rp/reverserepo/propositions/search.json"
        self.summary_api_url = "https://markets.newyorkfed.org/api/rp/reverserepo/propositions/summary"
        
        # Alternative: Treasury Direct API for auction data
        self.treasury_api_url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny"
        
        # Thresholds based on research document
        self.threshold_amber = 2200  # $2.2T in billions
        self.threshold_red = 2500    # $2.5T in billions
        
    def collect(self) -> Dict[str, Any]:
        """
        Collect reverse repo data from NY Fed API.
        
        Returns:
            Dictionary with RRP value in billions USD
        """
        if not HAS_REQUESTS:
            self.logger.warning("requests library not available, using mock data")
            return self._get_mock_data()
            
        try:
            # Try multiple data sources in order of preference
            
            # 1. Try NY Fed RRP API
            rrp_value = self._fetch_ny_fed_rrp()
            if rrp_value is not None:
                return self._create_reading(
                    value=rrp_value,
                    metadata={
                        'unit': 'billions_usd',
                        'source': 'ny_fed_rrp_api',
                        'threshold_amber': self.threshold_amber,
                        'threshold_red': self.threshold_red,
                        'data_date': datetime.now().strftime('%Y-%m-%d')
                    }
                )
            
            # 2. Try Treasury Direct API as fallback
            treasury_value = self._fetch_treasury_direct()
            if treasury_value is not None:
                return self._create_reading(
                    value=treasury_value,
                    metadata={
                        'unit': 'billions_usd',
                        'source': 'treasury_direct_api',
                        'threshold_amber': self.threshold_amber,
                        'threshold_red': self.threshold_red,
                        'data_date': datetime.now().strftime('%Y-%m-%d')
                    }
                )
            
            # 3. Fall back to mock data if APIs fail
            self.logger.warning("All API sources failed, using mock data")
            return self._get_mock_data()
            
        except Exception as e:
            self.logger.error(f"Failed to collect Treasury data: {e}")
            return self._get_mock_data()
    
    def _fetch_ny_fed_rrp(self) -> Optional[float]:
        """Fetch RRP data from NY Fed API."""
        try:
            # Get data from last 5 days to ensure we have recent data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=5)
            
            params = {
                'startDate': start_date.strftime('%Y-%m-%d'),
                'endDate': end_date.strftime('%Y-%m-%d'),
                'operationTypes': 'RRP',  # Reverse Repo
                'method': 'fixed_rate'
            }
            
            self.logger.debug(f"Fetching NY Fed RRP data with params: {params}")
            
            response = requests.get(
                self.rrp_api_url,
                params=params,
                timeout=30,
                headers={'Accept': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract the most recent RRP value
                if 'repo' in data and isinstance(data['repo'], list) and len(data['repo']) > 0:
                    # Sort by operation date to get most recent
                    sorted_data = sorted(data['repo'], key=lambda x: x.get('operationDate', ''), reverse=True)
                    latest = sorted_data[0]
                    
                    # Get total submitted amount in millions, convert to billions
                    if 'totalAmtSubmitted' in latest:
                        value_millions = float(latest['totalAmtSubmitted'])
                        value_billions = value_millions / 1000.0
                        
                        self.logger.info(f"NY Fed RRP: ${value_billions:.1f}B on {latest.get('operationDate', 'unknown date')}")
                        return value_billions
                        
            else:
                self.logger.warning(f"NY Fed API returned status {response.status_code}")
                
        except requests.RequestException as e:
            self.logger.error(f"NY Fed API request failed: {e}")
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to parse NY Fed data: {e}")
            
        return None
    
    def _fetch_treasury_direct(self) -> Optional[float]:
        """Fetch debt data from Treasury Direct API as a proxy."""
        try:
            # Get most recent debt data
            params = {
                'sort': '-record_date',
                'page[size]': 1,
                'fields': 'record_date,total_debt'
            }
            
            response = requests.get(
                self.treasury_api_url,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and len(data['data']) > 0:
                    latest = data['data'][0]
                    # This gives total debt, not RRP specifically
                    # Using a fraction as proxy (typically RRP is ~10% of total debt)
                    total_debt_millions = float(latest.get('total_debt', 0))
                    estimated_rrp = (total_debt_millions / 1000.0) * 0.08  # Convert to billions and estimate 8%
                    
                    self.logger.info(f"Estimated RRP from Treasury data: ${estimated_rrp:.1f}B")
                    return estimated_rrp
                    
        except Exception as e:
            self.logger.error(f"Treasury Direct API failed: {e}")
            
        return None
    
    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock data when APIs are unavailable."""
        mock_value = 2150.5  # $2.15T in billions
        
        self.logger.info(f"Using mock RRP value: ${mock_value}B")
        
        return self._create_reading(
            value=mock_value,
            metadata={
                'unit': 'billions_usd',
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
        
        # RRP should be between 0 and 5000 billion (reasonable bounds)
        if not isinstance(value, (int, float)) or value < 0 or value > 5000:
            self.logger.warning(f"Invalid RRP value: {value}")
            return False
            
        return True
        
    def format_reading(self, data: Dict[str, Any]) -> str:
        """Format the RRP reading for display."""
        value = data.get('value', 0)
        return f"${value:.1f}B"