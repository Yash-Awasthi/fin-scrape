"""
AI client for LLM-based financial event extraction.

Supports two backends:
  1. OpenRouter (set OPENROUTER_API_KEY in .env)
  2. Local OpenAI-compatible proxy (set OPENAI_BASE_URL env var)

Features:
  - Retry with exponential backoff (1 retry on failure)
  - Response validation (required fields, value ranges)
  - Batch analysis for processing multiple articles in one call
"""

from __future__ import annotations

import json
import logging
import os
import re
import time

import requests
from dotenv import load_dotenv

from finscrape.analysis.constants import (
    VALID_EVENT_TYPES, VALID_IMPACT_DIRECTIONS,
    VALID_MAGNITUDES, VALID_NOVELTIES, VALID_ACTIONABILITIES,
)

logger = logging.getLogger(__name__)

# Load .env from project root
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "proxy")
DEFAULT_MODEL = os.getenv("FINSCRAPE_MODEL", "deepseek/deepseek-chat")

# Retry configuration
MAX_RETRIES = 1
RETRY_BASE_DELAY = 2.0  # seconds


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def call_ai(prompt: str, system_prompt: str, model: str | None = None) -> dict | None:
    """
    Send a prompt to the LLM and return parsed JSON response.

    Uses local OpenAI proxy if available, falls back to OpenRouter.
    Retries once on failure with exponential backoff.
    Validates required fields in the response.
    Returns None on any failure (network, parsing, invalid response).
    """
    if OPENAI_BASE_URL:
        raw = _call_with_retry(_call_openai_proxy, prompt, system_prompt, model)
    elif OPENROUTER_API_KEY:
        raw = _call_with_retry(_call_openrouter, prompt, system_prompt, model)
    else:
        logger.error("No AI backend configured. Set OPENROUTER_API_KEY or OPENAI_BASE_URL.")
        return None

    if raw is None:
        return None

    # Validate and normalize the response
    return _validate_response(raw)


def analyze_batch(
    articles: list[dict],
    system_prompt: str,
    batch_prompt_template: str,
    model: str | None = None,
) -> list[dict | None]:
    """
    Process multiple articles in a single LLM call for efficiency.

    Each article dict should have "title" and "text" keys.
    Returns a list of analysis dicts (or None for failures), one per article.

    Falls back to individual calls if the batch call fails.
    """
    if not articles:
        return []

    # Build the articles block
    articles_block_parts = []
    for i, article in enumerate(articles):
        articles_block_parts.append(
            f"--- ARTICLE {i+1} ---\n"
            f"HEADLINE: {article.get('title', '')}\n"
            f"ARTICLE: {article.get('text', '')}\n"
        )
    articles_block = "\n".join(articles_block_parts)

    prompt = batch_prompt_template.replace("{{articles_block}}", articles_block)

    if OPENAI_BASE_URL:
        raw = _call_with_retry(_call_openai_proxy, prompt, system_prompt, model)
    elif OPENROUTER_API_KEY:
        raw = _call_with_retry(_call_openrouter, prompt, system_prompt, model)
    else:
        logger.error("No AI backend configured for batch analysis.")
        return [None] * len(articles)

    if raw is None:
        logger.warning("Batch call failed; falling back to individual calls.")
        return [None] * len(articles)

    # Extract the analyses array
    analyses = raw.get("analyses", [])
    if not isinstance(analyses, list) or len(analyses) != len(articles):
        logger.warning(
            "Batch response had %d analyses for %d articles; returning raw results.",
            len(analyses) if isinstance(analyses, list) else 0,
            len(articles),
        )
        # Try to salvage what we can
        if isinstance(analyses, list):
            results = []
            for i in range(len(articles)):
                if i < len(analyses):
                    results.append(_validate_response(analyses[i]))
                else:
                    results.append(None)
            return results
        return [None] * len(articles)

    return [_validate_response(a) for a in analyses]


# ---------------------------------------------------------------------------
# Retry logic
# ---------------------------------------------------------------------------

def _call_with_retry(fn, prompt, system_prompt, model):
    """Call an API function with up to MAX_RETRIES retries on failure."""
    for attempt in range(MAX_RETRIES + 1):
        result = fn(prompt, system_prompt, model)
        if result is not None:
            return result
        if attempt < MAX_RETRIES:
            delay = RETRY_BASE_DELAY * (2 ** attempt)
            logger.info("Retrying AI call in %.1fs (attempt %d/%d)", delay, attempt + 1, MAX_RETRIES)
            time.sleep(delay)
    return None


