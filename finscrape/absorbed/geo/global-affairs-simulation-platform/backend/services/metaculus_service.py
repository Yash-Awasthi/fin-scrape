"""
Metaculus 外部预测对接 - 获取公开预测市场数据用于校准对比
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional

import httpx

logger = logging.getLogger("metaculus")

METACULUS_API_BASE = "https://www.metaculus.com/api2"

SEARCH_KEYWORDS = {
    "military_escalation": ["military", "war", "conflict", "invasion"],
    "diplomatic_negotiation": ["diplomacy", "treaty", "negotiation", "sanctions"],
    "economic_coercion": ["sanctions", "trade war", "tariff", "economy"],
    "energy_shipping_risk": ["oil", "energy", "shipping", "pipeline"],
    "alliance_realignment": ["NATO", "alliance", "treaty", "partnership"],
    "domestic_political_spillover": ["election", "protest", "coup", "regime"],
    "information_psychological_operations": ["disinformation", "cyber", "propaganda"],
}


async def search_predictions(
    event_type: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 10,
) -> List[Dict]:
    params = {
        "limit": min(limit, 20),
        "order_by": "-published_at",
        "status": "open",
    }
    if query:
        params["search"] = query
    elif event_type and event_type in SEARCH_KEYWORDS:
        keywords = SEARCH_KEYWORDS[event_type]
        params["search"] = " ".join(keywords[:2])

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{METACULUS_API_BASE}/questions/", params=params)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            return [_format_question(q) for q in results[:limit]]
    except Exception as e:
        logger.warning(f"[metaculus] 搜索失败: {e}")
        return []


async def get_prediction(question_id: int) -> Optional[Dict]:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{METACULUS_API_BASE}/questions/{question_id}/")
            resp.raise_for_status()
            return _format_question(resp.json())
    except Exception as e:
        logger.warning(f"[metaculus] 获取预测 {question_id} 失败: {e}")
        return None


def _format_question(q: Dict) -> Dict:
    community_prediction = q.get("community_prediction", {})
    full = community_prediction.get("full", {})

    return {
        "id": q.get("id"),
        "title": q.get("title", ""),
        "short_title": q.get("short_title", ""),
        "url": f"https://www.metaculus.com/questions/{q.get('id')}",
        "published_at": q.get("published_at", ""),
        "resolve_by": q.get("resolve_by", ""),
        "prediction_type": q.get("prediction_type", ""),
        "community_median": full.get("median"),
        "community_mean": full.get("mean"),
        "community_q1": full.get("q1"),
        "community_q3": full.get("q3"),
        "comment_count": q.get("comment_count", 0),
        "votes": q.get("votes", 0),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
