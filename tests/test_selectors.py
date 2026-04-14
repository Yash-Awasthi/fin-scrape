"""Tests for adaptive selector tracking."""

import tempfile
from pathlib import Path

import pytest

from finscrape.selectors import SelectorTracker


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def tracker(db_path):
    t = SelectorTracker(db_path)
    yield t
    t.close()


class TestSelectorTracker:
    def test_register_and_get(self, tracker):
        tracker.register("yahoo", "article_links", "a.js-content-viewer")
        sel = tracker.get_selector("yahoo", "article_links")
        assert sel == "a.js-content-viewer"

    def test_hit_tracking(self, tracker):
        tracker.register("yahoo", "title", "h1.article-title")
        tracker.record_hit("yahoo", "title", "h1.article-title")
        tracker.record_hit("yahoo", "title", "h1.article-title")
        report = tracker.get_health_report("yahoo")
        assert len(report) == 1
        assert report[0]["hit_count"] == 2
        assert report[0]["miss_count"] == 0

    def test_miss_tracking(self, tracker):
        tracker.register("yahoo", "title", "h1.old-selector")
        tracker.record_miss("yahoo", "title", "h1.old-selector")
        report = tracker.get_health_report("yahoo")
        assert report[0]["miss_count"] == 1

    def test_primary_preferred(self, tracker):
        tracker.register("yahoo", "links", "a.primary", is_primary=True)
        tracker.register("yahoo", "links", "a.fallback", is_primary=False)
        sel = tracker.get_selector("yahoo", "links")
        assert sel == "a.primary"

    def test_fallbacks(self, tracker):
        tracker.register("yahoo", "links", "a.primary", is_primary=True)
        tracker.register("yahoo", "links", "a.fb1", is_primary=False)
        tracker.register("yahoo", "links", "a.fb2", is_primary=False)
        fallbacks = tracker.get_fallbacks("yahoo", "links")
        assert "a.fb1" in fallbacks
        assert "a.fb2" in fallbacks
        assert "a.primary" not in fallbacks

    def test_reliability_calculation(self, tracker):
        tracker.register("test", "sel", "div.x")
        for _ in range(8):
            tracker.record_hit("test", "sel", "div.x")
        for _ in range(2):
            tracker.record_miss("test", "sel", "div.x")
        report = tracker.get_health_report("test")
        assert abs(report[0]["reliability"] - 0.8) < 0.01

    def test_degraded_alert(self, tracker):
        tracker.register("test", "sel", "div.broken")
        for _ in range(5):
            tracker.record_miss("test", "sel", "div.broken")
        alerts = tracker.get_alerts("test")
        assert len(alerts) >= 1
        assert alerts[0]["alert_type"] == "degraded"

    def test_degraded_selectors(self, tracker):
        tracker.register("test", "good", "div.works")
        tracker.register("test", "bad", "div.broken")
        for _ in range(10):
            tracker.record_hit("test", "good", "div.works")
        for _ in range(10):
            tracker.record_miss("test", "bad", "div.broken")
        degraded = tracker.get_degraded_selectors()
        assert len(degraded) == 1
        assert degraded[0]["selector"] == "div.broken"

    def test_unknown_selector_returns_none(self, tracker):
        assert tracker.get_selector("unknown", "whatever") is None

    def test_source_isolation(self, tracker):
        tracker.register("src1", "links", "a.one")
        tracker.register("src2", "links", "a.two")
        assert tracker.get_selector("src1", "links") == "a.one"
        assert tracker.get_selector("src2", "links") == "a.two"

    def test_health_report_all(self, tracker):
        tracker.register("a", "x", "sel1")
        tracker.register("b", "y", "sel2")
        report = tracker.get_health_report()
        assert len(report) == 2
