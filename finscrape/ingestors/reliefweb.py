"""ReliefWeb (UN OCHA) disasters — keyless JSON. Humanitarian/disaster signals."""

from __future__ import annotations

from typing import Any

from finscrape.ingestors.base import BaseIngestor, RawGeoEvent


class ReliefWebIngestor(BaseIngestor):
    name = "reliefweb"
    base_url = "https://api.reliefweb.int/v1/disasters"

    def __init__(self, limit: int = 20):
        self.limit = limit

    def fetch_raw(self, url: str | None = None, params: dict | None = None) -> Any:
        # appname is required by ReliefWeb's terms; fields[] keeps the payload small.
        return super().fetch_raw(
            params={
                "appname": "finscrape-worldfin",
                "limit": self.limit,
                "sort[]": "date:desc",
                "fields[include][]": ["name", "status", "date", "country"],
            }
        )

    def parse(self, data: Any) -> list[RawGeoEvent]:
        events: list[RawGeoEvent] = []
        for item in (data or {}).get("data", []):
            fields = item.get("fields") or {}
            name = (fields.get("name") or "").strip()
            if not name:
                continue
            countries = fields.get("country") or []
            country = countries[0].get("name") if countries else ""
            date = (fields.get("date") or {}).get("created")
            events.append(
                RawGeoEvent(
                    title=name,
                    text=f"Humanitarian disaster: {name}."
                    + (f" Country: {country}." if country else ""),
                    source="reliefweb:gov",
                    event_type="other",
                    published_at=date,
                    url=(item.get("href") or ""),
                )
            )
        return events
