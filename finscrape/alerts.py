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
        elif op == "gt":
            return float(event_value) > float(target)
        elif op == "gte":
            return float(event_value) >= float(target)
        elif op == "lt":
            return float(event_value) < float(target)
        elif op == "lte":
            return float(event_value) <= float(target)
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
        return rule.id

    def remove_rule(self, rule_id: str) -> bool:
        """Delete a rule. Returns True if a row was removed."""
        cur = self._conn.execute("DELETE FROM alert_rules WHERE id = ?", (rule_id,))
        self._conn.commit()
        removed = cur.rowcount > 0
        if removed:
            logger.info("Removed alert rule %s", rule_id)
        return removed

    def enable_rule(self, rule_id: str) -> None:
        self._conn.execute("UPDATE alert_rules SET enabled = 1 WHERE id = ?", (rule_id,))
        self._conn.commit()

    def disable_rule(self, rule_id: str) -> None:
        self._conn.execute("UPDATE alert_rules SET enabled = 0 WHERE id = ?", (rule_id,))
        self._conn.commit()

    def get_rules(self) -> list[AlertRule]:
        """Return all rules (enabled and disabled)."""
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

    def execute_actions(self, event: dict, actions: list[Action]) -> None:
        """Fire the given actions for *event*.

        Currently only the ``log`` action is fully implemented.
        Telegram, webhook, and dashboard_push are stubs that log intent.
        """
        for action in actions:
            if action.action_type == "log":
                logger.info(
                    "ALERT [log]: event matched — %s | verdict=%s tickers=%s",
                    event.get("subject", "?"),
                    event.get("verdict", "?"),
                    event.get("tickers", []),
                )
            elif action.action_type == "telegram":
                chat_id = action.config.get("chat_id", "?")
                logger.info(
                    "ALERT [telegram stub]: would send to chat_id=%s — %s",
                    chat_id,
                    event.get("subject", "?"),
                )
            elif action.action_type == "webhook":
                url = action.config.get("url", "?")
                logger.info(
                    "ALERT [webhook stub]: would POST to %s — %s",
                    url,
                    event.get("subject", "?"),
                )
            elif action.action_type == "dashboard_push":
                logger.info(
                    "ALERT [dashboard_push stub]: would push event — %s",
                    event.get("subject", "?"),
                )

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
