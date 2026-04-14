"""
AI client for LLM-based financial event extraction.

Supports two backends:
  1. OpenRouter (set OPENROUTER_API_KEY in .env)
  2. Local OpenAI-compatible proxy (set OPENAI_BASE_URL env var)
"""

from __future__ import annotations

import json
import logging
import os
import re

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env from project root
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "proxy")
DEFAULT_MODEL = os.getenv("FINSCRAPE_MODEL", "deepseek/deepseek-chat")


def call_ai(prompt: str, system_prompt: str, model: str | None = None) -> dict | None:
    """
    Send a prompt to the LLM and return parsed JSON response.

    Uses local OpenAI proxy if available, falls back to OpenRouter.
    Returns None on any failure (network, parsing, invalid response).
    """
    if OPENAI_BASE_URL:
        return _call_openai_proxy(prompt, system_prompt, model)
    elif OPENROUTER_API_KEY:
        return _call_openrouter(prompt, system_prompt, model)
    else:
        logger.error("No AI backend configured. Set OPENROUTER_API_KEY or OPENAI_BASE_URL.")
        return None


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
                "max_tokens": 400,
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
