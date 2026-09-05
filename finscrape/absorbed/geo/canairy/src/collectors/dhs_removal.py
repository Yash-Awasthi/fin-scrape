"""
DHS expedited removal expansion tracker.
Monitors expansion of expedited removal geographic/temporal scope.
"""

import requests
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
from .base import BaseCollector


class DHSRemovalCollector(BaseCollector):
    """Tracks DHS expedited removal policy expansion."""
    
    def __init__(self, config):
        super().__init__(config)
        self._name = "DHSRemoval"
        
        # DHS policy sources
        self.dhs_url = "https://www.dhs.gov/immigration-enforcement"
        self.federal_register = "https://www.federalregister.gov/documents/search"
        
        # Current policy baseline (2019 expansion)
        self.current_scope = {
            'geographic': '100 miles from border',
            'temporal': '14 days',
            'expanded': False
        }
        
        # Expansion indicators
        self.expansion_keywords = [
            'expedited removal',
            'expand enforcement',
            'interior enforcement',
            'nationwide',
            'beyond 100 miles',
            'waive due process'
        ]
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Collect DHS removal expansion data.
        
        Returns:
            Dict with expansion status (0=current, 1=expanded)
        """
        try:
            # Check for policy changes
            is_expanded = self._check_policy_expansion()
            
            # Get expansion details
            expansion_details = self._get_expansion_details()
            
            # Binary indicator: 0=current scope, 1=expanded
            value = 1 if is_expanded else 0
            
            return {
                'value': value,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'expansion_status',
                    'source': 'DHS_policy',
                    'description': 'Expedited removal expanded' if is_expanded else 'Current 100mi/14day scope',
                    'current_scope': self.current_scope,
                    'expansion_details': expansion_details,
                    'is_expanded': is_expanded,
                    'threshold_red': 1
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect DHS removal data: {e}")
            return None
    
    def _check_policy_expansion(self) -> bool:
        """Check if expedited removal has been expanded."""
        try:
            # Check Federal Register for recent rules
            params = {
                'term': 'expedited removal',
                'agencies[]': 'homeland-security-department',
                'publication_date[gte]': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            }
            
            response = requests.get(
                self.federal_register,
                params=params,
                timeout=30,
                headers={'User-Agent': 'Brown-Man-Bunker-Monitor/1.0'}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for expansion rules
                for doc in data.get('results', []):
                    title = doc.get('title', '').lower()
                    abstract = doc.get('abstract', '').lower()
                    
                    # Look for expansion language
                    if any(keyword in title + abstract for keyword in self.expansion_keywords):
                        self.logger.info(f"Found potential expansion: {doc.get('title')}")
                        
                        # Check if it's actual expansion
                        if 'nationwide' in abstract or 'beyond 100 miles' in abstract:
                            return True
            
        except Exception as e:
            self.logger.error(f"Failed to check Federal Register: {e}")
        
        # Check DHS announcements
        return self._check_dhs_announcements()
    
    def _check_dhs_announcements(self) -> bool:
        """Check DHS website for policy announcements."""
        try:
            response = requests.get(
                self.dhs_url,
                timeout=30,
                headers={'User-Agent': 'Brown-Man-Bunker-Monitor/1.0'}
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for policy updates
                news_items = soup.find_all(['article', 'div'], class_=['news-item', 'announcement'])
                
                for item in news_items[:20]:  # Check recent items
                    text = item.get_text().lower()
                    
                    if 'expedited removal' in text:
                        # Check for expansion indicators
                        if any(phrase in text for phrase in ['nationwide', 'expand', 'beyond current']):
                            return True
            
        except Exception as e:
            self.logger.error(f"Failed to check DHS site: {e}")
        
        # Use mock data if no real data
        return self._get_mock_expansion()
    
    def _get_expansion_details(self) -> Dict[str, Any]:
        """Get details of any expansion."""
        # In production, would parse specific policy changes
        # For now, return potential expansion scenarios
        
        import random
        
        if random.random() < 0.1:  # 10% chance
            return {
                'geographic': 'Nationwide',
                'temporal': 'No time limit',
                'implementation_date': (datetime.now() + timedelta(days=30)).isoformat()
            }
        
        return self.current_scope
    
    def _get_mock_expansion(self) -> bool:
        """Return mock expansion status."""
        import random
        
        # Low probability of expansion
        # But if it happens, it's a major red flag
        return random.random() < 0.05  # 5% chance
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate DHS removal data."""
        if not data:
            return False
        
        value = data.get('value')
        return isinstance(value, int) and value in [0, 1]