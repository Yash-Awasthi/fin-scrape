# agents/judge.py
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

JUDGE_PROMPT = """You are the Judge agent in SENTINEL — a geopolitical market intelligence system.

Your job: score the entire session and produce a final summary report.

Evaluate:
- Research quality (0-25): How thorough and accurate was the analysis?
- Critique quality (0-25): Did the Critic improve the analysis?
- Tool quality (0-25): Is the generated code actually useful?
- Overall relevance (0-25): Does the output actually answer the query?

Format your response as:
RESEARCH SCORE: [0-25] — [reason]
CRITIQUE SCORE: [0-25] — [reason]
TOOL SCORE: [0-25] — [reason]
RELEVANCE SCORE: [0-25] — [reason]
TOTAL SCORE: [0-100]

EXECUTIVE SUMMARY:
[3-4 sentence summary of the key findings and what the tool does]

KEY TICKERS TO WATCH:
- [TICKER]: [one line reason]

RISK LEVEL: HIGH/MEDIUM/LOW"""

def judge_agent(state: dict) -> dict:
    messages = [
        SystemMessage(content=JUDGE_PROMPT),
        HumanMessage(content=f"""
Query: {state['query']}

Research: {state['research'][:1000]}...

Critique: {state.get('critique', 'N/A')[:500]}...

Generated Tool: {len(state.get('generated_code', '').splitlines())} lines of Python code

Audit: {state.get('audit_report', 'N/A')[:300]}...
""")
    ]
    response = get_llm().invoke(messages)
    judgment = response.content

    score = 75
    match = re.search(r'TOTAL SCORE:\s*(\d+)', judgment)
    if match:
        score = int(match.group(1))

    return {
        **state,
        "judgment": judgment,
        "score":    score,
        "agent_logs": state.get("agent_logs", []) + [
            {"agent": "JUDGE", "message": f"Session scored: {score}/100 — analysis complete"}
        ]
    }
