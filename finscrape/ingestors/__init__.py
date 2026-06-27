"""Keyless free-API ingestors for world signals.

Each ingestor pulls a public, no-auth API and emits `RawGeoEvent`s that flow into the
same analyze→judge pipeline as scraped articles (worker, Phase 3). Network `fetch_raw`
is kept separate from the pure `parse` so the parsers are unit-tested against fixtures
with no network. Endpoints are public facts (verified present in worldmonitor), not
copied source.
"""

from finscrape.ingestors.base import BaseIngestor, RawGeoEvent
from finscrape.ingestors.coingecko import CoinGeckoIngestor
from finscrape.ingestors.gdelt import GDELTIngestor
from finscrape.ingestors.opensky import OpenSkyIngestor
from finscrape.ingestors.reliefweb import ReliefWebIngestor
from finscrape.ingestors.usgs import USGSQuakesIngestor

# Event-producing ingestors (OpenSky is a flights data layer, not an event source).
EVENT_INGESTORS = (
    USGSQuakesIngestor,
    GDELTIngestor,
    ReliefWebIngestor,
    CoinGeckoIngestor,
)

__all__ = [
    "BaseIngestor",
    "RawGeoEvent",
    "USGSQuakesIngestor",
    "GDELTIngestor",
    "ReliefWebIngestor",
    "CoinGeckoIngestor",
    "OpenSkyIngestor",
    "EVENT_INGESTORS",
]
