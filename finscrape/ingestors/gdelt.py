"""GDELT 2.0 Doc API — global news articles, keyless JSON.

Default query targets conflict/crisis coverage; override `query` to retarget.
"""

from __future__ import annotations

from typing import Any

from finscrape.ingestors.base import BaseIngestor, RawGeoEvent

_DEFAULT_QUERY = "(conflict OR sanctions OR crisis OR military) sourcelang:english"


class GDELTIngestor(BaseIngestor):
    name = "gdelt"
    base_url = "https://api.gdeltproject.org/api/v2/doc/doc"

    def __init__(self, query: str = _DEFAULT_QUERY, max_records: int = 30):
        self.query = query
        self.max_records = max_records

    def fetch_raw(self, url: str | None = None, params: dict | None = None) -> Any:
        return super().fetch_raw(
            params={
                "query": self.query,
                "mode": "ArtList",
                "format": "json",
                "maxrecords": self.max_records,
                "sort": "datedesc",
            }
        )

    def parse(self, data: Any) -> list[RawGeoEvent]:
        events: list[RawGeoEvent] = []
        for art in (data or {}).get("articles", []):
            title = (art.get("title") or "").strip()
            if not title:
                continue
            events.append(
                RawGeoEvent(
                    title=title,
                    text=title,
                    source=f"gdelt/{art.get('domain', 'unknown')}:wire",
                    event_type="geopolitical_event",
                    published_at=art.get("seendate"),
                    url=art.get("url", ""),
                )
            )
        return events
