"""
Strike Tracker web scraper for Cornell ILR data.
Scrapes the public strike tracker website when API is unavailable.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import re
from .base import BaseCollector


class StrikeTrackerScraperCollector(BaseCollector):
    """Scrapes strike data from Cornell ILR Strike Tracker website."""
    
    def __init__(self, config):
        super().__init__(config)
        self._name = "StrikeTrackerScraper"
        self.base_url = "https://striketracker.ilr.cornell.edu"
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Scrape strike data from the website.
        
        Returns:
            Dict with total worker-days on strike in last 30 days
        """
        try:
            # Try to scrape the main page for recent strikes
            total_worker_days = self._scrape_strike_data()
            
            if total_worker_days is None:
                return self._get_mock_data()
            
            return {
                'value': total_worker_days,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'worker_days',
                    'period': '30_days',
                    'source': 'cornell_ilr_scraper',
                    'description': f'{total_worker_days:,} worker-days on strike in last 30 days',
                    'data_type': 'scraped'
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to scrape strike data: {e}")
            return self._get_mock_data()
    
    def _scrape_strike_data(self) -> Optional[int]:
        """Scrape the Cornell Strike Tracker website."""
        try:
            # First, try to get the main page
            response = requests.get(
                self.base_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                timeout=30
            )
            
            if response.status_code != 200:
                self.logger.warning(f"Strike tracker returned status {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for different possible data locations
            # Method 1: Check for summary statistics
            total_worker_days = self._extract_summary_stats(soup)
            if total_worker_days:
                return total_worker_days
            
            # Method 2: Try to find recent strikes table
            total_worker_days = self._extract_from_strikes_table(soup)
            if total_worker_days:
                return total_worker_days
            
            # Method 3: Look for data in scripts/JSON
            total_worker_days = self._extract_from_scripts(soup)
            if total_worker_days:
                return total_worker_days
                
            self.logger.warning("Could not find strike data in page")
            return None
            
        except Exception as e:
            self.logger.error(f"Error scraping strike tracker: {e}")
            return None
    
    def _extract_summary_stats(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract from summary statistics if available."""
        # Look for patterns like "X worker-days" or "X workers on strike"
        patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s*worker[-\s]?days',
            r'(\d{1,3}(?:,\d{3})*)\s*total\s*days',
            r'(\d{1,3}(?:,\d{3})*)\s*strike\s*days'
        ]
        
        text = soup.get_text()
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                number_str = match.group(1).replace(',', '')
                return int(number_str)
        
        return None
    
    def _extract_from_strikes_table(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract from strikes table if available."""
        # Look for tables with strike data
        tables = soup.find_all('table')
        
        for table in tables:
            # Check if this looks like a strikes table
            headers = [th.get_text().strip().lower() for th in table.find_all('th')]
            
            if any('worker' in h for h in headers) or any('strike' in h for h in headers):
                # Found a potential strikes table
                total_days = 0
                cutoff_date = datetime.now() - timedelta(days=30)
                
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    
                    # Try to extract worker count and duration
                    for cell in cells:
                        text = cell.get_text().strip()
                        # Look for numbers that could be worker-days
                        if re.match(r'^\d{1,3}(?:,\d{3})*$', text):
                            number = int(text.replace(',', ''))
                            if number > 100:  # Likely worker-days
                                total_days += number
                
                if total_days > 0:
                    return total_days
        
        return None
    
    def _extract_from_scripts(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract from JavaScript data if available."""
        scripts = soup.find_all('script')
        
        for script in scripts:
            if script.string:
                # Look for JSON data in scripts
                if 'workerDays' in script.string or 'strikeData' in script.string:
                    # Try to extract numbers
                    numbers = re.findall(r'"workerDays":\s*(\d+)', script.string)
                    if numbers:
                        total = sum(int(n) for n in numbers)
                        if total > 0:
                            return total
        
        return None
    
    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock data when scraping fails."""
        import random
        
        # Realistic distribution of worker-days
        base = random.randint(10000, 50000)
        if random.random() < 0.1:  # 10% chance of major strikes
            base = random.randint(100000, 500000)
        elif random.random() < 0.05:  # 5% chance of massive strikes
            base = random.randint(500000, 1000000)
        
        return {
            'value': base,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {
                'unit': 'worker_days',
                'period': '30_days',
                'source': 'mock_data',
                'description': f'{base:,} worker-days on strike in last 30 days (mock)',
                'data_type': 'mock'
            }
        }
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate strike data."""
        if not data:
            return False
        
        value = data.get('value')
        return isinstance(value, int) and 0 <= value <= 10000000