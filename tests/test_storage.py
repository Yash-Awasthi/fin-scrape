"""Tests for finscrape.storage.StateManager (SQLite backend)."""

import pytest
import tempfile
from pathlib import Path

from finscrape.storage import StateManager


@pytest.fixture()
def sm(tmp_path):
    """Create a StateManager backed by a temporary directory."""
    manager = StateManager(data_dir=str(tmp_path))
    yield manager
    manager.close()


# ---------------------------------------------------------------------------
# Table creation
# ---------------------------------------------------------------------------

class TestTableCreation:
    def test_db_file_exists(self, sm, tmp_path):
        assert (tmp_path / "finscrape.db").exists()

    def test_tables_exist(self, sm):
        tables = {
            row[0]
            for row in sm._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "visited_urls" in tables
        assert "events" in tables
        assert "entity_index" in tables


# ---------------------------------------------------------------------------
# Visited URLs
# ---------------------------------------------------------------------------

class TestVisitedUrls:
    def test_add_and_get(self, sm):
        sm.add_visited("rss", "https://example.com/1")
        sm.add_visited("rss", "https://example.com/2")
        visited = sm.get_visited("rss")
        assert visited == {"https://example.com/1", "https://example.com/2"}

    def test_get_visited_empty(self, sm):
        assert sm.get_visited("rss") == set()

    def test_sources_are_separate(self, sm):
        sm.add_visited("rss", "https://example.com/a")
        sm.add_visited("scraper", "https://example.com/b")
        assert sm.get_visited("rss") == {"https://example.com/a"}
        assert sm.get_visited("scraper") == {"https://example.com/b"}

    def test_duplicate_insert_ignored(self, sm):
        sm.add_visited("rss", "https://example.com/dup")
        sm.add_visited("rss", "https://example.com/dup")
        assert sm.visited_count("rss") == 1

    def test_visited_count(self, sm):
        sm.add_visited("rss", "https://a.com")
        sm.add_visited("rss", "https://b.com")
        sm.add_visited("other", "https://c.com")
        assert sm.visited_count("rss") == 2
        assert sm.visited_count() == 3


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

def _sample_event(**overrides):
    base = dict(
        subject="Tesla Q4 earnings beat",
        event_type="earnings",
        tickers=["TSLA"],
        impact_direction="positive",
        signal_score=4,
        confidence=0.85,
        verdict="INVEST",
        heuristic_impact=0.7,
        divergence_flag=False,
        sources=["https://example.com"],
        articles=["Tesla reported..."],
        timestamp="2026-01-15T12:00:00+00:00",
    )
    base.update(overrides)
    return base


class TestEvents:
    def test_add_event_returns_id(self, sm):
        eid = sm.add_event(_sample_event())
        assert isinstance(eid, int)
        assert eid >= 1

    def test_get_recent_events(self, sm):
        sm.add_event(_sample_event(subject="First"))
        sm.add_event(_sample_event(subject="Second"))
        events = sm.get_recent_events(limit=10)
        assert len(events) == 2
        # Most recent first
        assert events[0]["subject"] == "Second"
        assert events[1]["subject"] == "First"

    def test_event_fields_decoded(self, sm):
        sm.add_event(_sample_event())
        ev = sm.get_recent_events(1)[0]
        assert isinstance(ev["tickers"], list)
        assert isinstance(ev["sources"], list)
        assert isinstance(ev["articles"], list)
        assert isinstance(ev["divergence_flag"], bool)

    def test_get_events_by_ticker(self, sm):
        sm.add_event(_sample_event(tickers=["AAPL"]))
        sm.add_event(_sample_event(tickers=["TSLA"]))
        sm.add_event(_sample_event(tickers=["AAPL", "GOOG"]))
        results = sm.get_events_by_ticker("AAPL")
        assert len(results) == 2
        for ev in results:
            assert "AAPL" in ev["tickers"]

    def test_get_events_by_verdict(self, sm):
        sm.add_event(_sample_event(verdict="INVEST"))
        sm.add_event(_sample_event(verdict="PULL_OUT"))
        sm.add_event(_sample_event(verdict="INVEST"))
        results = sm.get_events_by_verdict("INVEST")
        assert len(results) == 2
        for ev in results:
            assert ev["verdict"] == "INVEST"

    def test_event_count(self, sm):
        assert sm.event_count() == 0
        sm.add_event(_sample_event())
        sm.add_event(_sample_event())
        assert sm.event_count() == 2

    def test_events_property(self, sm):
        sm.add_event(_sample_event())
        assert len(sm.events) == 1


# ---------------------------------------------------------------------------
# Entity Index
# ---------------------------------------------------------------------------

class TestEntityIndex:
    def test_add_and_resolve(self, sm):
        sm.add_entity("apple", "Apple Inc.", "AAPL")
        tickers = sm.resolve_entity_tickers("Big news about Apple Inc. today")
        assert "AAPL" in tickers

    def test_resolve_requires_company_name_in_text(self, sm):
        sm.add_entity("apple", "Apple Inc.", "AAPL")
        # keyword matches but full company name is absent
        tickers = sm.resolve_entity_tickers("apple pie recipe")
        assert "AAPL" not in tickers

    def test_seed_entity_index(self, sm):
        sm.seed_entity_index({
            "tesla": [("Tesla Inc.", "TSLA")],
            "google": [("Alphabet Inc.", "GOOG"), ("Google LLC", "GOOGL")],
        })
        tickers = sm.resolve_entity_tickers("Alphabet Inc. and google dominate search")
        assert "GOOG" in tickers

    def test_add_entity_normalizes_case(self, sm):
        sm.add_entity("MSFT", "Microsoft Corp", "msft")
        # keyword stored lowercase, ticker stored uppercase
        rows = sm._conn.execute(
            "SELECT keyword, ticker FROM entity_index"
        ).fetchall()
        assert rows[0] == ("msft", "MSFT")


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

class TestStats:
    def test_stats_keys(self, sm):
        s = sm.stats()
        assert "events" in s
        assert "visited_urls" in s
        assert "entity_entries" in s
        assert "db_size_kb" in s

    def test_stats_counts(self, sm):
        sm.add_event(_sample_event())
        sm.add_visited("rss", "https://example.com")
        sm.add_entity("test", "Test Co", "TST")
        s = sm.stats()
        assert s["events"] == 1
        assert s["visited_urls"] == 1
        assert s["entity_entries"] == 1
        assert s["db_size_kb"] > 0
