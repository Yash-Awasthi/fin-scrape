"""
Region Extractor — Extracted from Realpolitik patterns.

Geopolitical region extraction with:
- Location-to-region mapping
- Multi-region event classification
- Region-based filtering
"""
from __future__ import annotations

from typing import Dict, List, Set


REGIONS: Dict[str, List[str]] = {
    "MIDDLE_EAST": [
        "Israel", "Palestine", "Gaza", "West Bank", "Lebanon", "Syria",
        "Iran", "Iraq", "Yemen", "Saudi Arabia", "UAE", "Qatar",
        "Jordan", "Kuwait", "Bahrain", "Oman", "Tel Aviv", "Jerusalem",
    ],
    "EAST_ASIA": [
        "China", "Chinese", "Taiwan", "Japan", "Japanese", "South Korea",
        "Korean", "North Korea", "DPRK", "Beijing", "Seoul", "Tokyo",
        "Hong Kong", "Mongolia",
    ],
    "SOUTHEAST_ASIA": [
        "Vietnam", "Thai", "Thailand", "Philippines", "Indonesia",
        "Malaysia", "Singapore", "Myanmar", "Cambodia", "Laos", "Brunei",
    ],
    "SOUTH_ASIA": [
        "India", "Indian", "Pakistan", "Pakistani", "Bangladesh", "Sri Lanka",
        "Nepal", "Afghanistan", "Afghan", "Kashmir", "Delhi",
    ],
    "EUROPE": [
        "Germany", "French", "France", "UK", "Britain", "British", "London",
        "Spain", "Italian", "Italy", "Poland", "Ukraine", "Ukrainian",
        "Russia", "Russian", "Moscow", "NATO", "EU", "European",
    ],
    "AFRICA": [
        "Nigeria", "South Africa", "Kenya", "Ethiopia", "Egypt", "Egyptian",
        "Sudan", "Somalia", "Congo", "Morocco", "Tunisia", "Libya",
    ],
    "AMERICAS": [
        "USA", "United States", "American", "Washington", "Canada",
        "Canadian", "Mexico", "Brazil", "Brazilian", "Argentina",
        "Colombia", "Venezuela", "Cuba", "Caribbean",
    ],
    "CENTRAL_ASIA": [
        "Kazakhstan", "Uzbekistan", "Turkmenistan", "Kyrgyzstan", "Tajikistan",
    ],
    "OCEANIA": [
        "Australia", "Australian", "New Zealand", "Pacific", "Fiji",
        "Papua New Guinea",
    ],
}


def extract_regions(text: str) -> Set[str]:
    """Extract regions from text based on location mentions."""
    found = set()
    for region, keywords in REGIONS.items():
        for keyword in keywords:
            if keyword.lower() in text.lower():
                found.add(region)
                break
    return found


def classify_event_region(text: str) -> str:
    """Classify event to primary region."""
    regions = extract_regions(text)
    if len(regions) == 1:
        return regions.pop()
    elif len(regions) > 1:
        return "MULTI_REGION"
    return "OTHER"


def region_filter(events: List[Dict], allowed_regions: Set[str]) -> List[Dict]:
    """Filter events by allowed regions."""
    filtered = []
    for event in events:
        text = event.get("text", "") or event.get("title", "")
        regions = extract_regions(text)
        if regions & allowed_regions:
            filtered.append(event)
    return filtered


def get_region_stats(events: List[Dict]) -> Dict[str, int]:
    """Count events per region."""
    stats: Dict[str, int] = {}
    for event in events:
        text = event.get("text", "") or event.get("title", "")
        regions = extract_regions(text)
        for region in regions:
            stats[region] = stats.get(region, 0) + 1
    return stats
