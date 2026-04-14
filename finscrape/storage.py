"""
State persistence for the FinScrape pipeline.

Manages visited URLs, extracted events, and entity index.
Uses JSON files in the data/ directory.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _project_root() -> Path:
    """Find project root by looking for main.py or .git."""
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (parent / "main.py").exists() or (parent / ".git").exists():
            return parent
    return current.parent


class StateManager:
    """Manages pipeline state: visited URLs, events, entity index."""

    def __init__(self, data_dir: str | None = None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = _project_root() / "data"

        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.visited_path = self.data_dir / "visited_urls.json"
        self.events_path = self.data_dir / "events.json"
        self.entity_path = self.data_dir / "entity_index.json"

        self.visited: dict[str, list[str]] = self._load(self.visited_path, default={})
        self.events: list[dict] = self._load(self.events_path, default=[])
        self.entity_index: dict[str, list] = self._load(self.entity_path, default={})

    def _load(self, path: Path, default: Any = None) -> Any:
        if not path.exists():
            return default if default is not None else {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Error loading %s: %s", path, e)
            return default if default is not None else {}

    def _save(self, path: Path, data: Any) -> None:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error("Error saving %s: %s", path, e)

    def get_visited(self, source: str) -> list[str]:
        return self.visited.get(source, [])

    def add_visited(self, source: str, url: str) -> None:
        if source not in self.visited:
            self.visited[source] = []
        if url not in self.visited[source]:
            self.visited[source].append(url)
            self._save(self.visited_path, self.visited)

    def save_events(self) -> None:
        self._save(self.events_path, self.events)

    def add_event(self, event: dict) -> None:
        self.events.append(event)
        self.save_events()

    def resolve_entity_tickers(self, text: str) -> list[str]:
        """Look up tickers from entity index based on text content."""
        text_lower = text.lower()
        words = set(text_lower.split())
        tickers = []
        for w in words:
            if w in self.entity_index:
                for company, ticker in self.entity_index[w]:
                    if company.lower() in text_lower:
                        tickers.append(ticker)
        return tickers
