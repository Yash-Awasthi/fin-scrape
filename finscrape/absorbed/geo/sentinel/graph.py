# graph.py
from langgraph.graph import StateGraph, END
from typing import TypedDict
from agents.researcher import researcher_agent
from agents.critic     import critic_agent
from agents.builder    import builder_agent
from agents.auditor    import auditor_agent
from agents.judge      import judge_agent
from rag.retriever     import retrieve, seed_from_real_sources
from reranker.model    import rerank

class SentinelState(TypedDict):
    query:          str
    rag_docs:       list
    research:       str
    critique:       str
    verdict:        str
    generated_code: str
    audit_report:   str
    approved:       bool
    judgment:       str
    score:          int
    iteration:      int
    agent_logs:     list

def rag_node(state: SentinelState) -> SentinelState:
    query    = state["query"]
    raw_docs = retrieve(query, n_results=8)
    reranked = rerank(query, raw_docs)
    top_docs = reranked[:5]

    return {
        **state,
        "rag_docs": top_docs,
        "agent_logs": state.get("agent_logs", []) + [
            {"agent": "SYSTEM", "message": f"Retrieved {len(raw_docs)} docs → re-ranker selected top {len(top_docs)}"}
        ]
    }

def enriched_researcher(state: SentinelState) -> SentinelState:
    """Inject RAG context into researcher, but preserve original query in logs."""
    original_query = state["query"]  # save BEFORE enrichment

    rag_context = "\n\n".join([
        f"[Document {d['rank']} — Relevance: {d.get('rerank_score', 0):.2f}]\n{d['text']}"
        for d in state.get("rag_docs", [])
    ])

    enriched_state = {
        **state,
        "query": f"{original_query}\n\n[RELEVANT CONTEXT FROM KNOWLEDGE BASE]\n{rag_context}"
    }

    result = researcher_agent(enriched_state)

    # Restore clean original query and fix log message
    result["query"] = original_query
    logs = result.get("agent_logs", [])
    if logs:
        logs[-1]["message"] = f"Analysis complete — identified key affected entities for: {original_query[:80]}"

    return result

def should_revise(state: SentinelState) -> str:
    if state.get("verdict") == "NEEDS_REVISION":
        return "researcher"
    return "builder"

def build_graph():
    graph = StateGraph(SentinelState)

    graph.add_node("rag",        rag_node)
    graph.add_node("researcher", enriched_researcher)
    graph.add_node("critic",     critic_agent)
    graph.add_node("builder",    builder_agent)
    graph.add_node("auditor",    auditor_agent)
    graph.add_node("judge",      judge_agent)

    graph.set_entry_point("rag")
    graph.add_edge("rag",        "researcher")
    graph.add_edge("researcher", "critic")

    graph.add_conditional_edges(
        "critic",
        should_revise,
        {"researcher": "researcher", "builder": "builder"}
    )

    graph.add_edge("builder", "auditor")
    graph.add_edge("auditor", "judge")
    graph.add_edge("judge",   END)

    return graph.compile()

def initialize():
    seed_from_real_sources()
    from reranker.model import load_model
    load_model()
    print("[SENTINEL] System ready")

app = build_graph()
