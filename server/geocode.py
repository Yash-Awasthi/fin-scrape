"""Event → (lat, lon) for the globe.

Two paths: (1) explicit coords from a structured ingestor (USGS) pass straight
through; (2) otherwise we resolve a country mentioned in the subject / affected
entities to a representative centroid. This is a SEED country table (facts —
approximate centroids for major countries); extend toward the full
worldmonitor country-bbox set as needed. Returns (None, None) when nothing matches
— the globe simply doesn't plot that event.
"""

from __future__ import annotations

import re

# country name -> (lat, lon) approximate centroid. Seed set; extend freely.
COUNTRY_CENTROID: dict[str, tuple[float, float]] = {
    "united states": (39.8, -98.6),
    "usa": (39.8, -98.6),
    "u.s.": (39.8, -98.6),
    "china": (35.9, 104.2),
    "russia": (61.5, 105.3),
    "ukraine": (48.4, 31.2),
    "israel": (31.0, 34.9),
    "gaza": (31.4, 34.4),
    "palestine": (31.9, 35.2),
    "iran": (32.4, 53.7),
    "iraq": (33.2, 43.7),
    "saudi arabia": (23.9, 45.1),
    "united kingdom": (54.0, -2.0),
    "uk": (54.0, -2.0),
    "britain": (54.0, -2.0),
    "france": (46.6, 2.2),
    "germany": (51.2, 10.4),
    "spain": (40.5, -3.7),
    "italy": (41.9, 12.6),
    "japan": (36.2, 138.3),
    "south korea": (36.5, 127.8),
    "north korea": (40.3, 127.5),
    "india": (22.0, 79.0),
    "pakistan": (30.4, 69.3),
    "taiwan": (23.7, 121.0),
    "turkey": (39.0, 35.2),
    "egypt": (26.8, 30.8),
    "brazil": (-14.2, -51.9),
    "mexico": (23.6, -102.5),
    "canada": (56.1, -106.3),
    "australia": (-25.3, 133.8),
    "south africa": (-30.6, 22.9),
    "nigeria": (9.1, 8.7),
    "venezuela": (6.4, -66.6),
    "yemen": (15.6, 48.0),
    "syria": (34.8, 38.9),
    "lebanon": (33.9, 35.9),
    "afghanistan": (33.9, 67.7),
    "qatar": (25.3, 51.2),
    "united arab emirates": (23.4, 53.8),
    "uae": (23.4, 53.8),
    "poland": (51.9, 19.1),
    "netherlands": (52.1, 5.3),
    "switzerland": (46.8, 8.2),
    "sweden": (60.1, 18.6),
    "indonesia": (-0.8, 113.9),
    "philippines": (12.9, 121.8),
    "vietnam": (14.1, 108.3),
    "thailand": (15.9, 100.99),
    "greece": (39.1, 21.8),
    "hong kong": (22.3, 114.2),
    "singapore": (1.35, 103.8),
    "argentina": (-38.4, -63.6),
    "libya": (26.3, 17.2),
}

# match longest names first so "south korea" wins over "korea"
_SORTED = sorted(COUNTRY_CENTROID, key=len, reverse=True)


def geocode_text(text: str) -> tuple[float | None, float | None]:
    """Find the first country mentioned (word-boundary) and return its centroid."""
    low = (text or "").lower()
    for name in _SORTED:
        if re.search(rf"(?<![a-z]){re.escape(name)}(?![a-z])", low):
            return COUNTRY_CENTROID[name]
    return None, None


def geocode_event(
    subject: str,
    affected_entities: list | None = None,
    explicit_latlon: tuple[float | None, float | None] | None = None,
) -> tuple[float | None, float | None]:
    """Resolve coordinates: explicit ingestor coords win; else scan subject then
    entity names for a country."""
    if (
        explicit_latlon
        and explicit_latlon[0] is not None
        and explicit_latlon[1] is not None
    ):
        return explicit_latlon

    lat, lon = geocode_text(subject)
    if lat is not None:
        return lat, lon

    for ent in affected_entities or []:
        name = ent.get("name") if isinstance(ent, dict) else str(ent)
        lat, lon = geocode_text(name or "")
        if lat is not None:
            return lat, lon
    return None, None
