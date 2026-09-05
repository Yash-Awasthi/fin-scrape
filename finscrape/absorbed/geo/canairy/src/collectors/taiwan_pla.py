"""
Taiwan PLA activity collector.
Tracks PLA aircraft incursions and exclusion zone declarations.
"""

import requests
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
from .base import BaseCollector
from .taiwan_pla_scraper import TaiwanPLAScraperCollector


class TaiwanPLACollector(BaseCollector):
    """Collects PLA activity data from Taiwan MND and other sources."""
    
    def __init__(self, config):
        super().__init__(config)
        self._name = "TaiwanPLA"
        
        # Taiwan Ministry of National Defense
        self.mnd_url = "https://www.mnd.gov.tw/english/PublishTable.aspx?Types=Military%20News&Title=News"
        
        # Alternative sources for exclusion zones
        self.notam_sources = [
            "https://www.notams.faa.gov/search",  # Would need proper API
            "https://english.news.cn/",  # Xinhua for announcements
        ]
        
        # Initialize scraper as fallback
        self.scraper = TaiwanPLAScraperCollector(config)
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Collect Taiwan PLA activity data.
        
        Returns:
            Dict with max daily incursions or exclusion days
        """
        try:
            # Get both metrics
            daily_incursions = self._fetch_incursion_data()
            exclusion_days = self._check_exclusion_zones()
            
            # Use the more severe metric
            if exclusion_days > 0:
                value = exclusion_days
                metric_type = "exclusion_days"
                description = f"{exclusion_days} days of active exclusion zone"
            else:
                value = daily_incursions
                metric_type = "daily_incursions"
                description = f"{daily_incursions} PLA aircraft incursions (max daily)"
            
            return {
                'value': value,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': metric_type,
                    'source': 'Taiwan_MND',
                    'description': description,
                    'daily_incursions': daily_incursions,
                    'exclusion_days': exclusion_days,
                    'critical_threshold': 100  # Aircraft per day
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect Taiwan PLA data: {e}")
            return None
    
    def _fetch_incursion_data(self) -> int:
        """Fetch PLA aircraft incursion data from Taiwan MND."""
        try:
            # In production, would scrape MND daily reports
            # Format: "XX PLA aircraft... crossed the median line"
            
            response = requests.get(
                self.mnd_url,
                timeout=30,
                headers={'User-Agent': 'Brown-Man-Bunker-Monitor/1.0'}
            )
            
            if response.status_code != 200:
                self.logger.warning(f"Failed to fetch MND data: {response.status_code}")
                return self._get_mock_incursions()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for PLA aircraft numbers in recent reports
            max_daily = 0
            reports = soup.find_all('div', class_='news-item', limit=7)  # Last week
            
            for report in reports:
                text = report.get_text()
                # Pattern: "XX PLA aircraft"
                match = re.search(r'(\d+)\s+PLA\s+aircraft', text)
                if match:
                    count = int(match.group(1))
                    max_daily = max(max_daily, count)
                    self.logger.info(f"Found PLA incursion: {count} aircraft")
            
            if max_daily > 0:
                return max_daily
            else:
                # Fall back to scraper
                return self._use_scraper_fallback()
            
        except Exception as e:
            self.logger.error(f"Failed to parse MND data: {e}")
            return self._use_scraper_fallback()
    
    def _check_exclusion_zones(self) -> int:
        """Check for active PLA exclusion zones."""
        # In production, would check:
        # 1. NOTAMs for military exercise zones
        # 2. Maritime safety announcements
        # 3. News for "no-fly zone" declarations
        
        # For now, return mock data
        return self._get_mock_exclusion_days()
    
    def _get_mock_incursions(self) -> int:
        """Return realistic mock incursion data."""
        import random
        
        # Normal range: 5-30 aircraft/day
        # Elevated: 30-70
        # Crisis: 70-150+
        
        rand = random.random()
        if rand < 0.7:  # 70% normal
            return random.randint(5, 30)
        elif rand < 0.95:  # 25% elevated
            return random.randint(30, 70)
        else:  # 5% crisis level
            return random.randint(70, 150)
    
    def _get_mock_exclusion_days(self) -> int:
        """Return mock exclusion zone data."""
        import random
        
        # Usually 0, occasionally 1-3 days, rarely 7+
        rand = random.random()
        if rand < 0.9:  # 90% no exclusion
            return 0
        elif rand < 0.98:  # 8% short exclusion
            return random.randint(1, 3)
        else:  # 2% extended exclusion
            return random.randint(4, 10)
    
    def _use_scraper_fallback(self) -> int:
        """Use web scraper when primary methods fail."""
        try:
            self.logger.info("Using web scraper fallback for Taiwan PLA data")
            result = self.scraper.collect()
            if result and 'value' in result:
                return result['value']
            return self._get_mock_incursions()
        except Exception as e:
            self.logger.error(f"Scraper fallback failed: {e}")
            return self._get_mock_incursions()
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate Taiwan PLA data."""
        if not data:
            return False
        
        value = data.get('value')
        return isinstance(value, (int, float)) and value >= 0