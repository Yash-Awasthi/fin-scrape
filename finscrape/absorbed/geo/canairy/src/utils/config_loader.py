"""
Configuration loader for the monitoring system.

Handles loading and validation of YAML configuration files.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class ConfigLoader:
    """Loads and manages system configuration."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the configuration loader.
        
        Args:
            config_path: Path to the main configuration file
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.secrets = self._load_secrets()
        self._merge_secrets_into_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load the main configuration file."""
        if not HAS_YAML:
            self.logger.warning("PyYAML not installed. Using default configuration.")
            return self._get_default_config()
            
        if not self.config_path.exists():
            self.logger.warning(f"Config file not found: {self.config_path}")
            return self._get_default_config()
            
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                self.logger.info(f"Loaded configuration from {self.config_path}")
                return config or {}
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return self._get_default_config()
            
    def _load_secrets(self) -> Dict[str, Any]:
        """Load secrets from environment or secrets file."""
        secrets = {}
        
        # Try to load from secrets.yaml if it exists
        if HAS_YAML:
            secrets_path = self.config_path.parent / "secrets.yaml"
            if secrets_path.exists():
                try:
                    with open(secrets_path, 'r') as f:
                        secrets = yaml.safe_load(f) or {}
                        self.logger.info("Loaded secrets from secrets.yaml")
                except Exception as e:
                    self.logger.warning(f"Failed to load secrets file: {e}")
        
        # Override with environment variables if present
        env_mappings = {
            'TELEGRAM_BOT_TOKEN': 'notifications.telegram.bot_token',
            'TELEGRAM_CHAT_ID': 'notifications.telegram.chat_id',
            'SMTP_PASSWORD': 'notifications.email.smtp_password',
            'FRED_API_KEY': 'fred_api_key',
            'NEWS_API_KEY': 'news_api_key',
            'ALPHA_VANTAGE_API_KEY': 'alpha_vantage_key',
            'ALPHA_VANTAGE_KEY': 'alpha_vantage_key',
            'LEGISCAN_API_KEY': 'api_keys.legiscan',
            'CONGRESS_API_KEY': 'api_keys.congress',
            'BLS_API_KEY': 'api_keys.bls',
        }
        
        for env_var, config_key in env_mappings.items():
            if env_var in os.environ:
                self._set_nested(secrets, config_key, os.environ[env_var])
                
        return secrets
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            'monitoring': {
                'interval_minutes': 60,
                'retention_days': 30,
            },
            'collectors': {
                'enabled': ['treasury', 'ice_detention', 'taiwan_zone', 
                           'hormuz_risk', 'dod_autonomy', 'mbridge'],
                'timeout_seconds': 30,
            },
            'notifications': {
                'enabled': True,
                'channels': ['console'],
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/monitor.log',
            }
        }
        
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'monitoring.interval_minutes')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            value = self.config
            for part in key.split('.'):
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default
            
    def get_secret(self, key: str, default: Any = None) -> Any:
        """
        Get a secret value using dot notation.
        
        Args:
            key: Secret key (e.g., 'notifications.telegram.bot_token')
            default: Default value if key not found
            
        Returns:
            Secret value or default
        """
        try:
            value = self.secrets
            for part in key.split('.'):
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default
            
    def _set_nested(self, dict_obj: Dict, key: str, value: Any):
        """Set a nested dictionary value using dot notation."""
        keys = key.split('.')
        for k in keys[:-1]:
            dict_obj = dict_obj.setdefault(k, {})
        dict_obj[keys[-1]] = value
        
    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access to configuration."""
        return self.get(key)
    
    def get_trip_wire_config(self, name: str) -> Dict[str, Any]:
        """Get configuration for a specific trip-wire."""
        return self.config.get('trip_wires', {}).get(name, {})
    
    def get_alert_config(self) -> Dict[str, Any]:
        """Get alert configuration."""
        return self.config.get('alerts', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        return self.config.get('monitoring', {})
    
    def get_secrets(self) -> Dict[str, Any]:
        """Get secrets configuration."""
        return self.secrets
    
    def _merge_secrets_into_config(self):
        """Merge secrets into main configuration."""
        # Merge API keys
        if 'api_keys' in self.secrets:
            if 'api_keys' not in self.config:
                self.config['api_keys'] = {}
            self.config['api_keys'].update(self.secrets['api_keys'])
        
        # Merge other keys at root level
        for key in ['fred_api_key', 'news_api_key', 'alpha_vantage_key']:
            if key in self.secrets:
                self.config[key] = self.secrets[key]