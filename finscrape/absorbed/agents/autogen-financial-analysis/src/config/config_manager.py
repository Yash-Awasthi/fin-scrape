"""
Configuration Manager
Dynamic configuration management with change monitoring
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ConfigWatcher:
    """Configuration change watcher"""
    key: str
    callback: Callable
    last_value: Any = None


class ConfigurationManager:
    """Configuration management system with dynamic updates"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.watchers: List[ConfigWatcher] = []
        self.logger = logging.getLogger(__name__)
        self._load_config()

    def _load_config(self):
        """Load configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    if self.config_path.suffix.lower() == '.yaml' or self.config_path.suffix.lower() == '.yml':
                        self.config = yaml.safe_load(f)
                    elif self.config_path.suffix.lower() == '.json':
                        self.config = json.load(f)
                    else:
                        raise ValueError(f"Unsupported config file format: {self.config_path.suffix}")

                # Override with environment variables
                self._load_environment_overrides()

                self.logger.info(f"Configuration loaded from {self.config_path}")
            else:
                self.logger.warning(f"Config file {self.config_path} not found, using defaults")
                self.config = self._get_default_config()
                self._save_config()

        except Exception as e:
            self.logger.error(f"Failed to load config: {str(e)}")
            self.config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "autogen": {
                "model": "gpt-4",
                "temperature": 0.1,
                "max_tokens": 8000,
                "top_p": 0.9,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.1,
                "max_consecutive_auto_reply": 20
            },
            "data_sources": {
                "yahoo_finance": {
                    "enabled": True,
                    "rate_limit": 100,
                    "timeout": 30
                },
                "alpha_vantage": {
                    "enabled": False,
                    "rate_limit": 5,
                    "timeout": 60
                }
            },
            "cache": {
                "redis": {
                    "url": "redis://localhost:6379",
                    "ttl": 3600
                }
            },
            "performance": {
                "max_workers": 10,
                "max_concurrent_requests": 50,
                "timeout": 300
            },
            "monitoring": {
                "enabled": True,
                "log_level": "INFO"
            },
            "security": {
                "encryption_enabled": True,
                "rate_limiting": True
            }
        }

    def _load_environment_overrides(self):
        """Load configuration overrides from environment variables"""
        env_mappings = {
            "OPENAI_API_KEY": ["api_keys", "openai"],
            "ALPHA_VANTAGE_API_KEY": ["api_keys", "alpha_vantage"],
            "QUANDL_API_KEY": ["api_keys", "quandl"],
            "DATABASE_URL": ["database", "url"],
            "REDIS_URL": ["cache", "redis", "url"],
            "LOG_LEVEL": ["monitoring", "log_level"],
            "MAX_WORKERS": ["performance", "max_workers"],
            "MAX_CONCURRENT_REQUESTS": ["performance", "max_concurrent_requests"],
            "ENABLE_REDIS": ["cache", "redis", "enabled"],
            "ENABLE_ALPHA_VANTAGE": ["data_sources", "alpha_vantage", "enabled"],
            "ENABLE_QUANDL": ["data_sources", "quandl", "enabled"]
        }

        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                converted_value = self._convert_env_value(value)
                self._set_nested_value(self.config, config_path, converted_value)
                self.logger.debug(f"Set {config_path} from environment variable {env_var}")

    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type"""
        # Try to convert to boolean
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'

        # Try to convert to integer
        try:
            return int(value)
        except ValueError:
            pass

        # Try to convert to float
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value

    def _set_nested_value(self, config: Dict, path: List[str], value: Any):
        """Set a nested value in the configuration"""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        try:
            keys = key.split('.')
            value = self.config
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value
        except Exception as e:
            self.logger.warning(f"Error getting config key '{key}': {str(e)}")
            return default

    def set(self, key: str, value: Any, save: bool = True):
        """Set configuration value using dot notation"""
        try:
            keys = key.split('.')
            config = self.config

            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]

            # Set the value
            old_value = config.get(keys[-1])
            config[keys[-1]] = value

            self.logger.info(f"Config updated: {key} = {value}")

            # Save configuration if requested
            if save:
                self._save_config()

            # Notify watchers
            self._notify_watchers(key, value, old_value)

        except Exception as e:
            self.logger.error(f"Error setting config key '{key}': {str(e)}")
            raise

    def _save_config(self):
        """Save configuration to file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(self.config, f, default_flow_style=False, indent=2)
                elif self.config_path.suffix.lower() == '.json':
                    json.dump(self.config, f, indent=2)
                else:
                    raise ValueError(f"Unsupported config file format: {self.config_path.suffix}")

            self.logger.debug(f"Configuration saved to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to save config: {str(e)}")

    def watch(self, key: str, callback: Callable):
        """Watch for configuration changes"""
        try:
            current_value = self.get(key)
            watcher = ConfigWatcher(
                key=key,
                callback=callback,
                last_value=current_value
            )
            self.watchers.append(watcher)
            self.logger.debug(f"Watching config key: {key}")
        except Exception as e:
            self.logger.error(f"Error watching config key '{key}': {str(e)}")

    def _notify_watchers(self, key: str, new_value: Any, old_value: Any):
        """Notify watchers of configuration changes"""
        for watcher in self.watchers:
            if key.startswith(watcher.key):
                try:
                    watcher.callback(key, new_value, old_value)
                    watcher.last_value = new_value
                    self.logger.debug(f"Notified watcher for key: {key}")
                except Exception as e:
                    self.logger.error(f"Error in config watcher callback for key '{key}': {str(e)}")

    def unwatch(self, key: str):
        """Stop watching a configuration key"""
        self.watchers = [w for w in self.watchers if not key.startswith(w.key)]
        self.logger.debug(f"Stopped watching config key: {key}")

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration"""
        return self.config.copy()

    def reload(self):
        """Reload configuration from file"""
        old_config = self.config.copy()
        self._load_config()

        # Check for changes and notify watchers
        self._check_config_changes(old_config, self.config)

    def _check_config_changes(self, old_config: Dict, new_config: Dict, prefix: str = ""):
        """Check for configuration changes and notify watchers"""
        for key, new_value in new_config.items():
            current_key = f"{prefix}.{key}" if prefix else key
            old_value = old_config.get(key)

            if isinstance(new_value, dict) and isinstance(old_value, dict):
                self._check_config_changes(old_value, new_value, current_key)
            elif old_value != new_value:
                self._notify_watchers(current_key, new_value, old_value)

    def validate(self) -> Dict[str, Any]:
        """Validate configuration"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        # Check required configuration sections
        required_sections = ["autogen", "data_sources", "cache", "performance"]
        for section in required_sections:
            if section not in self.config:
                validation_results["errors"].append(f"Missing required section: {section}")
                validation_results["valid"] = False

        # Validate autogen configuration
        if "autogen" in self.config:
            autogen_config = self.config["autogen"]
            if "model" not in autogen_config:
                validation_results["errors"].append("Missing autogen.model")
                validation_results["valid"] = False
            elif not isinstance(autogen_config["model"], str):
                validation_results["errors"].append("autogen.model must be a string")
                validation_results["valid"] = False

            # Validate numeric parameters
            for param in ["temperature", "max_tokens", "top_p", "frequency_penalty", "presence_penalty"]:
                if param in autogen_config:
                    if not isinstance(autogen_config[param], (int, float)):
                        validation_results["errors"].append(f"autogen.{param} must be numeric")
                        validation_results["valid"] = False
                    elif param == "temperature" and not 0 <= autogen_config[param] <= 2:
                        validation_results["warnings"].append(f"autogen.{param} should be between 0 and 2")
                    elif param in ["max_tokens"] and autogen_config[param] <= 0:
                        validation_results["errors"].append(f"autogen.{param} must be positive")
                        validation_results["valid"] = False

        # Validate data sources configuration
        if "data_sources" in self.config:
            for source_name, source_config in self.config["data_sources"].items():
                if not isinstance(source_config, dict):
                    validation_results["errors"].append(f"data_sources.{source_name} must be a dictionary")
                    validation_results["valid"] = False
                    continue

                if "enabled" in source_config and not isinstance(source_config["enabled"], bool):
                    validation_results["errors"].append(f"data_sources.{source_name}.enabled must be boolean")
                    validation_results["valid"] = False

                if "rate_limit" in source_config:
                    if not isinstance(source_config["rate_limit"], int) or source_config["rate_limit"] <= 0:
                        validation_results["errors"].append(f"data_sources.{source_name}.rate_limit must be positive integer")
                        validation_results["valid"] = False

                if "timeout" in source_config:
                    if not isinstance(source_config["timeout"], int) or source_config["timeout"] <= 0:
                        validation_results["errors"].append(f"data_sources.{source_name}.timeout must be positive integer")
                        validation_results["valid"] = False

        # Validate performance configuration
        if "performance" in self.config:
            perf_config = self.config["performance"]
            for param in ["max_workers", "max_concurrent_requests", "timeout"]:
                if param in perf_config:
                    if not isinstance(perf_config[param], int) or perf_config[param] <= 0:
                        validation_results["errors"].append(f"performance.{param} must be positive integer")
                        validation_results["valid"] = False

        return validation_results

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get a complete configuration section"""
        return self.get(section, {})

    def update_section(self, section: str, new_config: Dict[str, Any], save: bool = True):
        """Update an entire configuration section"""
        self.set(section, new_config, save)

    def merge_config(self, new_config: Dict[str, Any], save: bool = True):
        """Merge new configuration with existing one"""
        self._deep_merge(self.config, new_config)
        if save:
            self._save_config()

    def _deep_merge(self, base: Dict, update: Dict):
        """Deep merge two dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def export_config(self, format: str = "yaml") -> str:
        """Export configuration to string"""
        if format.lower() == "yaml":
            return yaml.dump(self.config, default_flow_style=False, indent=2)
        elif format.lower() == "json":
            return json.dumps(self.config, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def import_config(self, config_str: str, format: str = "yaml", save: bool = True):
        """Import configuration from string"""
        try:
            if format.lower() == "yaml":
                new_config = yaml.safe_load(config_str)
            elif format.lower() == "json":
                new_config = json.loads(config_str)
            else:
                raise ValueError(f"Unsupported import format: {format}")

            # Validate imported config
            old_config = self.config.copy()
            self.config = new_config

            validation = self.validate()
            if not validation["valid"]:
                self.config = old_config
                raise ValueError(f"Invalid configuration: {validation['errors']}")

            if save:
                self._save_config()

            self.logger.info("Configuration imported successfully")

        except Exception as e:
            self.logger.error(f"Failed to import configuration: {str(e)}")
            raise

    def reset_to_defaults(self, save: bool = True):
        """Reset configuration to defaults"""
        old_config = self.config.copy()
        self.config = self._get_default_config()

        if save:
            self._save_config()

        # Notify watchers of changes
        self._check_config_changes(old_config, self.config)

        self.logger.info("Configuration reset to defaults")

    def get_metadata(self) -> Dict[str, Any]:
        """Get configuration metadata"""
        return {
            "config_file": str(self.config_path),
            "config_exists": self.config_path.exists(),
            "last_modified": datetime.fromtimestamp(self.config_path.stat().st_mtime).isoformat() if self.config_path.exists() else None,
            "watchers_count": len(self.watchers),
            "config_size": len(self.export_config()),
            "validation": self.validate()
        }