"""
Configuration Watcher
File system watcher for configuration changes
"""

import os
import logging
import time
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ConfigChangeEvent:
    """Configuration change event"""
    file_path: str
    change_type: str  # 'created', 'modified', 'deleted'
    timestamp: datetime
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None


class ConfigWatcher:
    """Configuration file watcher"""

    def __init__(self, config_dir: str = ".", watch_interval: float = 1.0):
        self.config_dir = Path(config_dir)
        self.watch_interval = watch_interval
        self.logger = logging.getLogger(__name__)
        self._watching = False
        self._callbacks: List[Callable[[ConfigChangeEvent], None]] = []
        self._file_states: Dict[str, float] = {}

    def add_callback(self, callback: Callable[[ConfigChangeEvent], None]):
        """Add change callback"""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[ConfigChangeEvent], None]):
        """Remove change callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def start_watching(self):
        """Start watching configuration files"""
        self._watching = True
        self._initialize_file_states()

    def stop_watching(self):
        """Stop watching configuration files"""
        self._watching = False

    def _initialize_file_states(self):
        """Initialize file modification times"""
        config_files = [
            "config.yaml",
            ".env",
            "requirements.txt"
        ]

        for file_name in config_files:
            file_path = self.config_dir / file_name
            if file_path.exists():
                self._file_states[str(file_path)] = file_path.stat().st_mtime

    def check_changes(self):
        """Check for configuration changes"""
        if not self._watching:
            return

        current_time = datetime.now()

        for file_path, mtime in list(self._file_states.items()):
            file = Path(file_path)

            if file.exists():
                current_mtime = file.stat().st_mtime
                if current_mtime > mtime:
                    # File was modified
                    event = ConfigChangeEvent(
                        file_path=file_path,
                        change_type="modified",
                        timestamp=current_time
                    )
                    self._notify_callbacks(event)
                    self._file_states[file_path] = current_mtime
            else:
                # File was deleted
                event = ConfigChangeEvent(
                    file_path=file_path,
                    change_type="deleted",
                    timestamp=current_time
                )
                self._notify_callbacks(event)
                del self._file_states[file_path]