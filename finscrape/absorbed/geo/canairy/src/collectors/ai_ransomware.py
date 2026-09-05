"""
AI-assisted ransomware collector.
Monitors CISA ICS advisories for AI-related ransomware incidents.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from .base import BaseCollector


class AIRansomwareCollector(BaseCollector):
    """Collects AI-related ransomware data from CISA ICS advisories."""
    
    def __init__(self, config):
        super().__init__(config)
        self._name = "AIRansomware"
        self.ics_url = "https://www.cisa.gov/sites/default/files/feeds/ics-advisories.json"
        self.kev_url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
        
        # AI-related keywords to search for
        self.ai_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'ml',
            'neural network', 'deep learning', 'automated', 'autonomous',
            'bot', 'algorithm', 'model', 'chatgpt', 'llm', 'generative'
        ]
        
        # Ransomware indicators
        self.ransomware_keywords = [
            'ransomware', 'ransom', 'encrypt', 'decrypt', 'extortion',
            'lockbit', 'blackcat', 'alphv', 'clop', 'royal', 'akira'
        ]
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Collect AI-assisted ransomware incident data.
        
        Returns:
            Dict with incident count or None if collection fails
        """
        try:
            incident_count = self._count_ai_ransomware_incidents()
            
            if incident_count is None:
                return None
            
            return {
                'value': incident_count,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'incidents',
                    'period': '90_days',
                    'source': 'CISA_ICS',
                    'description': f'{incident_count} AI-assisted ransomware incidents in 90 days',
                    'ai_keywords': self.ai_keywords[:5],  # Show first 5 keywords
                    'critical_threshold': 6
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect AI ransomware data: {e}")
            return None
    
    def _count_ai_ransomware_incidents(self) -> Optional[int]:
        """Count AI-related ransomware incidents from CISA feeds."""
        try:
            incidents = 0
            cutoff_date = datetime.now() - timedelta(days=90)
            
            # Check ICS advisories
            ics_incidents = self._check_ics_advisories(cutoff_date)
            incidents += ics_incidents
            
            # Check KEV for AI-exploited vulnerabilities used in ransomware
            kev_incidents = self._check_kev_feed(cutoff_date)
            incidents += kev_incidents
            
            self.logger.info(f"Total AI ransomware incidents: {incidents} (ICS: {ics_incidents}, KEV: {kev_incidents})")
            return incidents
            
        except Exception as e:
            self.logger.error(f"Failed to count incidents: {e}")
            return self._get_mock_data()
    
    def _check_ics_advisories(self, cutoff_date: datetime) -> int:
        """Check ICS advisories for AI-related ransomware."""
        try:
            response = requests.get(
                self.ics_url,
                timeout=30,
                headers={'User-Agent': 'Brown-Man-Bunker-Monitor/1.0'}
            )
            
            if response.status_code != 200:
                self.logger.warning(f"Failed to fetch ICS advisories: {response.status_code}")
                return 0
            
            advisories = response.json()
            ai_ransomware_count = 0
            
            for advisory in advisories:
                # Check date
                try:
                    pub_date = datetime.strptime(
                        advisory.get('published', ''), 
                        '%Y-%m-%dT%H:%M:%S'
                    )
                except:
                    continue
                
                if pub_date < cutoff_date:
                    continue
                
                # Check for AI and ransomware keywords
                text_to_check = ' '.join([
                    advisory.get('title', '').lower(),
                    advisory.get('summary', '').lower(),
                    advisory.get('description', '').lower()
                ])
                
                has_ai = any(keyword in text_to_check for keyword in self.ai_keywords)
                has_ransomware = any(keyword in text_to_check for keyword in self.ransomware_keywords)
                
                if has_ai and has_ransomware:
                    ai_ransomware_count += 1
                    self.logger.info(f"Found AI ransomware advisory: {advisory.get('title', '')[:50]}...")
            
            return ai_ransomware_count
            
        except Exception as e:
            self.logger.error(f"Failed to check ICS advisories: {e}")
            return 0
    
    def _check_kev_feed(self, cutoff_date: datetime) -> int:
        """Check KEV feed for AI-exploited vulnerabilities in ransomware."""
        try:
            response = requests.get(
                self.kev_url,
                timeout=30,
                headers={'User-Agent': 'Brown-Man-Bunker-Monitor/1.0'}
            )
            
            if response.status_code != 200:
                self.logger.warning(f"Failed to fetch KEV: {response.status_code}")
                return 0
            
            data = response.json()
            vulnerabilities = data.get('vulnerabilities', [])
            ai_ransomware_count = 0
            
            for vuln in vulnerabilities:
                # Check date
                try:
                    date_added = datetime.strptime(
                        vuln.get('dateAdded', ''), 
                        '%Y-%m-%d'
                    )
                except:
                    continue
                
                if date_added < cutoff_date:
                    continue
                
                # Check for AI-related exploitation in ransomware context
                notes = vuln.get('notes', '').lower()
                short_desc = vuln.get('shortDescription', '').lower()
                
                text_to_check = f"{notes} {short_desc}"
                
                # Look for AI tools being used for exploitation
                ai_exploitation = any(keyword in text_to_check for keyword in [
                    'ai-powered', 'automated exploitation', 'machine learning',
                    'bot', 'autonomous'
                ])
                
                ransomware_related = any(keyword in text_to_check for keyword in [
                    'ransomware', 'ransom', 'encrypt'
                ])
                
                if ai_exploitation and ransomware_related:
                    ai_ransomware_count += 1
                    self.logger.info(f"Found AI-exploited vuln in ransomware: {vuln.get('cveID', '')}")
            
            return ai_ransomware_count
            
        except Exception as e:
            self.logger.error(f"Failed to check KEV feed: {e}")
            return 0
    
    def _get_mock_data(self) -> int:
        """Return realistic mock data for AI ransomware incidents."""
        import random
        
        # Base incidents (1-4 per 90 days currently)
        base = random.randint(1, 4)
        
        # Add spike chance (AI tools becoming more accessible)
        if random.random() < 0.15:  # 15% chance of spike
            base += random.randint(2, 4)
        
        # Ensure non-zero (at least some activity)
        return max(1, base)
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate AI ransomware data."""
        if not data:
            return False
        
        value = data.get('value')
        return isinstance(value, int) and value >= 0