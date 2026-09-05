# agents/builder.py
import os, re
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

BUILDER_PROMPT = """You are the Builder agent in SENTINEL — a geopolitical market intelligence system.

Your job: take the verified research and produce a WORKING Python tool a defense-finance professional can run immediately.

Rules:
- Use yfinance for stock data (import yfinance as yf)
- Use only standard libraries + yfinance + requests
- The script must be complete and runnable as-is
- Include real ticker symbols from the research
- Include a risk scoring function
- Print a clean formatted report
- Add a timestamp
- NO placeholder comments like "# add your logic here"

The tool should:
1. Fetch live prices for affected tickers
2. Calculate an exposure/risk score based on the event
3. Print a formatted report with risk levels (HIGH/MEDIUM/LOW)
4. Identify top risks and opportunities

Output ONLY the Python code. No explanation before or after."""

def builder_agent(state: dict) -> dict:
    research = state["research"]
    critique = state.get("critique", "")
    query    = state["query"]

    messages = [
        SystemMessage(content=BUILDER_PROMPT),
        HumanMessage(content=f"""
Query: {query}

Verified Research:
{research}

Critic's Notes:
{critique}

Generate a complete, runnable Python tool for this analysis.
""")
    ]
    response = get_llm().invoke(messages)
    raw = response.content

    code_match = re.search(r'```python\n(.*?)```', raw, re.DOTALL)
    code = code_match.group(1).strip() if code_match else raw.strip()

    return {
        **state,
        "generated_code": code,
        "agent_logs": state.get("agent_logs", []) + [
            {"agent": "BUILDER", "message": f"Tool generated — {len(code.splitlines())} lines of runnable Python"}
        ]
    }
