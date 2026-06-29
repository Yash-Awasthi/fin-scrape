"""Telegram bot webhook + outbound verdict alerts (Phase 13).

`POST /api/telegram/webhook` ALWAYS returns 200 immediately (Telegram retries otherwise)
and processes the command off the request path. Outbound INVEST/PULL_OUT alerts reuse the
finscrape alert message format and fan out to subscribers. Everything no-ops gracefully
when no `TELEGRAM_BOT_TOKEN` is set, so the rest of the app is unaffected.

Subscribers (chat_ids) persist to `<data_dir>/telegram_subs.json` — no schema, no DB.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import requests
from fastapi import APIRouter, BackgroundTasks, Body

from server import queries
from server import db
from server.settings import get_settings

log = logging.getLogger("worldfin.telegram")
router = APIRouter()

_HELP = (
    "WorldFin bot commands:\n"
    "/subscribe — get INVEST/PULL_OUT alerts\n"
    "/unsubscribe — stop alerts\n"
    "/status — subscription + alert status\n"
    "/latest — most recent signals"
)


def _subs_path() -> Path:
    d = Path(get_settings().data_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d / "telegram_subs.json"


def _load_subs() -> set[str]:
    try:
        return set(json.loads(_subs_path().read_text()))
    except (OSError, ValueError):
        return set()


def _save_subs(subs: set[str]) -> None:
    try:
        _subs_path().write_text(json.dumps(sorted(subs)))
    except OSError as exc:  # pragma: no cover - disk full / read-only
        log.warning("telegram subs save failed: %s", exc)


def send_message(chat_id: str | int, text: str) -> bool:
    """POST a message to a chat. No-op (False) when no bot token configured."""
    token = get_settings().telegram_bot_token
    if not token or not chat_id:
        return False
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=10,
        )
        return resp.status_code == 200
    except requests.RequestException as exc:  # pragma: no cover - network
        log.warning("telegram send failed: %s", exc)
        return False


def format_alert(event: dict) -> str:
    """Same shape as finscrape.alerts AlertEngine._send_telegram_alert."""
    score = event.get("signal_score", 0)
    arrow = "+" if score >= 0 else ""
    text = (
        f"🚨 *{event.get('verdict', '?')}* ({arrow}{score}) — "
        f"{event.get('confidence', 0):.0%} confidence\n"
        f"Tickers: `{', '.join(event.get('tickers', []))}`\n"
        f"{event.get('subject', 'Unknown event')}"
    )
    reasoning = (event.get("reasoning") or "")[:200]
    return text + (f"\n_{reasoning}_" if reasoning else "")


def notify_new_events(events: list[dict]) -> int:
    """Send directional (INVEST/PULL_OUT) events to all subscribers. Returns sends made."""
    if not get_settings().telegram_bot_token:
        return 0
    subs = _load_subs()
    if not subs:
        return 0
    sent = 0
    for ev in events:
        if ev.get("verdict") not in ("INVEST", "PULL_OUT"):
            continue
        msg = format_alert(ev)
        for chat_id in subs:
            if send_message(chat_id, msg):
                sent += 1
    return sent


async def _handle_command(chat_id: str, text: str) -> None:
    cmd = (
        text.strip().split()[0].lower().lstrip("/").split("@")[0]
        if text.strip()
        else ""
    )
    if cmd in ("start", "help"):
        send_message(chat_id, _HELP)
    elif cmd == "subscribe":
        subs = _load_subs()
        subs.add(str(chat_id))
        _save_subs(subs)
        send_message(chat_id, "✅ Subscribed to INVEST/PULL_OUT alerts.")
    elif cmd == "unsubscribe":
        subs = _load_subs()
        subs.discard(str(chat_id))
        _save_subs(subs)
        send_message(chat_id, "Unsubscribed.")
    elif cmd == "status":
        subbed = str(chat_id) in _load_subs()
        send_message(chat_id, f"Alerts: {'on' if subbed else 'off'}.")
    elif cmd == "latest":
        rows = await queries.get_events(db.pool(), limit=5)
        lines = [f"• {r['verdict']} {r['subject']}" for r in rows] or [
            "No signals yet."
        ]
        send_message(chat_id, "Latest signals:\n" + "\n".join(lines))


@router.post("/api/telegram/webhook")
async def webhook(background: BackgroundTasks, update: dict = Body(default={})) -> dict:
    """Always 200. Command handling runs in the background so Telegram never retries."""
    msg = (update or {}).get("message") or {}
    chat_id = str((msg.get("chat") or {}).get("id") or "")
    text = msg.get("text") or ""
    if chat_id and text.startswith("/"):
        background.add_task(_handle_command, chat_id, text)
    return {"ok": True}
