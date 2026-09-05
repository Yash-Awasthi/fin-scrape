"""
GraphRAG layer: Cypher-based retrieval of a route's relevant subgraph,
followed by LLM synthesis into a human-readable risk explanation.
This is what turns a bare risk number into an explainable verdict.
"""
import os
import requests
from datetime import datetime


def retrieve_route_context(driver, route_name: str, days_back: int = 7) -> list:
    date_cutoff = (datetime.utcnow() - __import__("pandas").Timedelta(days=days_back)).strftime("%Y%m%d")
    query = """
    MATCH (r:Route {name: $route_name})-[:PASSES_THROUGH]->(l:Location)
    OPTIONAL MATCH (l)-[:HAS_SNAPSHOT]->(s:RiskSnapshot)
    WITH r, l, s ORDER BY s.timestamp DESC
    WITH r, l, collect(s)[0] AS latest_snapshot
    OPTIONAL MATCH (e:Event)-[:OCCURRED_AT]->(l)
    WHERE e.date >= $date_cutoff
    OPTIONAL MATCH (a:Actor)-[:INVOLVED_IN]->(e)
    RETURN l.name AS location,
           latest_snapshot.risk_score AS risk_score,
           latest_snapshot.timestamp AS snapshot_time,
           collect(DISTINCT e.event_code)[0..10] AS recent_event_codes,
           avg(e.goldstein) AS avg_goldstein,
           avg(e.tone) AS avg_tone,
           collect(DISTINCT a.name)[0..10] AS actors_involved
    """
    with driver.session() as session:
        result = session.run(query, route_name=route_name, date_cutoff=date_cutoff)
        return [dict(r) for r in result]


def context_to_text(context_rows: list) -> str:
    lines = []
    for row in context_rows:
        lines.append(
            f"Location: {row['location']} | Risk score: {row['risk_score']} "
            f"(as of {row['snapshot_time']})\n"
            f"  Avg Goldstein: {row['avg_goldstein']}, Avg Tone: {row['avg_tone']}\n"
            f"  Recent event codes: {row['recent_event_codes']}\n"
            f"  Actors involved: {row['actors_involved']}"
        )
    return "\n\n".join(lines)


def assess_route_with_llm(route_name: str, context_rows: list) -> str:
    context_text = context_to_text(context_rows)
    prompt = f"""You are a maritime logistics risk analyst for the ARGUS system.
Assess route "{route_name}" using this graph-derived context:

{context_text}

Give: (1) overall route risk verdict, (2) the specific bottleneck location and why,
(3) whether to reroute now, (4) confidence level based on data volume."""

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "content-type": "application/json",
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 800,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["content"][0]["text"]
