"""
Grid Outage collector for monitoring power infrastructure stability.
Tracks major outages (>50k customers) from DOE OE-417 reports.

Green: 0-1 major outages per quarter
Amber: 2 outages
Red: ≥3 outages
"""

from typing import Dict, Any, Optional, List
import requests
import logging
from datetime import datetime, timedelta
import csv
from io import StringIO
from .base import BaseCollector

class GridOutageCollector(BaseCollector):
    """Collects power grid outage data from DOE."""
    
    def __init__(self, config):
        super().__init__(config)
        self._name = "Grid Outages"
        self.logger = logging.getLogger(__name__)
        
    def collect(self) -> Dict[str, Any]:
        """Collect grid outage data for current quarter."""
        try:
            # Fetch from DOE OE-417
            outage_data = self._fetch_grid_outages()
            
            if outage_data:
                return {
                    'name': self.name,
                    'value': outage_data['major_outages_quarter'],
                    'metadata': {
                        'unit': 'outages',
                        'source': 'DOE_OE417',
                        'description': f'{outage_data["major_outages_quarter"]} major outages (>50k) this quarter',
                        'total_affected': outage_data.get('total_customers_affected', 0),
                        'largest_outage': outage_data.get('largest_outage', 'N/A'),
                        'data_source': 'LIVE'
                    }
                }
            else:
                # Fallback to mock data
                return self._get_mock_data()
                
        except Exception as e:
            self.logger.error(f"Failed to collect grid outage data: {e}")
            return self._get_mock_data()
    
    def _fetch_grid_outages(self) -> Optional[Dict[str, Any]]:
        """Fetch grid outage data from DOE OE-417 reports."""
        try:
            # DOE OE-417 annual summary CSV - try different URLs
            urls = [
                "https://www.oe.netl.doe.gov/OE417_annual_summary.csv",
                "https://www.oe.energy.gov/OE417_annual_summary.csv",
                "https://www.energy.gov/sites/default/files/OE417_annual_summary.csv"
            ]
            
            response = None
            for url in urls:
                try:
                    response = requests.get(url, timeout=15)
                    if response.status_code == 200:
                        break
                except:
                    continue
            
            if response and response.status_code == 200:
                # Parse CSV data
                csv_data = StringIO(response.text)
                reader = csv.DictReader(csv_data)
                
                # Get current quarter date range
                now = datetime.now()
                quarter_start = datetime(now.year, ((now.month-1)//3)*3+1, 1)
                
                major_outages = []
                total_customers = 0
                
                for row in reader:
                    try:
                        # Parse date
                        date_str = row.get('Date Event Began', '')
                        event_date = datetime.strptime(date_str.split()[0], '%m/%d/%Y')
                        
                        # Check if in current quarter
                        if event_date >= quarter_start:
                            # Parse number of customers affected
                            customers_str = row.get('Number of Customers Affected', '0')
                            customers = int(customers_str.replace(',', ''))
                            
                            # Major outage = >50,000 customers
                            if customers >= 50000:
                                major_outages.append({
                                    'date': event_date,
                                    'customers': customers,
                                    'state': row.get('Geographic Areas', 'Unknown'),
                                    'cause': row.get('Event Type', 'Unknown')
                                })
                                total_customers += customers
                    except:
                        continue
                
                # Find largest outage
                largest = None
                if major_outages:
                    largest = max(major_outages, key=lambda x: x['customers'])
                    largest_desc = f"{largest['state']}: {largest['customers']:,} customers"
                else:
                    largest_desc = "None"
                
                return {
                    'major_outages_quarter': len(major_outages),
                    'total_customers_affected': total_customers,
                    'largest_outage': largest_desc,
                    'outage_list': major_outages[:5]  # Top 5 for reference
                }
            
            self.logger.warning("DOE OE-417 data not available")
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching grid outage data: {e}")
            return None
    
    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock grid outage data."""
        # Typical scenario - 1 major outage (green)
        mock_value = 1
        
        return {
            'name': self.name,
            'value': mock_value,
            'metadata': {
                'unit': 'outages',
                'source': 'Mock data - DOE feed unavailable',
                'description': f'{mock_value} major outage this quarter (mock)',
                'data_source': 'MOCK'
            }
        }
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate grid outage data."""
        if not data or 'value' not in data:
            return False
            
        value = data['value']
        
        # Outage count should be reasonable (0-20 per quarter)
        if not isinstance(value, (int, float)) or value < 0 or value > 20:
            self.logger.warning(f"Invalid outage count: {value}")
            return False
            
        return True