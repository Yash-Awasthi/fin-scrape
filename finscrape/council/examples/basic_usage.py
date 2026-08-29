"""
Basic usage of worldfin-council.

Shows how to set up a simple council with 3 agents and run a deliberation.

Usage:
    python -m finscrape.council.examples.basic_usage
"""
from finscrape.council.council import AgentCouncil
from finscrape.council.base import BaseAgent, AgentVerdict
from finscrape.council.protocols import CouncilEvent


# ── Step 1: Define your AI client ────────────────────────────────────────────
# This is any function that calls an LLM and returns parsed JSON.
# In production, use your actual LLM client (OpenAI, Anthropic, Ollama, etc.)

def mock_ai_client(prompt: str, system: str, model: str | None = None) -> dict | None:
    """Mock AI client for demonstration. Replace with real LLM calls."""
    # In real code, you'd call your LLM here:
    # response = openai.ChatCompletion.create(model="gpt-4", messages=[...])
    # return json.loads(response.choices[0].message.content)

    # For demo, return a mock verdict
    return {
        "verdict": "OBSERVE",
        "signal_score": 2,
        "confidence": 0.7,
        "reasoning": "The news is mildly positive for the sector.",
        "tickers": ["AAPL"],
        "risk_factors": ["Market volatility"],
        "key_insights": ["Positive sentiment shift"],
    }


# ── Step 2: Create agents ────────────────────────────────────────────────────

class BullishAgent(BaseAgent):
    """Simple agent that looks for bullish signals."""

    @property
    def name(self) -> str:
        return "bullish"

    @property
    def role(self) -> str:
        return "Agent that identifies bullish opportunities."

    @property
    def system_prompt(self) -> str:
        return (
            "You are a bullish analyst. Look for positive signals and growth "
            "opportunities. Return a JSON verdict."
        )


class BearishAgent(BaseAgent):
    """Simple agent that looks for bearish signals."""

    @property
    def name(self) -> str:
        return "bearish"

    @property
    def role(self) -> str:
        return "Agent that identifies bearish risks."

    @property
    def system_prompt(self) -> str:
        return (
            "You are a bearish analyst. Look for risks and downside scenarios. "
            "Return a JSON verdict."
        )


class NeutralAgent(BaseAgent):
    """Balanced agent that weighs both sides."""

    @property
    def name(self) -> str:
        return "neutral"

    @property
    def role(self) -> str:
        return "Balanced analyst weighing both sides."

    @property
    def system_prompt(self) -> str:
        return (
            "You are a balanced analyst. Weigh bullish and bearish factors "
            "evenly. Return a JSON verdict."
        )


# ── Step 3: Run the council ──────────────────────────────────────────────────

def main():
    council = AgentCouncil(
        agents=[
            BullishAgent(weight=1.2),
            BearishAgent(weight=1.0),
            NeutralAgent(weight=0.8),
        ],
        ai_client=mock_ai_client,
        rounds=1,  # number of rebuttal rounds
    )

    verdict = council.deliberate(
        title="Apple reports record Q3 revenue",
        text=(
            "Apple Inc. reported fiscal Q3 revenue of $94.8 billion, "
            "beating analyst estimates of $90 billion. iPhone sales grew "
            "12% year over year. The company raised full-year guidance."
        ),
        metadata={"source": "Reuters", "tickers": ["AAPL"]},
    )

    print("=" * 60)
    print("COUNCIL DELIBERATION RESULT")
    print("=" * 60)
    print(f"Consensus Score:    {verdict.consensus_score:+.1f}")
    print(f"Consensus Verdict:  {verdict.consensus_verdict}")
    print(f"Confidence:         {verdict.consensus_confidence:.1%}")
    print(f"Agreement Level:    {verdict.agreement_level:.1%}")
    print(f"Dissenting Agents:  {verdict.dissenting_agents or 'None'}")
    print()
    print("Individual Verdicts:")
    for v in verdict.individual_verdicts:
        print(f"  {v.agent_name:12s}  score={v.signal_score:+d}  "
              f"verdict={v.verdict:10s}  conf={v.confidence:.0%}")
    print()
    print("Key Risks:")
    for r in verdict.key_risks:
        print(f"  - {r}")
    print()
    print("Key Opportunities:")
    for o in verdict.key_opportunities:
        print(f"  + {o}")


if __name__ == "__main__":
    main()
