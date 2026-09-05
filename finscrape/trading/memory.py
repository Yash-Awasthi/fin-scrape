"""
Decision memory — persists past analyses and generates reflections.

Modeled after TradingAgents' TradingMemoryLog. Stores decisions in a JSON-lines
file, resolves outcomes (realized returns), and generates reflections that inject
past lessons into the next analysis of the same ticker.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MEMORY_DIR = os.path.expanduser("~/.finscrape/memory")


class DecisionMemory:
    """Persistent decision log with reflection on realized returns."""

    def __init__(self, memory_dir: str | None = None):
        self.memory_dir = Path(memory_dir or DEFAULT_MEMORY_DIR)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.memory_dir / "decisions.jsonl"

    def store_decision(
        self,
        ticker: str,
        trade_date: str,
        signal: str,
        decision: str,
        reports: dict[str, str] | None = None,
    ) -> None:
        """Append a decision to the log."""
        entry = {
            "ticker": ticker,
            "trade_date": trade_date,
            "signal": signal,
            "decision": decision,
            "timestamp": datetime.now().isoformat(),
            "raw_return": None,
            "alpha_return": None,
            "reflection": None,
            "resolved": False,
            "resolution_date": None,
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
        logger.info("Stored decision for %s on %s: %s", ticker, trade_date, signal)

    def get_pending_entries(self, ticker: str) -> list[dict]:
        """Get unresolved entries for a ticker that are old enough to evaluate."""
        entries = self._read_entries()
        cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        return [
            e for e in entries
            if e["ticker"] == ticker
            and not e["resolved"]
            and e["trade_date"] <= cutoff
        ]

    def get_past_context(self, ticker: str, limit: int = 5) -> str:
        """Get formatted past decisions and reflections for injection into prompts."""
        entries = self._read_entries()
        relevant = [
            e for e in entries
            if e["ticker"] == ticker and e.get("reflection")
        ][-limit:]

        if not relevant:
            return ""

        lines = [f"=== Past Decisions for {ticker} ==="]
        for e in relevant:
            ret_label = ""
            if e.get("raw_return") is not None:
                ret_label = f" (realized: {e['raw_return']:+.1%})"
            lines.append(f"  {e['trade_date']}: {e['signal']}{ret_label}")
            if e.get("reflection"):
                lines.append(f"    Reflection: {e['reflection'][:200]}")
        return "\n".join(lines)

    def resolve_entries(
        self,
        ticker: str,
        holding_days: int = 5,
    ) -> list[dict]:
        """Resolve pending entries by fetching realized returns via yfinance."""
        pending = self.get_pending_entries(ticker)
        if not pending:
            return []

        resolved = []
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)

            for entry in pending:
                try:
                    trade_date = entry["trade_date"]
                    start = datetime.strptime(trade_date, "%Y-%m-%d")
                    end = start + timedelta(days=holding_days + 7)
                    hist = stock.history(
                        start=start.strftime("%Y-%m-%d"),
                        end=end.strftime("%Y-%m-%d"),
                    )
                    if len(hist) <= holding_days:
                        continue  # not enough data yet

                    raw_return = float(
                        (hist["Close"].iloc[holding_days] - hist["Close"].iloc[0])
                        / hist["Close"].iloc[0]
                    )
                    entry["raw_return"] = round(raw_return, 4)
                    entry["resolved"] = True
                    entry["resolution_date"] = hist.index[holding_days].strftime("%Y-%m-%d")

                    # Generate reflection
                    entry["reflection"] = self._reflect(entry, raw_return)
                    resolved.append(entry)

                except Exception as e:
                    logger.warning("Could not resolve entry for %s on %s: %s", ticker, entry["trade_date"], e)
                    continue

            # Rewrite the log with updated entries
            if resolved:
                self._rewrite_log(self._read_entries())

        except ImportError:
            logger.warning("yfinance not available — cannot resolve entries")

        return resolved

    def _reflect(self, entry: dict, raw_return: float) -> str:
        """Generate a brief reflection on a realized return."""
        signal = entry.get("signal", "Hold")
        direction = "long" if signal == "Buy" else "short" if signal == "Sell" else "flat"

        if direction == "long":
            correct = raw_return > 0
        elif direction == "short":
            correct = raw_return < 0
        else:
            correct = abs(raw_return) < 0.02  # within 2% = neutral was right

        if correct:
            return f"Decision was correct. {signal} on {entry['trade_date']} resulted in {raw_return:+.1%} return."
        else:
            return f"Decision was incorrect. {signal} on {entry['trade_date']} resulted in {raw_return:+.1%} return — reassess approach."

    def _read_entries(self) -> list[dict]:
        """Read all entries from the JSONL log."""
        if not self.log_path.exists():
            return []
        entries = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return entries

    def _rewrite_log(self, entries: list[dict]) -> None:
        """Rewrite the entire log file."""
        with open(self.log_path, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry, default=str) + "\n")
