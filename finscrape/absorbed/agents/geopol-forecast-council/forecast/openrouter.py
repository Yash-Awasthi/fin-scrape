import json
import os

import httpx

from .config import OPENROUTER_URL


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/danielrosehill/Geopol-Forecast-Council",
        "X-Title": "Geopol-Forecast-Council",
    }


def call(model: str, system: str, user: str, temperature: float = 0.3,
         timeout: float = 240.0, response_schema: dict | None = None) -> str:
    body: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
    }
    if response_schema is not None:
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": response_schema.get("name", "structured_output"),
                "strict": False,
                "schema": response_schema["schema"],
            },
        }
    r = httpx.post(OPENROUTER_URL, headers=_headers(), json=body, timeout=timeout)
    r.raise_for_status()
    content = r.json()["choices"][0]["message"].get("content")
    if not content:
        raise ValueError("empty content from model")
    return content


def _extract_json(raw: str) -> dict:
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON object in response: {raw[:400]}")
    return json.loads(raw[start : end + 1])


def call_json(model: str, system: str, user: str, temperature: float = 0.3,
              response_schema: dict | None = None) -> dict:
    """Call with optional structured-output schema.

    If the model or route doesn't honour `response_format`, we fall back to
    extracting the first JSON object from the raw text. If strict schema use
    fails outright, we retry once without it.
    """
    try:
        raw = call(model, system, user, temperature=temperature, response_schema=response_schema)
        return _extract_json(raw)
    except httpx.HTTPStatusError as e:
        if response_schema is not None and e.response.status_code in (400, 422):
            raw = call(model, system, user, temperature=temperature, response_schema=None)
            return _extract_json(raw)
        raise
    except ValueError:
        if response_schema is not None:
            raw = call(model, system, user, temperature=temperature, response_schema=None)
            return _extract_json(raw)
        raise
