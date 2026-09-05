"""
ICE detention capacity collector.

Monitors Immigration and Customs Enforcement detention bed utilization
as an indicator of policy enforcement intensity.
"""

from typing import Dict, Any
from .base import BaseCollector

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class ICEDetentionCollector(BaseCollector):
    """Collects ICE detention facility utilization data."""
    
    def __init__(self, config):
        """Initialize the ICE detention collector."""
        super().__init__(config)
        self.threshold_amber = 80  # 80% capacity
        self.threshold_red = 90    # 90% capacity
        self.total_capacity = 34000  # Approximate total ICE bed capacity
        
    def collect(self) -> Dict[str, Any]:
        """
        Collect ICE detention utilization data.
        
        Returns:
            Dictionary with utilization percentage
        """
        try:
            # Mock data for now
            # In production, this would scrape ICE reports or use FOIA data
            current_detained = 25500
            utilization_pct = (current_detained / self.total_capacity) * 100
            
            self.logger.info(f"ICE detention utilization: {utilization_pct:.1f}%")
            
            return self._create_reading(
                value=utilization_pct,
                metadata={
                    'unit': 'percent',
                    'detained_count': current_detained,
                    'total_capacity': self.total_capacity,
                    'threshold_amber': self.threshold_amber,
                    'threshold_red': self.threshold_red
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to collect ICE detention data: {e}")
            raise
            
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate the collected ICE detention data."""
        if not data or 'value' not in data:
            return False
            
        value = data['value']
        
        # Utilization should be between 0 and 100 percent
        if not isinstance(value, (int, float)) or value < 0 or value > 100:
            self.logger.warning(f"Invalid utilization percentage: {value}")
            return False
            
        return True
        
    def format_reading(self, data: Dict[str, Any]) -> str:
        """Format the utilization reading for display."""
        value = data.get('value', 0)
        detained = data.get('metadata', {}).get('detained_count', 0)
        return f"{value:.1f}% ({detained:,} detained)"