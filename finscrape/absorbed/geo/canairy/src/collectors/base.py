"""
Base collector class that all data collectors must inherit from.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
from datetime import datetime


class BaseCollector(ABC):
    """Abstract base class for all data collectors."""
    
    def __init__(self, config):
        """
        Initialize the collector with configuration.
        
        Args:
            config: Configuration object containing collector settings
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._name = self.__class__.__name__.replace('Collector', '')
        
    @property
    def name(self) -> str:
        """Get the collector name."""
        return self._name
        
    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """
        Collect data from the source.
        
        Returns:
            Dict containing the collected data with at least:
            - value: The primary metric value
            - timestamp: When the data was collected
            - metadata: Additional context about the data
        """
        pass
        
    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate the collected data.
        
        Args:
            data: The data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        pass
        
    def get_cache_key(self) -> str:
        """Generate a cache key for this collector."""
        return f"collector_{self.name.lower()}_data"
        
    def format_reading(self, data: Dict[str, Any]) -> str:
        """
        Format the data reading for display.
        
        Args:
            data: The collected data
            
        Returns:
            Formatted string representation
        """
        value = data.get('value', 'N/A')
        return f"{value}"
        
    def _create_reading(self, value: Any, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create a standardized reading structure.
        
        Args:
            value: The primary metric value
            metadata: Optional additional context
            
        Returns:
            Standardized reading dictionary
        """
        return {
            'value': value,
            'timestamp': datetime.utcnow().isoformat(),
            'collector': self.name,
            'metadata': metadata or {}
        }