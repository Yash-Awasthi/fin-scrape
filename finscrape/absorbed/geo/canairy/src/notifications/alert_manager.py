"""
Alert manager for sending notifications through various channels.

Supports console output, email, Telegram, and other notification methods.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import json
from pathlib import Path
from .email_notifier import EmailNotifier


class AlertManager:
    """Manages alert notifications across multiple channels."""
    
    def __init__(self, config):
        """
        Initialize the alert manager.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.enabled = config.get('notifications.enabled', True)
        self.channels = config.get('notifications.channels', ['console'])
        
        # Initialize notification channels
        self._init_channels()
        
    def _init_channels(self):
        """Initialize configured notification channels."""
        self.notifiers = {}
        
        if 'console' in self.channels:
            self.notifiers['console'] = ConsoleNotifier()
            
        if 'file' in self.channels:
            self.notifiers['file'] = FileNotifier(self.config)
            
        if 'email' in self.channels:
            self.notifiers['email'] = EmailNotifier(self.config)
        
    def send_tighten_up_alert(self, threat_levels: Dict[str, str], 
                            readings: Dict[str, Any]):
        """
        Send TIGHTEN-UP condition alert.
        
        Args:
            threat_levels: Current threat levels by collector
            readings: Current readings from all collectors
        """
        if not self.enabled:
            return
            
        # Count red alerts
        red_alerts = [(name, level) for name, level in threat_levels.items() 
                     if level == "red"]
        
        alert_data = {
            'type': 'TIGHTEN_UP',
            'severity': 'CRITICAL',
            'timestamp': datetime.utcnow().isoformat(),
            'red_count': len(red_alerts),
            'red_indicators': red_alerts,
            'threat_levels': threat_levels,
            'readings': self._format_readings(readings),
            'actions': [
                "Top off fuel & cash reserves",
                "Charge all power banks and devices",
                "Conduct family group briefing",
                "Review trusted OSINT information feeds"
            ]
        }
        
        self._send_to_channels(alert_data)
        
    def send_status_update(self, threat_levels: Dict[str, str], 
                         readings: Dict[str, Any]):
        """
        Send regular status update.
        
        Args:
            threat_levels: Current threat levels by collector
            readings: Current readings from all collectors
        """
        if not self.enabled:
            return
            
        alert_data = {
            'type': 'STATUS_UPDATE',
            'severity': 'INFO',
            'timestamp': datetime.utcnow().isoformat(),
            'threat_levels': threat_levels,
            'readings': self._format_readings(readings)
        }
        
        self._send_to_channels(alert_data)
        
    def send_error_alert(self, error_message: str, collector: Optional[str] = None):
        """
        Send error alert.
        
        Args:
            error_message: Error message
            collector: Name of collector that failed (optional)
        """
        if not self.enabled:
            return
            
        alert_data = {
            'type': 'ERROR',
            'severity': 'WARNING',
            'timestamp': datetime.utcnow().isoformat(),
            'error': error_message,
            'collector': collector
        }
        
        self._send_to_channels(alert_data)
        
    def _send_to_channels(self, alert_data: Dict[str, Any]):
        """Send alert to all configured channels."""
        for channel_name, notifier in self.notifiers.items():
            try:
                notifier.send(alert_data)
                self.logger.debug(f"Alert sent to {channel_name}")
            except Exception as e:
                self.logger.error(f"Failed to send alert to {channel_name}: {e}")
                
    def _format_readings(self, readings: Dict[str, Any]) -> Dict[str, Any]:
        """Format readings for notification."""
        formatted = {}
        for name, reading in readings.items():
            if reading and isinstance(reading, dict):
                formatted[name] = {
                    'value': reading.get('value'),
                    'timestamp': reading.get('timestamp'),
                    'formatted': reading.get('formatted', str(reading.get('value')))
                }
            else:
                formatted[name] = {'value': None, 'error': 'No data'}
        return formatted


class ConsoleNotifier:
    """Console notification handler."""
    
    def send(self, alert_data: Dict[str, Any]):
        """Print alert to console."""
        alert_type = alert_data['type']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if alert_type == 'TIGHTEN_UP':
            print("\n" + "🚨" * 20)
            print(f"*** TIGHTEN-UP ALERT - {timestamp} ***")
            print(f"Red Alerts: {alert_data['red_count']}")
            print("Red Indicators:")
            for name, _ in alert_data['red_indicators']:
                value = alert_data['readings'].get(name, {}).get('formatted', 'N/A')
                print(f"  - {name}: {value}")
            print("\nREQUIRED ACTIONS:")
            for action in alert_data['actions']:
                print(f"  ✓ {action}")
            print("🚨" * 20 + "\n")
        elif alert_type == 'ERROR':
            print(f"\n⚠️  ERROR - {timestamp}")
            print(f"Collector: {alert_data.get('collector', 'Unknown')}")
            print(f"Error: {alert_data['error']}\n")


class FileNotifier:
    """File-based notification handler."""
    
    def __init__(self, config):
        """Initialize file notifier."""
        self.alert_dir = Path("alerts")
        self.alert_dir.mkdir(exist_ok=True)
        
    def send(self, alert_data: Dict[str, Any]):
        """Save alert to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        alert_type = alert_data['type'].lower()
        filename = self.alert_dir / f"{alert_type}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(alert_data, f, indent=2, default=str)