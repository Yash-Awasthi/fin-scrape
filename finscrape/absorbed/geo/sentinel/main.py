# main.py
import os
from dotenv import load_dotenv
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

import json
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from graph import app as sentinel_graph, initialize
from tools.mcp_tools import get_stock_data, calculate_risk_scores, DEFAULT_PORTFOLIO, LIVE_PRICE_TICKERS
from tools.data_fetcher import fetch_defense_news, fetch_ofac_sanctions

api = FastAPI(title="SENTINEL — Geopolitical Market Intelligence")
api.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "frontend")), name="static")

@api.get("/")
def root():
    return FileResponse(os.path.join(BASE_DIR, "frontend", "terminal.html"))

@api.get("/api/stocks")
def stocks():
    return get_stock_data(DEFAULT_PORTFOLIO)

@api.get("/api/universe")
def universe():
    from tools.mcp_tools import get_defense_universe_summary
    return get_defense_universe_summary()

@api.get("/api/news")
def news():
    return fetch_defense_news()

@api.get("/api/sanctions")
def sanctions():
    return fetch_ofac_sanctions(max_entries=20)

# Agent name → display label for streaming
AGENT_LABELS = {
    "rag_node":           ("SYSTEM",     "RAG retrieval + reranking…"),
    "enriched_researcher":("RESEARCHER", "Analyzing geopolitical impact…"),
    "critic_agent":       ("CRITIC",     "Stress-testing findings…"),
    "builder_agent":      ("BUILDER",    "Generating risk analysis tool…"),
    "auditor_agent":      ("AUDITOR",    "Reviewing generated code…"),
    "judge_agent":        ("JUDGE",      "Scoring session…"),
}

@api.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data    = await websocket.receive_text()
            payload = json.loads(data)
            query   = payload.get("query", "")
            if not query:
                continue

            await websocket.send_text(json.dumps({
                "type": "status", "message": f"Processing: {query}"
            }))

            initial_state = {
                "query": query, "rag_docs": [], "research": "",
                "critique": "", "verdict": "", "generated_code": "",
                "audit_report": "", "approved": False, "judgment": "",
                "score": 0, "iteration": 0, "agent_logs": []
            }

            result = None

            # ── TRUE STREAMING via astream_events ────────────────────────
            # Run the graph in a thread and stream node-level events back
            def run_graph_streaming():
                """Generator that yields (event_type, data) tuples."""
                import queue, threading
                q = queue.Queue()

                def _stream():
                    try:
                        for event in sentinel_graph.stream(
                            initial_state,
                            stream_mode="updates"
                        ):
                            q.put(("node", event))
                        q.put(("done", None))
                    except Exception as e:
                        q.put(("error", str(e)))

                t = threading.Thread(target=_stream, daemon=True)
                t.start()

                while True:
                    item = q.get()
                    yield item
                    if item[0] in ("done", "error"):
                        break

            final_state = {**initial_state}

            loop = asyncio.get_event_loop()
            stream_gen = await loop.run_in_executor(
                None, lambda: list(run_graph_streaming())
            )

            for event_type, event_data in stream_gen:
                if event_type == "error":
                    await websocket.send_text(json.dumps({
                        "type": "error", "message": event_data
                    }))
                    break

                if event_type == "node" and event_data:
                    # Each update is {node_name: state_dict}
                    for node_name, node_state in event_data.items():
                        final_state.update(node_state)

                        # Send streaming node update to frontend
                        label, status_msg = AGENT_LABELS.get(
                            node_name, ("SYSTEM", f"{node_name} complete")
                        )

                        # Pull latest agent log if available
                        logs = node_state.get("agent_logs", [])
                        log_msg = logs[-1]["message"] if logs else status_msg

                        await websocket.send_text(json.dumps({
                            "type":    "node_complete",
                            "node":    node_name,
                            "agent":   label,
                            "message": log_msg,
                            # Stream partial results as each agent finishes
                            "partial": {
                                "research":       node_state.get("research", ""),
                                "critique":       node_state.get("critique", ""),
                                "generated_code": node_state.get("generated_code", ""),
                                "audit_report":   node_state.get("audit_report", ""),
                                "judgment":       node_state.get("judgment", ""),
                                "score":          node_state.get("score", 0),
                            }
                        }))

            # Send final complete result
            keywords  = query.lower().split()
            risk_data = calculate_risk_scores(
                DEFAULT_PORTFOLIO,
                keywords
            )

            await websocket.send_text(json.dumps({
                "type":           "complete",
                "research":       final_state.get("research", ""),
                "critique":       final_state.get("critique", ""),
                "generated_code": final_state.get("generated_code", ""),
                "audit_report":   final_state.get("audit_report", ""),
                "judgment":       final_state.get("judgment", ""),
                "score":          final_state.get("score", 0),
                "risk_data":      risk_data,
                "rag_docs":       final_state.get("rag_docs", [])
            }))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except:
            pass

@api.on_event("startup")
async def startup():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, initialize)

if __name__ == "__main__":
    uvicorn.run("main:api", host="0.0.0.0", port=8000, reload=False)
