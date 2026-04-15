"""
Alert rules engine for FinScrape.

Lets users define conditions like "notify me when any FAANG stock gets
PULL_OUT verdict" or "alert on any INVEST signal with confidence > 80%".

Rules are persisted in SQLite alongside the main finscrape.db data.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Condition:
    """A single condition that checks one event field."""

    field: str  # verdict, signal_score, confidence, tickers, event_type, sector_impact, magnitude, sources
    operator: str  # eq, neq, gt, gte, lt, lte, in, contains, not_in
    value: Any

    VALID_FIELDS = frozenset({
        "verdict", "signal_score", "confidence", "tickers",
        "event_type", "sector_impact", "magnitude", "sources",
    })
    VALID_OPERATORS = frozenset({
        "eq", "neq", "gt", "gte", "lt", "lte", "in", "contains", "not_in",
    })

    def __post_init__(self) -> None:
        if self.field not in self.VALID_FIELDS:
            raise ValueError(f"Invalid condition field: {self.field!r}")
        if self.operator not in self.VALID_OPERATORS:
            raise ValueError(f"Invalid operator: {self.operator!r}")

    def evaluate(self, event: dict) -> bool:
        """Return True if the event satisfies this condition."""
        event_value = event.get(self.field)
        if event_value is None:
            return False

        op = self.operator
        target = self.value

        if op == "eq":
            return event_value == target
        elif op == "neq":
            return event_value != target
        elif op in ("gt", "gte", "lt", "lte"):
            try:
                ev = float(event_value)
                tv = float(target)
            except (ValueError, TypeError):
                return False
            if op == "gt":
                return ev > tv
            elif op == "gte":
                return ev >= tv
            elif op == "lt":
                return ev < tv
            else:
                return ev <= tv
        elif op == "in":
            # target is a list; event_value must be one of them
            return event_value in target
        elif op == "contains":
            # event_value is a list (e.g. tickers); check if target is in it
            if isinstance(event_value, list):
                if isinstance(target, list):
                    return any(t in event_value for t in target)
                return target in event_value
            # string containment fallback
            return str(target) in str(event_value)
        elif op == "not_in":
            return event_value not in target

        return False

    def to_dict(self) -> dict:
        return {"field": self.field, "operator": self.operator, "value": self.value}

    @classmethod
    def from_dict(cls, data: dict) -> Condition:
        return cls(field=data["field"], operator=data["operator"], value=data["value"])


@dataclass
class Action:
    """An action to fire when a rule matches."""

    action_type: str  # telegram, dashboard_push, log, webhook
    config: dict = field(default_factory=dict)

    VALID_TYPES = frozenset({"telegram", "dashboard_push", "log", "webhook"})

    def __post_init__(self) -> None:
        if self.action_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid action type: {self.action_type!r}")

    def to_dict(self) -> dict:
        return {"action_type": self.action_type, "config": self.config}

    @classmethod
    def from_dict(cls, data: dict) -> Action:
        return cls(action_type=data["action_type"], config=data.get("config", {}))


@dataclass
class AlertRule:
    """A named rule combining conditions (AND-logic) with actions."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = ""
    conditions: list[Condition] = field(default_factory=list)
    actions: list[Action] = field(default_factory=list)
    enabled: bool = True
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def matches(self, event: dict) -> bool:
        """Return True if ALL conditions are satisfied (AND logic)."""
        if not self.conditions:
            return False
        return all(c.evaluate(event) for c in self.conditions)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "conditions": [c.to_dict() for c in self.conditions],
            "actions": [a.to_dict() for a in self.actions],
            "enabled": self.enabled,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> AlertRule:
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            conditions=[Condition.from_dict(c) for c in data.get("conditions", [])],
            actions=[Action.from_dict(a) for a in data.get("actions", [])],
            enabled=data.get("enabled", True),
            created_at=data.get("created_at", ""),
        )


# ---------------------------------------------------------------------------
# Alert engine
# ---------------------------------------------------------------------------

