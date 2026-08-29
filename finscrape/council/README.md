# worldfin-council

**Multi-agent deliberation council with consensus scoring and judge override.**

Zero-dependency Python package for running multiple AI agents in parallel, computing weighted consensus, and optionally overriding with an independent judge — originally built for the [WorldFin](https://github.com/Yash-Awasthi/fin-scrape) geopolitical intelligence platform.

## Installation

```bash
pip install worldfin-council
```

## Quick Start

```python
from worldfin_council import AgentCouncil, CouncilVerdict
from worldfin_council.base import BaseAgent, AgentVerdict

# 1. Define your AI client (any function that calls an LLM)
def my_ai_client(prompt: str, system: str, model: str = None) -> dict | None:
    # Call your LLM here and return parsed JSON
    return {"verdict": "OBSERVE", "signal_score": 2, "confidence": 0.7,
            "reasoning": "Analysis...", "tickers": ["AAPL"],
            "risk_factors": [], "key_insights": []}

# 2. Create a custom agent
class MyAgent(BaseAgent):
    name = "my-analyst"
    role = "Financial analyst"
    system_prompt = "You analyze financial news..."

# 3. Run the council
council = AgentCouncil(
    agents=[MyAgent(weight=1.5)],
    ai_client=my_ai_client,
    judge=False,
)
verdict = council.deliberate(
    title="Fed cuts rates by 50bps",
    text="The Federal Reserve announced...",
    metadata={"source": "Reuters", "age_hours": 0.5},
)

print(verdict.consensus_verdict)  # "INVEST"
print(verdict.consensus_score)    # 3.5
print(verdict.agreement_level)    # 0.85
```

## API Reference

### AgentCouncil

The main orchestrator class.

```python
AgentCouncil(
    agents: list[BaseAgent],      # Required: your agent instances
    ai_client: AiClient,          # Required: your LLM client function
    max_workers: int = None,      # ThreadPoolExecutor workers (default: min(agents, 8))
    judge: bool = False,          # Enable judge override
    rounds: int = None,           # Debate rounds (default: 1, env: FINSCRAPE_COUNCIL_ROUNDS)
)
```

**Methods:**
- `deliberate(title, text, metadata=None, market_facts=None, lessons=None)` → `CouncilVerdict`

### CouncilVerdict

The aggregated output from council deliberation.

| Field | Type | Description |
|-------|------|-------------|
| `consensus_score` | float | Weighted average score [-5, +5] |
| `consensus_confidence` | float | Confidence [0.0, 1.0] |
| `consensus_verdict` | str | INVEST / OBSERVE / CAUTIOUS / PULL_OUT |
| `agreement_level` | float | [0.0, 1.0]; 1 = perfect agreement |
| `dissenting_agents` | list[str] | Agent names that disagree with consensus |
| `key_risks` | list[str] | Aggregated risk factors |
| `key_opportunities` | list[str] | Aggregated insights |
| `individual_verdicts` | list[AgentVerdict] | Each agent's verdict |
| `judge_rationale` | str | Judge's reasoning (if judged) |
| `judged` | bool | Whether judge overrode consensus |

### BaseAgent

Abstract base class for agents. Subclass and implement:

| Property | Type | Description |
|----------|------|-------------|
| `name` | str | Short identifier (e.g. "analyst") |
| `role` | str | One-line description |
| `system_prompt` | str | LLM system prompt |
| `weight` | float | Consensus weight (default: 1.0) |

### AiClient Protocol

Your LLM client must match this signature:

```python
def ai_client(prompt: str, system: str, model: str | None = None) -> dict | None:
    ...
```

Returns parsed JSON dict, or None on failure (council uses default verdict).

## Built-in Personas

The package includes 7 financial analyst personas (import from `worldfin_council.personas`):

| Persona | Weight | Perspective |
|---------|--------|-------------|
| AnalystAgent | 1.5 | Neutral event extraction and impact analysis |
| ContrarianAgent | 1.0 | Challenges consensus, finds counter-arguments |
| RiskAgent | 1.2 | Downside scenarios, tail risks, contagion |
| MomentumAgent | 0.8 | Short-term sentiment and technical catalysts |
| FundamentalsAgent | 1.0 | Long-term business value and earnings quality |
| ScoutAgent | 0.7 | Source reliability, freshness, novelty |
| ReviewerAgent | 1.4 | Cross-checks claims, completeness, pricing |

```python
from worldfin_council.personas import DEFAULT_AGENTS
council = AgentCouncil(agents=DEFAULT_AGENTS, ai_client=my_client)
```

## License

MIT
