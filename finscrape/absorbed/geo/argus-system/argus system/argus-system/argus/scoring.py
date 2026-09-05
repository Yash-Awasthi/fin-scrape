"""
Computes and logs a 0-100 risk score per location, using events already
ingested into Neo4j within a rolling time window. Also rolls location
scores up into route-level scores.
"""
import numpy as np
import pandas as pd
from datetime import datetime


def recompute_location_risk(driver, location: str, window_hours: int = 168) -> dict | None:
    # e.date is stored as an 8-digit string 'yyyyMMdd' (GDELT's SQLDATE format),
    # which sorts/compares correctly as a plain string — no APOC/date parsing needed.
    cutoff_date = (datetime.utcnow() - pd.Timedelta(hours=window_hours)).strftime("%Y%m%d")
    query = """
    MATCH (l:Location {name: $location})<-[:OCCURRED_AT]-(e:Event)
    WHERE e.date >= $cutoff_date
    RETURN e.goldstein AS goldstein, e.tone AS tone, e.mentions AS mentions, e.quad_class AS quad_class
    """
    with driver.session() as session:
        result = session.run(query, location=location, cutoff_date=cutoff_date)
        rows = [dict(r) for r in result]

    if not rows:
        return None

    d = pd.DataFrame(rows)
    weights = d["mentions"].fillna(1).clip(lower=1)
    avg_goldstein = np.average(d["goldstein"].fillna(0), weights=weights)
    avg_tone = np.average(d["tone"].fillna(0), weights=weights)
    conflict_share = d["quad_class"].isin([3, 4]).mean()

    goldstein_risk = np.clip((10 - avg_goldstein) / 20, 0, 1)
    tone_risk = np.clip((10 - np.clip(avg_tone, -10, 10)) / 20, 0, 1)

    risk_score = (0.40 * goldstein_risk + 0.30 * tone_risk + 0.30 * conflict_share) * 100
    n_events = len(d)
    confidence = "low" if n_events < 20 else "medium" if n_events < 100 else "high"

    return {
        "location": location,
        "risk_score": round(float(risk_score), 1),
        "n_events": n_events,
        "avg_goldstein": round(float(avg_goldstein), 2),
        "avg_tone": round(float(avg_tone), 2),
        "conflict_share": round(float(conflict_share), 2),
        "confidence": confidence,
    }


def log_risk_snapshot(driver, result: dict):
    query = """
    MATCH (l:Location {name: $location})
    CREATE (s:RiskSnapshot {
        timestamp: $timestamp,
        risk_score: $risk_score,
        confidence: $confidence,
        n_events: $n_events
    })
    MERGE (l)-[:HAS_SNAPSHOT]->(s)
    """
    with driver.session() as session:
        session.run(
            query,
            location=result["location"],
            timestamp=datetime.utcnow().isoformat(),
            risk_score=result["risk_score"],
            confidence=result["confidence"],
            n_events=result["n_events"],
        )


def score_and_log_locations(driver, locations: list, window_hours: int = 168) -> pd.DataFrame:
    results = []
    for loc in locations:
        r = recompute_location_risk(driver, loc, window_hours=window_hours)
        if r:
            log_risk_snapshot(driver, r)
            results.append(r)
    return pd.DataFrame(results)


def score_route(route_locations: list, location_risk_df: pd.DataFrame) -> dict:
    """Route risk = its riskiest chokepoint (a route is only as safe as its weakest link)."""
    scores = location_risk_df[location_risk_df["location"].isin(route_locations)]
    if len(scores) == 0:
        return {"risk_score": 0.0, "bottleneck": None}
    row = scores.loc[scores["risk_score"].idxmax()]
    return {"risk_score": float(row["risk_score"]), "bottleneck": row["location"]}


def score_all_routes(routes: dict, location_risk_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for route_name, locs in routes.items():
        r = score_route(locs, location_risk_df)
        rows.append({"route": route_name, **r})
    return pd.DataFrame(rows).sort_values("risk_score")
