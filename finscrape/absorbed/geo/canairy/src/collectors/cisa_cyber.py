"""
CISA Cyber Threat collector for monitoring critical vulnerabilities.
Tracks Known Exploited Vulnerabilities (KEV) from CISA.

Green: ≤2 significant bulletins in 90 days
Amber: 3-5 bulletins
Red: >5 bulletins
"""

from typing import Dict, Any, Optional
import requests
import logging
from datetime import datetime, timedelta
from .base import BaseCollector

class CISACyberCollector(BaseCollector):
    """Collects CISA Known Exploited Vulnerabilities data."""
    
    def __init__(self, config):
        super().__init__(config)
        self._name = "CISA Cyber Threats"
        self.logger = logging.getLogger(__name__)
        
    def collect(self) -> Dict[str, Any]:
        """Collect CISA KEV data for last 90 days."""
        try:
            # Fetch from CISA KEV feed
            kev_data = self._fetch_cisa_kev()
            
            if kev_data:
                return {
                    'name': self.name,
                    'value': kev_data['count_90_days'],
                    'metadata': {
                        'unit': 'vulnerabilities',
                        'source': 'CISA_KEV',
                        'description': f'{kev_data["count_90_days"]} critical vulnerabilities in last 90 days',
                        'total_kevs': kev_data['total_kevs'],
                        'latest_kev': kev_data.get('latest_kev', 'N/A'),
                        'data_source': 'LIVE'
                    }
                }
            else:
                # Fallback to mock data
                return self._get_mock_data()
                
        except Exception as e:
            self.logger.error(f"Failed to collect CISA data: {e}")
            return self._get_mock_data()
    
    def _fetch_cisa_kev(self) -> Optional[Dict[str, Any]]:
        """Fetch Known Exploited Vulnerabilities from CISA."""
        try:
            url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                vulnerabilities = data.get('vulnerabilities', [])
                
                # Count vulnerabilities from last 90 days
                ninety_days_ago = datetime.now() - timedelta(days=90)
                recent_kevs = []
                
                for vuln in vulnerabilities:
                    # Parse date added
                    date_added_str = vuln.get('dateAdded', '')
                    try:
                        date_added = datetime.strptime(date_added_str, '%Y-%m-%d')
                        if date_added >= ninety_days_ago:
                            recent_kevs.append(vuln)
                    except:
                        continue
                
                # Get latest KEV info
                latest_kev = None
                if recent_kevs:
                    latest = recent_kevs[0]
                    latest_kev = f"{latest.get('cveID', 'Unknown')}: {latest.get('vulnerabilityName', 'Unknown')}"
                
                return {
                    'count_90_days': len(recent_kevs),
                    'total_kevs': len(vulnerabilities),
                    'latest_kev': latest_kev,
                    'recent_kevs': recent_kevs[:5]  # Top 5 for reference
                }
            
            self.logger.warning("CISA KEV feed returned no data")
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching CISA data: {e}")
            return None
    
    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock CISA cyber threat data."""
        # Typical scenario - 4 KEVs (amber range)
        mock_value = 4
        
        return {
            'name': self.name,
            'value': mock_value,
            'metadata': {
                'unit': 'vulnerabilities',
                'source': 'Mock data - CISA feed unavailable',
                'description': f'{mock_value} critical vulnerabilities (mock)',
                'data_source': 'MOCK'
            }
        }
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate CISA cyber threat data."""
        if not data or 'value' not in data:
            return False
            
        value = data['value']
        
        # KEV count should be reasonable (0-100 in 90 days)
        if not isinstance(value, (int, float)) or value < 0 or value > 100:
            self.logger.warning(f"Invalid CISA KEV count: {value}")
            return False
            
        return True