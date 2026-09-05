# agents/auditor.py
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

_llm = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
    return _llm

AUDITOR_PROMPT = """You are the Auditor agent in SENTINEL — a geopolitical market intelligence system.

Your job: review the generated Python code for correctness and usefulness.

Check for:
1. Syntax correctness (will it run without errors?)
2. Correct yfinance API usage
3. Logic correctness (does the scoring make sense?)
4. Completeness (does it actually answer the query?)
5. Professional quality (would a finance professional trust this output?)

Format your response as:
SYNTAX: PASS/FAIL — [reason]
API USAGE: PASS/FAIL — [reason]
LOGIC: PASS/FAIL — [reason]
COMPLETENESS: PASS/FAIL — [reason]
QUALITY: PASS/FAIL — [reason]

OVERALL: APPROVED/REJECTED
NOTES: [any specific issues found]"""

def auditor_agent(state: dict) -> dict:
    code  = state["generated_code"]
    query = state["query"]

    messages = [
        SystemMessage(content=AUDITOR_PROMPT),
        HumanMessage(content=f"Query: {query}\n\nGenerated Code:\n```python\n{code}\n```")
    ]
    response = get_llm().invoke(messages)
    audit    = response.content
    approved = "approved" in audit.lower()

    return {
        **state,
        "audit_report": audit,
        "approved":     approved,
        "agent_logs": state.get("agent_logs", []) + [
            {"agent": "AUDITOR", "message": f"Code review: {'APPROVED ✓' if approved else 'REJECTED ✗'} — reviewing quality and correctness"}
        ]
    }
