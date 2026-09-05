from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser


def _parse_dt(entry) -> datetime | None:
    for key in ("published", "updated"):
        val = entry.get(key)
        if not val:
            continue
        try:
            dt = parsedate_to_datetime(val)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (TypeError, ValueError):
            continue
    return None


def fetch_feeds(urls: list[str], per_feed_limit: int = 15) -> list[dict]:
    """Fetch RSS feeds, return flat list of items sorted newest-first."""
    items: list[dict] = []
    for url in urls:
        try:
            parsed = feedparser.parse(url)
        except Exception as e:
            items.append({"_error": f"{url}: {e}", "feed": url})
            continue
        feed_title = parsed.feed.get("title", url)
        for entry in parsed.entries[:per_feed_limit]:
            items.append(
                {
                    "feed": feed_title,
                    "feed_url": url,
                    "title": entry.get("title", "").strip(),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", "").strip(),
                    "published_raw": entry.get("published") or entry.get("updated") or "",
                    "published": _parse_dt(entry),
                }
            )
    items.sort(key=lambda i: i.get("published") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return items


def format_items(items: list[dict], max_items: int = 40, summary_chars: int = 400) -> str:
    lines = []
    for i, it in enumerate(items[:max_items], start=1):
        if it.get("_error"):
            lines.append(f"[{i}] FEED ERROR: {it['_error']}")
            continue
        ts = it["published"].isoformat() if it.get("published") else it.get("published_raw", "?")
        summary = (it.get("summary") or "").replace("\n", " ")[:summary_chars]
        lines.append(
            f"[{i}] {ts} | {it['feed']}\n"
            f"    {it['title']}\n"
            f"    {it['link']}\n"
            f"    {summary}"
        )
    return "\n\n".join(lines)
