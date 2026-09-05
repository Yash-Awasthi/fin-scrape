"""
State Department Travel Advisory Collector
Fetches travel advisories from State Department.
Free RSS: https://travel.state.gov/
"""

import requests
from typing import Any, Dict, List
from datetime import datetime, timedelta
import logging
import xml.etree.ElementTree as ET
from .base import BaseCollector

logger = logging.getLogger(__name__)


class StateDeptAdvisoryCollector(BaseCollector):
    """Collector for State Department travel advisories."""

    RSS_URL = "https://travel.state.gov/_res/rss/TAsTWs.xml"
    ADVISORIES_URL = "https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories.html"

    def __init__(self, config=None):
        super().__init__(config or {})

    def collect(self) -> Dict[str, Any]:
        """Fetch travel advisory counts by level."""
        try:
            response = requests.get(self.RSS_URL, timeout=15)

            if response.status_code == 200:
                root = ET.fromstring(response.content)

                advisories = {
                    'level_4': [],  # Do Not Travel
                    'level_3': [],  # Reconsider Travel
                    'level_2': [],  # Exercise Increased Caution
                    'level_1': []   # Exercise Normal Precautions
                }

                recent_changes = []
                thirty_days_ago = datetime.now() - timedelta(days=30)

                for item in root.findall('.//item'):
                    title = item.find('title')
                    description = item.find('description')
                    pub_date = item.find('pubDate')

                    if title is not None:
                        title_text = title.text or ''

                        # Parse advisory level from title
                        if 'Level 4' in title_text or 'Do Not Travel' in title_text:
                            advisories['level_4'].append(title_text)
                        elif 'Level 3' in title_text or 'Reconsider' in title_text:
                            advisories['level_3'].append(title_text)
                        elif 'Level 2' in title_text:
                            advisories['level_2'].append(title_text)
                        else:
                            advisories['level_1'].append(title_text)

                        # Track recent changes
                        if pub_date is not None:
                            try:
                                pub_datetime = datetime.strptime(
                                    pub_date.text[:25],
                                    '%a, %d %b %Y %H:%M:%S'
                                )
                                if pub_datetime > thirty_days_ago:
                                    recent_changes.append({
                                        'title': title_text,
                                        'date': pub_date.text
                                    })
                            except:
                                pass

                # Score based on Level 4 count (most critical)
                level_4_count = len(advisories['level_4'])

                return self._create_reading(
                    value=level_4_count,
                    metadata={
                        'level_4_count': level_4_count,
                        'level_3_count': len(advisories['level_3']),
                        'level_2_count': len(advisories['level_2']),
                        'level_1_count': len(advisories['level_1']),
                        'recent_changes_30d': len(recent_changes),
                        'level_4_countries': advisories['level_4'][:10],
                        'source': 'State Department Travel Advisories',
                        'source_url': self.ADVISORIES_URL
                    }
                )

            return self._get_fallback()

        except Exception as e:
            logger.error(f"State Dept advisory collection failed: {e}")
            return self._get_fallback()

    def _get_fallback(self) -> Dict[str, Any]:
        """Fallback advisory count."""
        return self._create_reading(
            value=20,
            metadata={
                'source': 'Estimated',
                'note': 'Typical Level 4 count is ~20 countries'
            }
        )

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate advisory data."""
        value = data.get('value')
        return value is not None and 0 <= value <= 200


class PassportWaitCollector(BaseCollector):
    """Collector for passport processing wait times."""

    PASSPORT_URL = "https://travel.state.gov/content/travel/en/passports/how-apply/processing-times.html"

    def __init__(self, config=None):
        super().__init__(config or {})

    def collect(self) -> Dict[str, Any]:
        """Fetch passport processing wait times."""
        try:
            response = requests.get(self.PASSPORT_URL, timeout=15)

            if response.status_code == 200:
                text = response.text.lower()

                # Parse for processing times
                import re

                # Look for "X to Y weeks" patterns
                pattern = r'(\d+)\s*(?:to|-)\s*(\d+)\s*weeks'
                matches = re.findall(pattern, text)

                if matches:
                    # Get the longest wait time mentioned
                    max_weeks = max(int(m[1]) for m in matches)

                    return self._create_reading(
                        value=max_weeks,
                        metadata={
                            'unit': 'weeks',
                            'processing_ranges': matches[:5],
                            'source': 'State Department Passport Services',
                            'source_url': self.PASSPORT_URL
                        }
                    )

            return self._create_reading(value=8, metadata={'source': 'Estimated'})

        except Exception as e:
            logger.error(f"Passport wait collection failed: {e}")
            return self._create_reading(value=8, metadata={'source': 'Error fallback'})

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate passport wait data."""
        value = data.get('value')
        return value is not None and 0 <= value <= 52
