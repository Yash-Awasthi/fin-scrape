# agents/critic.py
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

_llm = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
    return _llm

CRITIC_PROMPT = """You are the Critic agent in SENTINEL — a geopolitical market intelligence system.

Review the Researcher's analysis and decide: is it good enough, or does it need revision?

PASS if the analysis:
- Covers the main affected tickers with clear reasoning
- Identifies both risks AND opportunities
- Has at least 3 distinct sections
- Explains the geopolitical mechanism clearly

NEEDS_REVISION only if the analysis:
- Is missing major affected sectors entirely
- Has no specific ticker symbols
- Contradicts itself significantly
- Is under 150 words

If you issue NEEDS_REVISION, you MUST specify exactly 1-2 concrete things to add — be precise.

Format:
ASSESSMENT: [2-3 sentences on quality]
GAPS: [specific missing item, or "None"]
VERDICT: PASS

Always end with VERDICT: PASS or VERDICT: NEEDS_REVISION on its own line."""

def critic_agent(state: dict) -> dict:
    research  = state["research"]
    query     = state["query"]
    iteration = state.get("iteration", 0)

    if iteration >= 2:
        return {
            **state,
            "critique": "Analysis is sufficiently thorough after multiple iterations.",
            "verdict":  "PASS",
            "agent_logs": state.get("agent_logs", []) + [
                {"agent": "CRITIC", "message": "Max iterations reached — passing to Builder"}
            ]
        }

    messages = [
        SystemMessage(content=CRITIC_PROMPT),
        HumanMessage(content=f"Original Query: {query}\n\nResearcher's Analysis:\n{research}")
    ]
    response = get_llm().invoke(messages)
    critique = response.content
    verdict  = "NEEDS_REVISION" if "VERDICT: NEEDS_REVISION" in critique else "PASS"

    return {
        **state,
        "critique":  critique,
        "verdict":   verdict,
        "iteration": iteration + 1,
        "agent_logs": state.get("agent_logs", []) + [
            {"agent": "CRITIC", "message": f"Verdict: {verdict} — {'Sending back for revision' if verdict == 'NEEDS_REVISION' else 'Analysis approved'}"}
        ]
    }
