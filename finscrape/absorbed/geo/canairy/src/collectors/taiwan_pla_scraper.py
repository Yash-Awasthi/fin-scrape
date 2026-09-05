"""
Taiwan MND PLA activity web scraper.
Scrapes PLA aircraft incursion data from Taiwan's Ministry of National Defense.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import re
from .base import BaseCollector


class TaiwanPLAScraperCollector(BaseCollector):
    """Scrapes PLA activity data from Taiwan MND website."""
    
    def __init__(self, config):
        super().__init__(config)
        self._name = "TaiwanPLAScraper"
        # Taiwan MND English site
        self.base_url = "https://www.mnd.gov.tw/english/"
        # Alternative: Direct reports page
        self.reports_url = "https://www.mnd.gov.tw/PublishTable.aspx?Types=即時軍事動態&title=國防消息"
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Scrape PLA incursion data from Taiwan MND.
        
        Returns:
            Dict with 14-day average of PLA aircraft
        """
        try:
            # Try to scrape recent PLA activity
            avg_aircraft = self._scrape_pla_activity()
            
            if avg_aircraft is None:
                return self._get_mock_data()
            
            # Determine threat level
            threat_description = "Normal activity"
            if avg_aircraft > 50:
                threat_description = "Heightened military pressure"
            elif avg_aircraft > 100:
                threat_description = "Severe escalation - possible blockade preparation"
            
            return {
                'value': avg_aircraft,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'aircraft_per_day',
                    'period': '14_days',
                    'source': 'taiwan_mnd_scraper',
                    'description': f'{avg_aircraft} PLA aircraft/day (14-day avg)',
                    'threat_assessment': threat_description,
                    'data_type': 'scraped'
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to scrape Taiwan MND data: {e}")
            return self._get_mock_data()
    
    def _scrape_pla_activity(self) -> Optional[int]:
        """Scrape PLA activity from Taiwan MND website."""
        try:
            # First try the English site
            response = requests.get(
                self.base_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept-Language': 'en-US,en;q=0.9'
                },
                timeout=30
            )
            
            if response.status_code != 200:
                self.logger.warning(f"Taiwan MND returned status {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for PLA activity reports
            aircraft_counts = self._extract_aircraft_counts(soup)
            
            if aircraft_counts:
                # Calculate 14-day average
                recent_counts = aircraft_counts[:14]  # Last 14 days
                if recent_counts:
                    return sum(recent_counts) // len(recent_counts)
            
            # Try alternative extraction methods
            daily_avg = self._extract_from_summary(soup)
            if daily_avg:
                return daily_avg
                
            self.logger.warning("Could not find PLA activity data")
            return None
            
        except Exception as e:
            self.logger.error(f"Error scraping Taiwan MND: {e}")
            return None
    
    def _extract_aircraft_counts(self, soup: BeautifulSoup) -> List[int]:
        """Extract aircraft counts from daily reports."""
        counts = []
        
        # Look for patterns in the page
        # Common patterns: "X aircraft", "X PLA aircraft", "X military aircraft"
        patterns = [
            r'(\d+)\s*(?:PLA\s*)?aircraft',
            r'(\d+)\s*military\s*aircraft',
            r'aircraft[:\s]+(\d+)',
            r'偵獲共機\s*(\d+)\s*架次'  # Chinese pattern
        ]
        
        # Find all text that might contain aircraft counts
        text_elements = soup.find_all(text=True)
        
        for text in text_elements:
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    count = int(match)
                    if 0 < count < 200:  # Sanity check
                        counts.append(count)
        
        # Also look for structured data in tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                for cell in cells:
                    text = cell.get_text().strip()
                    # Look for numbers that could be aircraft counts
                    if re.match(r'^\d{1,3}$', text):
                        count = int(text)
                        if 0 < count < 200:
                            counts.append(count)
        
        return counts
    
    def _extract_from_summary(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract from summary statistics if available."""
        # Look for average or summary statements
        patterns = [
            r'average[:\s]+(\d+)\s*aircraft',
            r'daily\s*average[:\s]+(\d+)',
            r'(\d+)\s*aircraft\s*per\s*day'
        ]
        
        text = soup.get_text()
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None
    
    def _get_mock_data(self) -> Dict[str, Any]:
        """Return realistic mock data."""
        import random
        
        # Realistic distribution based on recent trends
        # Normal: 10-30 aircraft/day
        # Elevated: 30-50 aircraft/day  
        # High tension: 50-100 aircraft/day
        # Crisis: 100+ aircraft/day
        
        rand = random.random()
        if rand < 0.6:  # 60% normal
            avg_aircraft = random.randint(10, 30)
            threat = "Normal activity"
        elif rand < 0.85:  # 25% elevated
            avg_aircraft = random.randint(30, 50)
            threat = "Elevated activity"
        elif rand < 0.95:  # 10% high tension
            avg_aircraft = random.randint(50, 100)
            threat = "High tension - significant escalation"
        else:  # 5% crisis
            avg_aircraft = random.randint(100, 150)
            threat = "Crisis level - possible blockade imminent"
        
        return {
            'value': avg_aircraft,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {
                'unit': 'aircraft_per_day',
                'period': '14_days',
                'source': 'mock_data',
                'description': f'{avg_aircraft} PLA aircraft/day (14-day avg) - mock',
                'threat_assessment': threat,
                'data_type': 'mock'
            }
        }
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate PLA activity data."""
        if not data:
            return False
        
        value = data.get('value')
        return isinstance(value, int) and 0 <= value <= 500