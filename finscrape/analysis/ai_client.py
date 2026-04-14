"""
AI client for LLM-based financial event extraction via OpenRouter.
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
DEFAULT_MODEL = os.getenv("FINSCRAPE_MODEL", "deepseek/deepseek-chat")


def call_ai(prompt: str, system_prompt: str, model: str | None = None) -> dict | None:
    """
    Send a prompt to the LLM and return parsed JSON response.

    Returns None on any failure (network, parsing, invalid response).
    """
    api_key = OPENROUTER_API_KEY
    if not api_key:
        logger.error("OPENROUTER_API_KEY not set")
        return None

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
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

        data = response.json()
        if "choices" not in data:
            logger.error("AI response missing 'choices' key")
            return None

        content = data["choices"][0]["message"]["content"]

        # Extract JSON from response (may be wrapped in markdown)
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            return json.loads(match.group(0))

        return json.loads(content)

    except json.JSONDecodeError as e:
        logger.error("AI JSON parse error: %s", e)
        return None
    except requests.exceptions.RequestException as e:
        logger.error("AI request error: %s", e)
        return None
    except Exception as e:
        logger.error("AI unexpected error: %s", e)
        return None
