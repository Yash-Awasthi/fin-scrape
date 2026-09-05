"""
Stale Data Handler for Brown Man Bunker.
Handles automatic coloring of stale data based on age.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging


class StaleDataHandler:
    """Manages stale data detection and automatic threat level adjustments."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Get stale thresholds from config
        monitoring_config = config.config.get('monitoring', {})
        stale_config = monitoring_config.get('stale_thresholds', {})
        
        self.amber_hours = stale_config.get('amber_hours', 48)
        self.red_hours = stale_config.get('red_hours', 168)  # 7 days
    
    def check_staleness(self, reading: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check if data is stale and adjust threat level accordingly.
        
        Args:
            reading: Data reading with timestamp
            
        Returns:
            Updated reading with stale status
        """
        if not reading:
            # No data is automatically red
            return {
                'value': 'NO DATA',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'metadata': {
                    'stale': True,
                    'stale_reason': 'no_data',
                    'force_level': 'red'
                }
            }
        
        # Check timestamp
        try:
            if 'timestamp' in reading:
                timestamp_str = reading['timestamp'].replace('Z', '+00:00')
                data_time = datetime.fromisoformat(timestamp_str)
            else:
                # No timestamp means stale
                reading['metadata'] = reading.get('metadata', {})
                reading['metadata']['stale'] = True
                reading['metadata']['stale_reason'] = 'no_timestamp'
                reading['metadata']['force_level'] = 'red'
                return reading
            
            # Calculate age
            now = datetime.utcnow()
            age = now - data_time.replace(tzinfo=None)
            age_hours = age.total_seconds() / 3600
            
            # Update metadata
            metadata = reading.get('metadata', {})
            metadata['data_age_hours'] = round(age_hours, 1)
            
            # Check staleness thresholds
            if age_hours >= self.red_hours:
                metadata['stale'] = True
                metadata['stale_reason'] = f'stale>{self.red_hours/24:.0f}d'
                metadata['force_level'] = 'red'
                self.logger.warning(
                    f"Data stale (red): {reading.get('collector', 'unknown')} "
                    f"age={age_hours:.1f}h"
                )
            elif age_hours >= self.amber_hours:
                metadata['stale'] = True
                metadata['stale_reason'] = f'stale>{self.amber_hours}h'
                metadata['force_level'] = 'amber'
                self.logger.info(
                    f"Data stale (amber): {reading.get('collector', 'unknown')} "
                    f"age={age_hours:.1f}h"
                )
            else:
                metadata['stale'] = False
                metadata.pop('stale_reason', None)
                metadata.pop('force_level', None)
            
            reading['metadata'] = metadata
            return reading
            
        except Exception as e:
            self.logger.error(f"Failed to check staleness: {e}")
            reading['metadata'] = reading.get('metadata', {})
            reading['metadata']['stale'] = True
            reading['metadata']['stale_reason'] = 'parse_error'
            reading['metadata']['force_level'] = 'red'
            return reading
    
    def apply_stale_level(self, threat_level: str, metadata: Dict[str, Any]) -> str:
        """
        Apply stale data forced level if applicable.
        
        Args:
            threat_level: Original threat level
            metadata: Metadata including stale status
            
        Returns:
            Updated threat level
        """
        if metadata.get('stale') and 'force_level' in metadata:
            forced_level = metadata['force_level']
            self.logger.debug(
                f"Forcing level due to staleness: {threat_level} → {forced_level}"
            )
            return forced_level
        
        return threat_level
    
    def process_indicator(self, collector_name: str, reading: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process an indicator reading to check for staleness.
        
        Args:
            collector_name: Name of the collector (for logging)
            reading: Data reading with timestamp
            
        Returns:
            Updated reading with stale status
        """
        if reading and 'collector' not in reading:
            # Add collector name to reading for better logging
            reading['collector'] = collector_name
        return self.check_staleness(reading)