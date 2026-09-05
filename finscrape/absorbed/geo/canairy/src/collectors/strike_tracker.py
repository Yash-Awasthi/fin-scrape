"""
Cornell ILR Labor Action Tracker collector for monitoring US strike days.
Tracks total strike days per month as an economic/social stability indicator.
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .base import BaseCollector
from .strike_tracker_scraper import StrikeTrackerScraperCollector


class StrikeTrackerCollector(BaseCollector):
    """Collects US strike data from Cornell ILR Labor Action Tracker."""
    
    def __init__(self, config):
        super().__init__(config)
        self._name = "StrikeTracker"
        self.base_url = "https://striketracker.ilr.cornell.edu/api/v1/strikes"
        # Initialize scraper as fallback
        self.scraper = StrikeTrackerScraperCollector(config)
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Collect strike days from Cornell ILR Labor Action Tracker.
        
        Returns:
            Dict with strike days count or None if collection fails
        """
        try:
            strike_days = self._fetch_strike_data()
            
            if strike_days is None:
                return None
            
            return {
                'value': strike_days,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'strike_days',
                    'period': '30_days',
                    'source': 'Cornell_ILR',
                    'description': f'{strike_days:,} total strike days in last 30 days'
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect strike data: {e}")
            return None
    
    def _fetch_strike_data(self) -> Optional[int]:
        """Fetch strike data from Cornell ILR API."""
        try:
            # Calculate date range for last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Cornell ILR API parameters
            params = {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'country': 'United States'
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                timeout=30,
                headers={'User-Agent': 'Brown-Man-Bunker-Monitor/1.0'}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Calculate total strike days
                total_strike_days = 0
                for strike in data.get('strikes', []):
                    # Get number of workers and duration
                    workers = strike.get('approximate_number_of_participants', 0)
                    duration = strike.get('duration_days', 1)
                    
                    # Calculate worker-days for this strike
                    strike_days = workers * duration
                    total_strike_days += strike_days
                
                self.logger.info(f"Found {len(data.get('strikes', []))} strikes, "
                               f"total {total_strike_days:,} strike days")
                
                return total_strike_days
            else:
                self.logger.error(f"API returned status {response.status_code}")
                # Try scraper as fallback
                self.logger.info("Falling back to web scraper")
                return self._fallback_to_scraper()
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            # Try scraper as fallback
            self.logger.info("Falling back to web scraper due to request error")
            return self._fallback_to_scraper()
        except Exception as e:
            self.logger.error(f"Failed to parse strike data: {e}")
            return None
    
    def _fallback_to_scraper(self) -> Optional[int]:
        """Use web scraper as fallback when API fails."""
        try:
            result = self.scraper.collect()
            if result and 'value' in result:
                return result['value']
            return None
        except Exception as e:
            self.logger.error(f"Scraper fallback also failed: {e}")
            return None
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate strike data."""
        if not data:
            return False
        return 'value' in data and isinstance(data['value'], (int, float))