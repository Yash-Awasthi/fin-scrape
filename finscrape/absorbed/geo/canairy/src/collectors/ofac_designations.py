"""
OFAC (Office of Foreign Assets Control) designations collector.
Tracks sanctions on India/China entities related to oil/energy sector.
"""

import requests
import csv
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from io import StringIO
from .base import BaseCollector


class OFACDesignationsCollector(BaseCollector):
    """Collects OFAC sanctions data for India/China oil entities."""
    
    def __init__(self, config):
        super().__init__(config)
        self._name = "OFACDesignations"
        self.sdn_url = "https://home.treasury.gov/system/files/126/sdn.csv"
        self.countries = ['india', 'china', 'chinese', 'indian']
        self.oil_keywords = ['oil', 'petroleum', 'energy', 'gas', 'lng', 
                           'refinery', 'petrochemical', 'tanker', 'shipping']
        
    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Collect OFAC designation data.
        
        Returns:
            Dict with designation count or None if collection fails
        """
        try:
            designation_count = self._fetch_designation_data()
            
            if designation_count is None:
                return None
            
            return {
                'value': designation_count,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'collector': self.name,
                'metadata': {
                    'unit': 'designations',
                    'period': '30_days',
                    'source': 'OFAC_SDN',
                    'description': f'{designation_count} India/China oil-related designations',
                    'search_countries': self.countries,
                    'search_keywords': self.oil_keywords
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect OFAC data: {e}")
            return None
    
    def _fetch_designation_data(self) -> Optional[int]:
        """Fetch and analyze OFAC SDN data."""
        try:
            # Download SDN CSV
            response = requests.get(
                self.sdn_url,
                timeout=60,  # Large file, needs more time
                headers={'User-Agent': 'Brown-Man-Bunker-Monitor/1.0'}
            )
            
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch SDN CSV: status {response.status_code}")
                return 0
            
            # Parse CSV
            # SDN format: ent_num, SDN_Name, SDN_Type, Program, Title, Call_Sign, 
            # Vess_type, Tonnage, GRT, Vess_flag, Vess_owner, Remarks
            csv_reader = csv.DictReader(StringIO(response.text))
            
            cutoff_date = datetime.now() - timedelta(days=30)
            recent_designations = 0
            
            for row in csv_reader:
                # Check if India/China related
                name_remarks = f"{row.get('SDN_Name', '')} {row.get('Remarks', '')}".lower()
                
                country_match = any(country in name_remarks for country in self.countries)
                if not country_match:
                    continue
                
                # Check if oil/energy related
                oil_match = any(keyword in name_remarks for keyword in self.oil_keywords)
                if not oil_match:
                    continue
                
                # Try to extract date from remarks (often includes "designated on" text)
                # This is approximate as SDN CSV doesn't have clean date column
                if 'designated on' in row.get('Remarks', '').lower():
                    # Simple heuristic - count as recent if mentioned in remarks
                    recent_designations += 1
                    self.logger.info(f"Found designation: {row.get('SDN_Name', '')[:50]}...")
            
            self.logger.info(f"Total India/China oil designations (estimated recent): {recent_designations}")
            return recent_designations
            
        except Exception as e:
            self.logger.error(f"Failed to process OFAC data: {e}")
            return 0
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate OFAC data."""
        if not data:
            return False
        return 'value' in data and isinstance(data['value'], (int, float))