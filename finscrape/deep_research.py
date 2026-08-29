"""
Deep Research Mode

Multi-step geopolitical analysis that goes beyond single-event processing.
Traces second-order effects across supply chains, alliances, and markets.
Inspired by onyx deep research + reflexivity geopolitical analysis.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ResearchStep:
    """Single step in a deep research chain."""
    step_number: int
    query: str
    sources_checked: list[str]
    findings: list[str]
    connections: list[str]  # Links to other steps or events
    confidence: float  # 0-1


@dataclass
class DeepResearchReport:
    """Complete deep research report."""
    topic: str
    steps: list[ResearchStep]
    synthesis: str
    market_implications: list[dict]  # [{ticker, signal, reasoning, confidence}]
    risk_factors: list[str]
    sources_summary: dict  # source -> reliability score
    total_sources_checked: int
    research_depth: str  # "shallow", "standard", "deep", "exhaustive"


# Research depth levels
DEPTH_CONFIG = {
    "shallow":    {"max_steps": 3,  "sources_per_step": 5,  "triangulation": False},
    "standard":   {"max_steps": 5,  "sources_per_step": 10, "triangulation": True},
    "deep":       {"max_steps": 10, "sources_per_step": 20, "triangulation": True},
    "exhaustive": {"max_steps": 20, "sources_per_step": 50, "triangulation": True},
}


# Source reliability tiers
SOURCE_TIERS = {
    "wire":       {"reliability": 0.95, "examples": ["Reuters", "AP", "Bloomberg"]},
    "gov":        {"reliability": 0.90, "examples": ["State Dept", "EU Commission", "UN"]},
    "intel":      {"reliability": 0.85, "examples": ["ISW", "RUSI", "IISS"]},
    "financial":  {"reliability": 0.80, "examples": ["Fed", "ECB", "IMF"]},
    "specialist": {"reliability": 0.75, "examples": ["Jane's", "Stratfor", "Eurasianet"]},
    "social":     {"reliability": 0.50, "examples": ["Twitter/X", "Reddit", "Telegram"]},
}


def build_research_chain(topic: str, depth: str = "standard") -> dict:
    """
    Build a research chain for a geopolitical topic.
    Returns the research plan, not results (results come from the pipeline).
    """
    config = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["standard"])

    # Generate research steps based on topic
    steps = []

    # Step 1: Direct event analysis
    steps.append({
        "step": 1,
        "type": "direct_analysis",
        "query": f"What is happening with {topic}? Primary sources.",
        "sources": ["wire", "gov"],
        "min_sources": 3,
    })

    # Step 2: Actor identification
    steps.append({
        "step": 2,
        "type": "actor_mapping",
        "query": f"Who are the key actors involved in {topic}? What are their interests?",
        "sources": ["wire", "intel", "specialist"],
        "min_sources": 5,
    })

    # Step 3: Historical context
    steps.append({
        "step": 3,
        "type": "historical_context",
        "query": f"What is the historical precedent for {topic}? Similar past events?",
        "sources": ["specialist", "intel"],
        "min_sources": 3,
    })

    if config["max_steps"] >= 5:
        # Step 4: Supply chain / economic impact
        steps.append({
            "step": 4,
            "type": "economic_impact",
            "query": f"What supply chains, trade routes, or markets does {topic} affect?",
            "sources": ["financial", "wire", "specialist"],
            "min_sources": 5,
        })

        # Step 5: Alliance / diplomatic fallout
        steps.append({
            "step": 5,
            "type": "diplomatic_analysis",
            "query": f"How are allies and adversaries responding to {topic}?",
            "sources": ["gov", "wire", "intel"],
            "min_sources": 5,
        })

    if config["max_steps"] >= 10:
        # Step 6-10: Second and third order effects
        for i, dimension in enumerate([
            "energy markets and commodity prices",
            "military force posture changes",
            "sanctions and financial warfare",
            "information warfare and narrative competition",
            "humanitarian and refugee implications",
        ], 6):
            steps.append({
                "step": i,
                "type": "second_order",
                "query": f"What are the {dimension} implications of {topic}?",
                "sources": ["specialist", "financial", "intel"],
                "min_sources": 5,
            })

    return {
        "topic": topic,
        "depth": depth,
        "total_steps": len(steps),
        "steps": steps,
        "triangulation": config["triangulation"],
        "estimated_sources": sum(s["min_sources"] for s in steps),
    }


def assess_source_quality(source_type: str, source_name: str) -> dict:
    """Assess the quality and reliability of a source."""
    tier = SOURCE_TIERS.get(source_type, {"reliability": 0.5, "examples": []})
    is_known = source_name in tier["examples"]
    return {
        "source": source_name,
        "type": source_type,
        "base_reliability": tier["reliability"],
        "known_source": is_known,
        "effective_reliability": tier["reliability"] * (1.1 if is_known else 0.9),
    }


def synthesize_findings(steps: list[dict]) -> dict:
    """
    Synthesize findings from multiple research steps into a coherent report.
    This is the 'judge' step — like the 7-agent council judge in the main pipeline.
    """
    all_findings = []
    source_counts = {}
    high_confidence = []

    for step in steps:
        findings = step.get("findings", [])
        all_findings.extend(findings)
        for source in step.get("sources_checked", []):
            source_counts[source] = source_counts.get(source, 0) + 1
            if step.get("confidence", 0) > 0.8:
                high_confidence.extend(findings)

    # Triangulation: findings confirmed by 3+ independent sources
    triangulated = []
    finding_sources = {}
    for step in steps:
        for finding in step.get("findings", []):
            key = finding.lower().strip()
            if key not in finding_sources:
                finding_sources[key] = set()
            for source in step.get("sources_checked", []):
                finding_sources[key].add(source)

    for finding, sources in finding_sources.items():
        if len(sources) >= 3:
            triangulated.append({
                "finding": finding,
                "source_count": len(sources),
                "confidence": min(1.0, 0.5 + len(sources) * 0.15),
            })

    return {
        "total_findings": len(all_findings),
        "unique_sources": len(source_counts),
        "triangulated_findings": triangulated,
        "high_confidence_findings": len(high_confidence),
        "source_distribution": source_counts,
    }
