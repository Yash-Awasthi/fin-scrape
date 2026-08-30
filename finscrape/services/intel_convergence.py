"""
Intel Convergence — Extracted from World Intelligence MCP patterns.

Multi-domain signal convergence detection with:
- Geographic grid-based event clustering
- Cross-domain signal overlap detection
- Risk scoring based on signal diversity
- Escalation detection
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class IntelEvent:
    lat: float
    lon: float
    event_type: str
    weight: float = 1.0
    source: str = ""
    timestamp: str = ""
    description: str = ""


@dataclass
class ConvergenceHotspot:
    lat: float
    lon: float
    event_count: int
    signal_types: List[str]
    type_count: int
    total_weight: float
    convergence_score: float
    radius_km: float = 0.0


def grid_key(lat: float, lon: float, resolution: float = 1.0) -> Tuple[int, int]:
    """Convert lat/lon to grid cell key."""
    return (int(math.floor(lat / resolution)), int(math.floor(lon / resolution)))


def detect_convergence(
    events: List[IntelEvent],
    resolution: float = 1.0,
    min_types: int = 2,
    min_total: int = 3,
) -> List[ConvergenceHotspot]:
    """Detect geographic convergence of multi-domain signals."""
    grid: Dict[Tuple[int, int], List[IntelEvent]] = defaultdict(list)

    for event in events:
        key = grid_key(event.lat, event.lon, resolution)
        grid[key].append(event)

    hotspots: List[ConvergenceHotspot] = []
    for (grid_lat, grid_lon), cell_events in grid.items():
        if len(cell_events) < min_total:
            continue

        types: Set[str] = set()
        total_weight = 0.0
        for e in cell_events:
            types.add(e.event_type)
            total_weight += e.weight

        if len(types) < min_types:
            continue

        center_lat = (grid_lat + 0.5) * resolution
        center_lon = (grid_lon + 0.5) * resolution

        score = len(types) * (1 + len(cell_events) ** 0.5) * (total_weight / len(cell_events))

        hotspots.append(ConvergenceHotspot(
            lat=round(center_lat, 2),
            lon=round(center_lon, 2),
            event_count=len(cell_events),
            signal_types=sorted(types),
            type_count=len(types),
            total_weight=round(total_weight, 1),
            convergence_score=round(score, 2),
        ))

    hotspots.sort(key=lambda h: h.convergence_score, reverse=True)
    return hotspots


def detect_escalation(
    events: List[IntelEvent],
    time_window_hours: float = 24.0,
) -> Dict[str, Any]:
    """Detect escalation patterns in event streams."""
    if not events:
        return {"escalating": False, "confidence": 0.0, "factors": []}

    type_counts: Dict[str, int] = defaultdict(int)
    for event in events:
        type_counts[event.event_type] += 1

    total = len(events)
    unique_types = len(type_counts)

    # Escalation indicators
    factors = []
    if unique_types >= 3:
        factors.append("multi_domain")
    if total >= 10:
        factors.append("high_volume")
    if any(c >= 5 for c in type_counts.values()):
        factors.append("concentrated_type")

    confidence = min(1.0, unique_types * 0.2 + total * 0.02 + len(factors) * 0.15)

    return {
        "escalating": confidence > 0.5,
        "confidence": round(confidence, 2),
        "factors": factors,
        "event_count": total,
        "unique_types": unique_types,
    }


def calculate_risk_score(
    hotspots: List[ConvergenceHotspot],
    max_score: float = 100.0,
) -> float:
    """Calculate aggregate risk score from convergence hotspots."""
    if not hotspots:
        return 0.0

    total_score = sum(h.convergence_score for h in hotspots)
    # Normalize with diminishing returns
    normalized = max_score * (1 - math.exp(-total_score / 10))
    return round(normalized, 1)


def cluster_events(
    events: List[IntelEvent],
    radius_km: float = 100.0,
) -> List[Dict[str, Any]]:
    """Cluster events by geographic proximity."""
    if not events:
        return []

    used = set()
    clusters: List[Dict[str, Any]] = []

    for i, event in enumerate(events):
        if i in used:
            continue

        cluster_events = [event]
        used.add(i)

        for j, other in enumerate(events):
            if j in used:
                continue
            dist = haversine_distance(event.lat, event.lon, other.lat, other.lon)
            if dist <= radius_km:
                cluster_events.append(other)
                used.add(j)

        avg_lat = sum(e.lat for e in cluster_events) / len(cluster_events)
        avg_lon = sum(e.lon for e in cluster_events) / len(cluster_events)
        types = list(set(e.event_type for e in cluster_events))

        clusters.append({
            "center_lat": avg_lat,
            "center_lon": avg_lon,
            "event_count": len(cluster_events),
            "types": types,
            "events": cluster_events,
        })

    return clusters


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in km."""
    R = 6371.0
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
