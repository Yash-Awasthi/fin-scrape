"""
mBridge CBDC collector.

Monitors the mBridge multi-CBDC platform adoption and transaction volumes
as an indicator of USD hegemony challenges.
"""

from typing import Dict, Any
from .base import BaseCollector

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class MBridgeCollector(BaseCollector):
    """Collects mBridge CBDC platform data."""
    
    def __init__(self, config):
        """Initialize the mBridge collector."""
        super().__init__(config)
        self.threshold_amber = 50    # $50B monthly volume
        self.threshold_red = 100     # $100B monthly volume
        
    def collect(self) -> Dict[str, Any]:
        """
        Collect mBridge transaction volume data.
        
        Returns:
            Dictionary with monthly transaction volume in billions USD
        """
        try:
            # Mock data for now
            # In production, this would aggregate CBDC platform reports
            monthly_volume = 15.5  # $15.5B monthly volume
            
            self.logger.info(f"mBridge monthly volume: ${monthly_volume}B")
            
            return self._create_reading(
                value=monthly_volume,
                metadata={
                    'unit': 'billions_usd',
                    'period': 'monthly',
                    'participants': ['China', 'UAE', 'Thailand', 'Hong Kong'],
                    'threshold_amber': self.threshold_amber,
                    'threshold_red': self.threshold_red
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to collect mBridge data: {e}")
            raise
            
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate the collected mBridge data."""
        if not data or 'value' not in data:
            return False
            
        value = data['value']
        
        # Volume should be non-negative
        if not isinstance(value, (int, float)) or value < 0:
            self.logger.warning(f"Invalid transaction volume: {value}")
            return False
            
        return True
        
    def format_reading(self, data: Dict[str, Any]) -> str:
        """Format the volume reading for display."""
        value = data.get('value', 0)
        return f"${value:.1f}B/month"