class AlertEngine:
    """Evaluate events against user-defined alert rules.

    Rules are persisted in the ``alert_rules`` SQLite table.
    """

    def __init__(self, db_path: str | Path | None = None):
        if db_path is None:
            project_root = Path(__file__).resolve().parent.parent
            db_path = project_root / "data" / "finscrape.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_table()
        self._rules_cache: list[AlertRule] | None = None

    # -- schema --------------------------------------------------------------

    def _init_table(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS alert_rules (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                conditions TEXT NOT NULL DEFAULT '[]',
                actions TEXT NOT NULL DEFAULT '[]',
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        self._conn.commit()

    # -- CRUD ----------------------------------------------------------------

    def add_rule(
        self,
        name: str,
        conditions: list[Condition],
        actions: list[Action] | None = None,
    ) -> str:
        """Create a new alert rule and return its ID."""
        if actions is None:
            actions = [Action(action_type="log")]
        rule = AlertRule(
            name=name,
            conditions=conditions,
            actions=actions,
        )
        self._conn.execute(
            "INSERT INTO alert_rules (id, name, conditions, actions, enabled, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                rule.id,
                rule.name,
                json.dumps([c.to_dict() for c in rule.conditions]),
                json.dumps([a.to_dict() for a in rule.actions]),
                1 if rule.enabled else 0,
                rule.created_at,
            ),
        )
        self._conn.commit()
        logger.info("Added alert rule %s: %s", rule.id, rule.name)
        self._rules_cache = None  # invalidate cache
        return rule.id

    def remove_rule(self, rule_id: str) -> bool:
        """Delete a rule. Returns True if a row was removed."""
        cur = self._conn.execute("DELETE FROM alert_rules WHERE id = ?", (rule_id,))
        self._conn.commit()
        self._rules_cache = None  # invalidate cache
        removed = cur.rowcount > 0
        if removed:
            logger.info("Removed alert rule %s", rule_id)
        return removed

    def enable_rule(self, rule_id: str) -> None:
        self._conn.execute("UPDATE alert_rules SET enabled = 1 WHERE id = ?", (rule_id,))
        self._conn.commit()
        self._rules_cache = None

    def disable_rule(self, rule_id: str) -> None:
        self._conn.execute("UPDATE alert_rules SET enabled = 0 WHERE id = ?", (rule_id,))
        self._conn.commit()
        self._rules_cache = None

    def get_rules(self) -> list[AlertRule]:
        """Return all rules (enabled and disabled). Cached until mutation."""
        if self._rules_cache is not None:
            return self._rules_cache
        rows = self._conn.execute(
            "SELECT id, name, conditions, actions, enabled, created_at FROM alert_rules"
        ).fetchall()
        rules: list[AlertRule] = []
        for row in rows:
            rules.append(AlertRule(
                id=row[0],
                name=row[1],
                conditions=[Condition.from_dict(c) for c in json.loads(row[2])],
                actions=[Action.from_dict(a) for a in json.loads(row[3])],
                enabled=bool(row[4]),
                created_at=row[5],
            ))
        self._rules_cache = rules
        return rules

    def get_rule(self, rule_id: str) -> AlertRule | None:
        """Return a single rule by ID, or None."""
        row = self._conn.execute(
            "SELECT id, name, conditions, actions, enabled, created_at "
            "FROM alert_rules WHERE id = ?",
            (rule_id,),
        ).fetchone()
        if row is None:
            return None
        return AlertRule(
            id=row[0],
            name=row[1],
            conditions=[Condition.from_dict(c) for c in json.loads(row[2])],
            actions=[Action.from_dict(a) for a in json.loads(row[3])],
            enabled=bool(row[4]),
            created_at=row[5],
        )

    # -- evaluation ----------------------------------------------------------

    def evaluate(self, event: dict) -> list[tuple[AlertRule, list[Action]]]:
        """Check event against all enabled rules.

        Returns a list of (rule, actions) for every rule that matches.
        """
        matches: list[tuple[AlertRule, list[Action]]] = []
        for rule in self.get_rules():
            if not rule.enabled:
                continue
            if rule.matches(event):
                matches.append((rule, rule.actions))
        return matches

    def execute_actions(self, event: dict, actions: list[Action]) -> list[dict]:
        """Fire the given actions for *event*.

        Returns a list of result dicts with action_type and status.
        """
        results = []
        for action in actions:
            try:
                result = self._execute_single_action(event, action)
                results.append(result)
            except Exception as e:
                logger.error("Action %s failed: %s", action.action_type, e)
                results.append({"action_type": action.action_type, "status": "error", "error": str(e)})

            # Record in alert history
            self._record_alert_fired(event, action)

        return results

    def _execute_single_action(self, event: dict, action: Action) -> dict:
        """Execute a single action. Returns result dict."""
        if action.action_type == "log":
            logger.info(
                "ALERT [log]: event matched — %s | verdict=%s tickers=%s",
                event.get("subject", "?"),
                event.get("verdict", "?"),
                event.get("tickers", []),
            )
            return {"action_type": "log", "status": "ok"}

        elif action.action_type == "telegram":
            return self._send_telegram_alert(event, action)

        elif action.action_type == "webhook":
            return self._send_webhook_alert(event, action)

        elif action.action_type == "dashboard_push":
            return self._send_dashboard_alert(event, action)

        return {"action_type": action.action_type, "status": "unknown_type"}

    def _send_telegram_alert(self, event: dict, action: Action) -> dict:
        """Send alert via Telegram Bot API."""
        import os
        bot_token = action.config.get("bot_token") or os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = action.config.get("chat_id") or os.getenv("TELEGRAM_CHAT_ID", "")

        if not bot_token or not chat_id:
            logger.warning("Telegram alert: missing bot_token or chat_id")
            return {"action_type": "telegram", "status": "skipped", "reason": "missing config"}

        verdict = event.get("verdict", "?")
        tickers = ", ".join(event.get("tickers", []))
        score = event.get("signal_score", 0)
        confidence = event.get("confidence", 0)
        subject = event.get("subject", "Unknown event")
        reasoning = event.get("reasoning", "")[:200]

        arrow = "+" if score >= 0 else ""
        text = (
            f"🚨 *Alert Triggered*\n\n"
            f"*{verdict}* ({arrow}{score}) — {confidence:.0%} confidence\n"
            f"Tickers: `{tickers}`\n"
            f"Subject: {subject}\n"
        )
        if reasoning:
            text += f"\n_{reasoning}_"

        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
                timeout=10,
            )
            if resp.status_code == 200:
                logger.info("Telegram alert sent successfully")
                return {"action_type": "telegram", "status": "ok"}
            else:
                logger.warning("Telegram API error %d", resp.status_code)
                return {"action_type": "telegram", "status": "error", "http_status": resp.status_code}
        except requests.RequestException as e:
            logger.error("Telegram request failed: %s", e)
            return {"action_type": "telegram", "status": "error", "error": str(e)}

    def _send_webhook_alert(self, event: dict, action: Action) -> dict:
        """POST event data to a webhook URL."""
        url = action.config.get("url", "")
        if not url:
            return {"action_type": "webhook", "status": "skipped", "reason": "no url"}

        # Validate URL: must be HTTPS, no private IPs
        if not self._is_safe_webhook_url(url):
            logger.warning("Webhook URL rejected (unsafe): %s", url[:100])
            return {"action_type": "webhook", "status": "rejected", "reason": "unsafe url"}

        headers = {"Content-Type": "application/json"}
        # Allow custom headers
        if action.config.get("headers"):
            headers.update(action.config["headers"])

        payload = {
            "alert_type": "finscrape",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": {
                "subject": event.get("subject", ""),
                "verdict": event.get("verdict", ""),
                "signal_score": event.get("signal_score", 0),
                "confidence": event.get("confidence", 0),
                "tickers": event.get("tickers", []),
                "event_type": event.get("event_type", ""),
                "reasoning": event.get("reasoning", "")[:500],
            },
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            logger.info("Webhook POST to %s: HTTP %d", url, resp.status_code)
            return {"action_type": "webhook", "status": "ok", "http_status": resp.status_code}
        except requests.RequestException as e:
            logger.error("Webhook POST failed: %s", e)
            return {"action_type": "webhook", "status": "error", "error": str(e)}

    def _send_dashboard_alert(self, event: dict, action: Action) -> dict:
        """Push alert event to dashboard."""
        from finscrape.dashboard import DashboardClient
        client = DashboardClient()
        if not client.is_configured:
            return {"action_type": "dashboard_push", "status": "skipped", "reason": "not configured"}

        alert_event = dict(event)
        alert_event["alert_triggered"] = True
        result = client.push_events([alert_event])
        return {"action_type": "dashboard_push", "status": "ok", "result": result}

    def _record_alert_fired(self, event: dict, action: Action) -> None:
        """Record that an alert was fired for deduplication tracking."""
        try:
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS alert_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT,
                    action_type TEXT NOT NULL,
                    event_subject TEXT,
                    event_tickers TEXT,
                    fired_at TEXT NOT NULL DEFAULT (datetime('now'))
                )"""
            )
            self._conn.execute(
                "INSERT INTO alert_history (action_type, event_subject, event_tickers, fired_at) "
                "VALUES (?, ?, ?, datetime('now'))",
                (action.action_type, event.get("subject", "")[:200],
                 json.dumps(event.get("tickers", []))),
            )
            self._conn.commit()
        except Exception as e:
            logger.debug("Could not record alert history: %s", e)

    # -- presets (class methods) ---------------------------------------------

    @classmethod
    def preset_faang_pullout(cls) -> tuple[list[Condition], list[Action]]:
        """PULL_OUT verdict on any FAANG stock."""
        conditions = [
            Condition(field="verdict", operator="eq", value="PULL_OUT"),
            Condition(
                field="tickers",
                operator="contains",
                value=["AAPL", "MSFT", "GOOGL", "AMZN", "META"],
            ),
        ]
        actions = [Action(action_type="log")]
        return conditions, actions

    @classmethod
    def preset_high_confidence_invest(cls) -> tuple[list[Condition], list[Action]]:
        """INVEST verdict with confidence >= 0.8."""
        conditions = [
            Condition(field="verdict", operator="eq", value="INVEST"),
            Condition(field="confidence", operator="gte", value=0.8),
        ]
        actions = [Action(action_type="log")]
        return conditions, actions

    @classmethod
    def preset_high_impact(cls) -> tuple[list[Condition], list[Action]]:
        """|signal_score| >= 4  (score >= 4 or score <= -4)."""
        # We approximate absolute value with two conditions OR-combined.
        # Since our engine uses AND logic, we implement this as a single
        # condition using a custom check.  Instead, we keep it simple:
        # signal_score >= 4 captures high-positive.  For a full implementation
        # we'd need OR logic.  For now, we use gte(4) which covers strongly
        # positive signals.  Users can add a second rule for lte(-4).
        conditions = [
            Condition(field="signal_score", operator="gte", value=4),
        ]
        actions = [Action(action_type="log")]
        return conditions, actions

    @classmethod
    def preset_breaking_news(cls) -> tuple[list[Condition], list[Action]]:
        """event_type == 'breaking_news'."""
        conditions = [
            Condition(field="event_type", operator="eq", value="breaking_news"),
        ]
        actions = [Action(action_type="log")]
        return conditions, actions

    # -- lifecycle -----------------------------------------------------------

    def close(self) -> None:
        self._conn.close()

    # -- security helpers ---------------------------------------------------

    @staticmethod
    def _is_safe_webhook_url(url: str) -> bool:
        """Validate that a webhook URL is safe (no SSRF).

        Rules:
        - Must use https:// scheme
        - Must not point to private/loopback IPs
        - Must have a valid hostname
        """
        from urllib.parse import urlparse
        import ipaddress

        try:
            parsed = urlparse(url)
        except Exception:
            return False

        # Must be HTTPS
        if parsed.scheme != "https":
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        # Block obvious private hostnames
        blocked_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "::1",
                         "metadata.google.internal", "169.254.169.254"}
        if hostname.lower() in blocked_hosts:
            return False

        # Try to check if it resolves to a private IP
        try:
            addr = ipaddress.ip_address(hostname)
            if addr.is_private or addr.is_loopback or addr.is_link_local:
                return False
        except ValueError:
            pass  # Not an IP literal — hostname is fine

        return True
