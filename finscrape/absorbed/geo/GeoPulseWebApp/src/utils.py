import json
import re
import plotly.graph_objects as go
from openai import OpenAI

def get_color(score):
    # Try converting score to numeric to prevent TypeErrors in comparisons
    try:
        if score is None:
            return "#7f8c8d" # Fallback professional slate
        score = float(score)
    except (ValueError, TypeError):
        return "#7f8c8d" # Fallback professional slate

    # 0 (Peace) -> 100 (War)
    if score < 20: return "#27ae60" # Emerald
    if score < 40: return "#f1c40f" # Yellow
    if score < 60: return "#f39c12" # Orange
    if score < 80: return "#e67e22" # Dark Orange
    return "#c0392b" # Red

def create_gauge(current, past):
    # Visualizes Current Score with a 'Reference' bar for the Past Score
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = current,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "TENSION INDEX", 'font': {'size': 18, 'color': '#7f8c8d'}},
        delta = {'reference': past, 'increasing': {'color': "#c0392b"}, 'decreasing': {'color': "#27ae60"}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#bdc3c7"},
            'bar': {'color': get_color(current)},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#ecf0f1",
            'steps': [
                {'range': [0, 20], 'color': '#e9f7ef'},
                {'range': [20, 100], 'color': '#fff'}],
            'threshold': {'line': {'color': "#c0392b", 'width': 4}, 'thickness': 0.75, 'value': current}
        }))
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)', font={'family': "Arial"})
    return fig

def clean_json(text):
    # Check for safety filter refusals
    lower_text = text.lower()
    if "i'm sorry" in lower_text or "cannot fulfill" in lower_text or "as an ai" in lower_text:
        return {"error": "Simulation Blocked: The AI model's safety filters prevented it from analyzing this geopolitical scenario."}
        
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if match: return json.loads(match.group(1))
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match: return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
        # Return a structured error dict — consistent with all other API functions
        return {"error": "Failed to parse AI response as JSON."}

def sanitize_input(text, max_len=50):
    """Sanitize user input to prevent basic LLM prompt injection."""
    if not text: return ""
    # Allow alphanumeric, spaces, dashes, periods, apostrophes, commas, and ampersands
    # (needed for valid country names like "Cote d'Ivoire", "Korea, South", "Bosnia & Herzegovina")
    sanitized = re.sub(r"[^a-zA-Z0-9 \.\-',&]", '', str(text))
    return sanitized[:max_len].strip()

def _make_client(key: str, base_url):
    """Construct and return a configured OpenAI-compatible client."""
    kwargs = {"api_key": key}
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)