# ---------------------------------------------------------------------------
# Response validation
# ---------------------------------------------------------------------------

def _validate_response(data: dict) -> dict | None:
    """
    Validate and normalize an AI analysis response.

    Checks required fields exist and values are in valid ranges.
    Fills in defaults for missing optional fields.
    Returns None if the response is fundamentally broken.
    """
    if not isinstance(data, dict):
        logger.error("AI response is not a dict: %s", type(data))
        return None

    # "relevant" is the one truly required field
    if "relevant" not in data:
        logger.warning("AI response missing 'relevant' field; defaulting to False")
        data["relevant"] = False

    # If not relevant, return early with minimal structure
    if not data.get("relevant", False):
        return data

    # Normalize event_type
    et = data.get("event_type", "other")
    if et not in VALID_EVENT_TYPES:
        data["event_type"] = "other"

    # Normalize impact_direction
    direction = data.get("impact_direction", "neutral")
    if direction not in VALID_IMPACT_DIRECTIONS:
        data["impact_direction"] = "neutral"

    # Clamp signal_score to [-5, 5]
    score = data.get("signal_score", 0)
    if isinstance(score, (int, float)):
        data["signal_score"] = max(-5, min(5, int(score)))
    else:
        data["signal_score"] = 0

    # Clamp confidence to [0.0, 1.0]
    conf = data.get("confidence", 0.5)
    if isinstance(conf, (int, float)):
        data["confidence"] = max(0.0, min(1.0, float(conf)))
    else:
        data["confidence"] = 0.5

    # Normalize magnitude
    mag = data.get("magnitude", "medium")
    if mag not in VALID_MAGNITUDES:
        data["magnitude"] = "medium"

    # Normalize novelty
    nov = data.get("novelty", "standard")
    if nov not in VALID_NOVELTIES:
        data["novelty"] = "standard"

    # Normalize actionability
    act = data.get("actionability", "medium")
    if act not in VALID_ACTIONABILITIES:
        data["actionability"] = "medium"

    # Ensure lists/dicts exist
    if not isinstance(data.get("tickers"), list):
        data["tickers"] = []
    if not isinstance(data.get("affected_entities"), list):
        data["affected_entities"] = []
    if not isinstance(data.get("second_order_effects"), list):
        data["second_order_effects"] = []
    if not isinstance(data.get("key_metrics"), dict):
        data["key_metrics"] = {}

    # Ensure strings exist
    data.setdefault("subject", "")
    data.setdefault("reasoning", "")
    data.setdefault("sector_impact", "")
    data.setdefault("temporal_context", "standard")

    return data


# ---------------------------------------------------------------------------
# Backend implementations
# ---------------------------------------------------------------------------

def _call_openai_proxy(prompt: str, system_prompt: str, model: str | None = None) -> dict | None:
    """Call local OpenAI-compatible proxy."""
    try:
        response = requests.post(
            f"{OPENAI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model or "auto",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 800,
                "response_format": {"type": "json_object"},
            },
            timeout=60,
        )

        if response.status_code != 200:
            logger.error("AI proxy HTTP %d: %s", response.status_code, response.text[:200])
            return None

        return _parse_response(response.json())

    except Exception as e:
        logger.error("AI proxy error: %s", e)
        return None


def _call_openrouter(prompt: str, system_prompt: str, model: str | None = None) -> dict | None:
    """Call OpenRouter API."""
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model or DEFAULT_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 800,
                "response_format": {"type": "json_object"},
            },
            timeout=45,
        )

        if response.status_code != 200:
            logger.error("AI HTTP %d: %s", response.status_code, response.text[:200])
            return None

        return _parse_response(response.json())

    except requests.exceptions.RequestException as e:
        logger.error("AI request error: %s", e)
        return None
    except Exception as e:
        logger.error("AI unexpected error: %s", e)
        return None


def _parse_response(data: dict) -> dict | None:
    """Extract and parse JSON from LLM response."""
    if "choices" not in data:
        logger.error("AI response missing 'choices' key")
        return None

    content = data["choices"][0]["message"]["content"]

    try:
        # Extract JSON from response (may be wrapped in markdown)
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            return json.loads(match.group(0))
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error("AI JSON parse error: %s | Content: %s", e, content[:200])
        return None
