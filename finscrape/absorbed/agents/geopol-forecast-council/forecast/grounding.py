"""Grounding tool registry.

Each tool is a callable that takes (query, **kwargs) and returns a dict of the
shape:
    {"tool": "<name>", "ok": bool, "output": str, "items": list[dict], "error": str|None}

`output` is a human/LLM-readable block. `items` is optional structured detail
(used by the RSS tool for per-item headlines, Tavily for per-result records).
"""
from __future__ import annotations

import os
from typing import Callable

import httpx

from .config import OPENROUTER_URL, DEFAULT_RSS_FEEDS, GROUNDING_DOMAINS_IRAN_ISRAEL
from .rss import fetch_feeds, format_items


def rss_tool(query: str, feeds: list[str] | None = None, per_feed_limit: int = 15, max_items: int = 40) -> dict:
    feeds = feeds or DEFAULT_RSS_FEEDS
    try:
        items = fetch_feeds(feeds, per_feed_limit=per_feed_limit)
        output = format_items(items, max_items=max_items)
        return {"tool": "rss", "ok": True, "output": output, "items": items, "error": None}
    except Exception as e:
        return {"tool": "rss", "ok": False, "output": "", "items": [], "error": str(e)}


def sonar_tool(query: str) -> dict:
    try:
        body = {
            "model": "perplexity/sonar",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a neutral geopolitical news briefer. Given a forecast "
                        "scenario, produce a factual context pack: recent developments, "
                        "key actors, current positions, stated intentions, and relevant "
                        "counter-narratives in reporting. Plain prose, no markdown, no "
                        "opinions, no probability estimates. 500-700 words."
                    ),
                },
                {"role": "user", "content": query},
            ],
            "temperature": 0.2,
            "max_tokens": 1400,
        }
        r = httpx.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/danielrosehill/Geopol-Forecast-Council",
                "X-Title": "Geopol-Forecast-Council",
            },
            json=body,
            timeout=120.0,
        )
        r.raise_for_status()
        data = r.json()
        summary = data["choices"][0]["message"]["content"]
        cites = data.get("citations") or []
        urls: list[str] = []
        for c in cites:
            if isinstance(c, str):
                urls.append(c)
            elif isinstance(c, dict) and c.get("url"):
                urls.append(c["url"])
        items = [{"url": u} for u in urls]
        return {"tool": "sonar", "ok": True, "output": summary, "items": items, "error": None}
    except Exception as e:
        return {"tool": "sonar", "ok": False, "output": "", "items": [], "error": str(e)}


def tavily_tool(query: str, max_results: int = 8) -> dict:
    if not os.environ.get("TAVILY_API_KEY"):
        return {"tool": "tavily", "ok": False, "output": "", "items": [],
                "error": "TAVILY_API_KEY not set"}
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
        res = client.search(query=query, search_depth="advanced", max_results=max_results,
                            topic="news", days=7,
                            include_domains=GROUNDING_DOMAINS_IRAN_ISRAEL)
        results = res.get("results", [])
        lines = []
        items = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "").strip()
            url = r.get("url", "")
            content = (r.get("content") or "").strip().replace("\n", " ")[:400]
            date = r.get("published_date", "") or ""
            lines.append(f"[{i}] {date} | {title}\n    {url}\n    {content}")
            items.append({"title": title, "url": url, "snippet": content, "published": date})
        return {"tool": "tavily", "ok": True, "output": "\n\n".join(lines),
                "items": items, "error": None}
    except Exception as e:
        return {"tool": "tavily", "ok": False, "output": "", "items": [], "error": str(e)}


GROUNDING_TOOLS: dict[str, Callable[..., dict]] = {
    "rss": rss_tool,
    "sonar": sonar_tool,
    "tavily": tavily_tool,
}


def run_grounding(query: str, tools: list[str], rss_feeds: list[str] | None = None) -> list[dict]:
    """Invoke the named grounding tools in order. Unknown tools produce an error record."""
    out: list[dict] = []
    for name in tools:
        fn = GROUNDING_TOOLS.get(name)
        if fn is None:
            out.append({"tool": name, "ok": False, "output": "", "items": [],
                        "error": f"unknown grounding tool: {name}"})
            continue
        if name == "rss":
            out.append(fn(query, feeds=rss_feeds))
        else:
            out.append(fn(query))
    return out


def format_grounding_block(results: list[dict]) -> str:
    parts = []
    for r in results:
        header = f"## Grounding source: {r['tool']}"
        if not r["ok"]:
            parts.append(f"{header}\n\n(tool failed: {r.get('error','')})")
            continue
        parts.append(f"{header}\n\n{r['output']}")
    return "\n\n".join(parts)
