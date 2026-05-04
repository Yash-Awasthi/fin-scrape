"""
Local scrape server — triggers push_to_dashboard.py and proxies Ollama AI calls.

Runs on port 5001. Used by the dashboard's Refresh button and AI summary panel.

Endpoints:
  GET  /scrape          — trigger a fresh scrape + push to dashboard
  POST /ai-analyze      — proxy an AI prompt to local Ollama/Qwen
  GET  /health          — liveness check

Usage:
  python scrape_server.py
"""

from flask import Flask, jsonify, request
import subprocess
import sys
import os

try:
    import requests as req
except ImportError:
    req = None

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))

# Config from .env (with sensible localhost defaults)
DASHBOARD_URL  = os.getenv("FINSCRAPE_DASHBOARD_URL", "http://localhost:8787")
API_KEY        = os.getenv("FINSCRAPE_API_KEY",       "local-dev-key")
OLLAMA_URL     = os.getenv("OPENAI_BASE_URL",          "http://localhost:11434/v1")
OLLAMA_MODEL   = os.getenv("FINSCRAPE_MODEL",          "qwen2.5:7b")


@app.route("/health")
def health():
    return jsonify({"ok": True, "dashboard": DASHBOARD_URL, "model": OLLAMA_MODEL})


@app.route("/scrape")
def scrape():
    """Trigger push_to_dashboard.py as a background process."""
    age_hours = request.args.get("age_hours", "2")
    limit     = request.args.get("limit",     "30")

    # Cross-platform: use the same Python interpreter that's running this server
    python = sys.executable

    subprocess.Popen(
        [
            python, "push_to_dashboard.py",
            "--url",       DASHBOARD_URL,
            "--api-key",   API_KEY,
            "--age-hours", age_hours,
            "--limit",     limit,
        ],
        cwd=BASE,
    )
    return jsonify({"ok": True, "message": f"Scrape started → {DASHBOARD_URL}"})


@app.route("/ai-analyze", methods=["POST"])
def ai_analyze():
    """Proxy an AI prompt to the local Ollama instance."""
    if req is None:
        return jsonify({"error": "requests library not installed"}), 500

    data   = request.get_json(silent=True) or {}
    prompt = data.get("prompt", "")
    model  = data.get("model",  OLLAMA_MODEL)

    if not prompt:
        return jsonify({"error": "prompt field required"}), 400

    try:
        resp = req.post(
            f"{OLLAMA_URL}/chat/completions",
            json={
                "model":    model,
                "messages": [
                    {
                        "role":    "system",
                        "content": "You are a financial analyst. Always respond with valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens":  800,
                "format":      "json",
            },
            timeout=120,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"]
        return jsonify({"text": text})

    except Exception as e:
        return jsonify({"error": str(e)}), 502


if __name__ == "__main__":
    port = int(os.getenv("SCRAPE_SERVER_PORT", "5001"))
    print(f"Scrape server running on http://localhost:{port}")
    print(f"  Dashboard : {DASHBOARD_URL}")
    print(f"  Ollama    : {OLLAMA_URL}  model={OLLAMA_MODEL}")
    app.run(port=port, debug=False)
