"""
ICE detention statistics web scraper.
Scrapes detention population data from ICE and TRAC websites.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, Any, Optional
import re
from .base import BaseCollector


class ICEDetentionScraperCollector(BaseCollector):
    """Scrapes ICE detention data from public sources."""
    
    def __init__(self, config):
        super().__init__(config)
        self._name = "ICEDetentionScraper"
        # ICE official statistics page
        self.ice_url = "https://www.ice.gov/detain/detention-management"
        # TRAC Immigration detention stats
        self.trac_url = "https://trac.syr.edu/immigration/detentionstats/pop_agen_table.html"
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Scrape ICE detention population data.
        
        Returns:
            Dict with total detention population
        """
        try:
            # Try multiple sources
            detainee_count = None
            
            # First try ICE official site
            detainee_count = self._scrape_ice_site()
            
            # If that fails, try TRAC
            if detainee_count is None:
                detainee_count = self._scrape_trac_site()
            
            # If both fail, use mock data
            if detainee_count is None:
                return self._get_mock_data()
            
            # Calculate capacity percentage (typical capacity ~40,000)
            typical_capacity = 40000
            capacity_pct = (detainee_count / typical_capacity) * 100
            
            return {
                'value': detainee_count,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'detainees',
                    'source': 'ice_scraper',
                    'description': f'{detainee_count:,} total ICE detainees',
                    'capacity_percentage': round(capacity_pct, 1),
                    'typical_capacity': typical_capacity,
                    'data_type': 'scraped'
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to scrape ICE detention data: {e}")
            return self._get_mock_data()
    
    def _scrape_ice_site(self) -> Optional[int]:
        """Scrape the official ICE website."""
        try:
            response = requests.get(
                self.ice_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                timeout=30
            )
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for detention statistics
            # Common patterns: "XX,XXX detainees", "detention population: XX,XXX"
            patterns = [
                r'(\d{1,3}(?:,\d{3})*)\s*(?:total\s*)?detainees',
                r'detention\s*population[:\s]+(\d{1,3}(?:,\d{3})*)',
                r'(\d{1,3}(?:,\d{3})*)\s*(?:people|individuals)\s*in\s*(?:ICE\s*)?detention',
                r'currently\s*detaining\s*(\d{1,3}(?:,\d{3})*)'
            ]
            
            text = soup.get_text()
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    count_str = match.group(1).replace(',', '')
                    count = int(count_str)
                    if count > 10000:  # Sanity check - should be at least 10k
                        self.logger.info(f"Found ICE detention count: {count:,}")
                        return count
            
            # Look in tables
            tables = soup.find_all('table')
            for table in tables:
                # Look for cells with large numbers
                cells = table.find_all(['td', 'th'])
                for cell in cells:
                    text = cell.get_text().strip()
                    if re.match(r'^\d{2,3},\d{3}$', text):  # Format: XX,XXX
                        count = int(text.replace(',', ''))
                        if 10000 < count < 200000:  # Reasonable range
                            return count
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error scraping ICE site: {e}")
            return None
    
    def _scrape_trac_site(self) -> Optional[int]:
        """Scrape TRAC Immigration website as backup."""
        try:
            response = requests.get(
                self.trac_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                timeout=30
            )
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # TRAC often has data in tables
            tables = soup.find_all('table')
            for table in tables:
                # Look for total row
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    for i, cell in enumerate(cells):
                        if 'total' in cell.get_text().lower():
                            # Check next cells for numbers
                            for next_cell in cells[i+1:]:
                                text = next_cell.get_text().strip()
                                if re.match(r'^\d{2,3},?\d{3}$', text):
                                    count = int(text.replace(',', ''))
                                    if 10000 < count < 200000:
                                        self.logger.info(f"Found TRAC detention count: {count:,}")
                                        return count
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error scraping TRAC site: {e}")
            return None
    
    def _get_mock_data(self) -> Dict[str, Any]:
        """Return realistic mock detention data."""
        import random
        
        # Historical ranges:
        # Normal: 20,000-35,000
        # Elevated: 35,000-50,000  
        # High: 50,000-80,000
        # Surge: 80,000-150,000
        
        rand = random.random()
        if rand < 0.5:  # 50% normal
            count = random.randint(20000, 35000)
        elif rand < 0.8:  # 30% elevated
            count = random.randint(35000, 50000)
        elif rand < 0.95:  # 15% high
            count = random.randint(50000, 80000)
        else:  # 5% surge
            count = random.randint(80000, 150000)
        
        capacity_pct = (count / 40000) * 100
        
        return {
            'value': count,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'collector': self.name,
            'metadata': {
                'unit': 'detainees',
                'source': 'mock_data',
                'description': f'{count:,} total ICE detainees (mock)',
                'capacity_percentage': round(capacity_pct, 1),
                'typical_capacity': 40000,
                'data_type': 'mock'
            }
        }
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate ICE detention data."""
        if not data:
            return False
        
        value = data.get('value')
        return isinstance(value, int) and 0 <= value <= 500000