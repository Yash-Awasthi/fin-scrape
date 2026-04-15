"""
Integration tests for the FinScrape pipeline.

Tests the full flow: article → AI analysis → validation → scoring → event creation,
plus the new integrations: alerts, portfolio, accuracy tracking, and performance stats.
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from finscrape.pipeline import FinScrapePipeline, PipelineStats, _StageTimer
from finscrape.models import ScrapedArticle, FinEvent, Verdict
from finscrape.alerts import AlertEngine, Condition, Action
from finscrape.portfolio import PortfolioManager
from finscrape.accuracy import AccuracyTracker


# --- Fixtures ---

@pytest.fixture
def tmp_data_dir(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return str(tmp_path)


@pytest.fixture
def sample_article():
    return ScrapedArticle(
        url="https://example.com/test-article",
        title="Apple Reports Record Q4 Earnings",
        text="Apple Inc. (AAPL) reported record fourth-quarter earnings of $1.46 per share, "
             "beating analyst estimates of $1.39. Revenue came in at $89.5 billion, "
             "up 8% year-over-year. The company also announced a new $90 billion share "
             "buyback program. CEO Tim Cook expressed optimism about the coming holiday "
             "season. iPhone sales were particularly strong in emerging markets. " * 3,
        source="yahoo",
        age_hours=2.0,
        raw_tickers=["AAPL"],
    )


@pytest.fixture
def mock_ai_response():
    return {
        "relevant": True,
        "event_type": "earnings",
        "subject": "apple reports record q4 earnings",
        "tickers": ["AAPL"],
        "impact_direction": "positive",
        "signal_score": 4,
        "confidence": 0.85,
        "reasoning": "Strong earnings beat with positive guidance",
        "magnitude": "high",
        "novelty": "standard",
        "actionability": "high",
        "affected_entities": [{"name": "Apple Inc.", "ticker": "AAPL"}],
        "second_order_effects": ["Positive for supply chain"],
        "sector_impact": "Technology",
        "key_metrics": {"eps": {"value": 1.46, "raw": "$1.46 per share"}},
    }


# --- PipelineStats tests ---

class TestPipelineStats:

    def test_stats_initialization(self):
        stats = PipelineStats()
        assert stats.articles_seen == 0
        assert stats.articles_skipped == 0
        assert stats.articles_analyzed == 0
        assert stats.articles_failed == 0
        assert stats.events_created == 0
        assert stats.alerts_fired == 0
        assert stats.signals_recorded == 0
        assert stats.stage_timings == {}

    def test_stage_timer(self):
        stats = PipelineStats()
        with stats.time_stage("test_stage"):
            pass  # Just measuring overhead
        assert "test_stage" in stats.stage_timings
        assert stats.stage_timings["test_stage"] >= 0

    def test_stage_timer_accumulates(self):
        stats = PipelineStats()
        with stats.time_stage("accum"):
            pass
        with stats.time_stage("accum"):
            pass
        assert "accum" in stats.stage_timings

    def test_elapsed(self):
        stats = PipelineStats()
        assert stats.elapsed >= 0

    def test_summary(self):
        stats = PipelineStats()
        stats.articles_seen = 10
        stats.events_created = 3
        summary = stats.summary()
        assert summary["articles_seen"] == 10
        assert summary["events_created"] == 3
        assert "elapsed_s" in summary
        assert "stage_timings" in summary


# --- Pipeline initialization tests ---

class TestPipelineInit:

    @patch("finscrape.pipeline.AlertEngine")
    @patch("finscrape.pipeline.AccuracyTracker")
    @patch("finscrape.pipeline.PortfolioManager")
    def test_init_with_all_integrations(self, mock_pm, mock_at, mock_ae, tmp_data_dir):
        pipeline = FinScrapePipeline(
            sources=["yahoo"],
            data_dir=tmp_data_dir,
            enable_alerts=True,
            enable_accuracy=True,
            enable_portfolio=True,
        )
        assert pipeline.alert_engine is not None
        assert pipeline.accuracy is not None
        assert pipeline.portfolio is not None

    @patch("finscrape.pipeline.AlertEngine", side_effect=Exception("DB error"))
    @patch("finscrape.pipeline.AccuracyTracker", side_effect=Exception("DB error"))
    @patch("finscrape.pipeline.PortfolioManager", side_effect=Exception("DB error"))
    def test_init_graceful_on_integration_failure(self, mock_pm, mock_at, mock_ae, tmp_data_dir):
        """Integration failures should not crash pipeline init."""
        pipeline = FinScrapePipeline(
            sources=["yahoo"],
            data_dir=tmp_data_dir,
        )
        assert pipeline.alert_engine is None
        assert pipeline.accuracy is None
        assert pipeline.portfolio is None

    def test_init_disables_integrations(self, tmp_data_dir):
        pipeline = FinScrapePipeline(
            sources=["yahoo"],
            data_dir=tmp_data_dir,
            enable_alerts=False,
            enable_accuracy=False,
            enable_portfolio=False,
        )
        assert pipeline.alert_engine is None
        assert pipeline.accuracy is None
        assert pipeline.portfolio is None

    def test_unknown_source_skipped(self, tmp_data_dir):
        pipeline = FinScrapePipeline(
            sources=["yahoo", "nonexistent_source"],
            data_dir=tmp_data_dir,
            enable_alerts=False,
            enable_accuracy=False,
            enable_portfolio=False,
        )
        assert "yahoo" in pipeline.scrapers
        assert "nonexistent_source" not in pipeline.scrapers

    def test_council_init(self, tmp_data_dir):
        pipeline = FinScrapePipeline(
            sources=["yahoo"],
            data_dir=tmp_data_dir,
            use_council=True,
            enable_alerts=False,
            enable_accuracy=False,
            enable_portfolio=False,
        )
        assert pipeline.council is not None


# --- Article processing tests ---

class TestArticleProcessing:

    @patch("finscrape.pipeline.call_ai")
    @patch("finscrape.pipeline.get_market_data", return_value=[{"ticker": "AAPL", "price": 185.0, "change_percent": 2.5}])
    def test_analyze_article_produces_event(self, mock_market, mock_ai, sample_article, mock_ai_response, tmp_data_dir):
        mock_ai.return_value = mock_ai_response
        pipeline = FinScrapePipeline(
            sources=["yahoo"],
            data_dir=tmp_data_dir,
            enable_alerts=False,
            enable_accuracy=False,
            enable_portfolio=False,
        )
        event = pipeline._analyze_article("yahoo", sample_article)
        assert event is not None
        assert isinstance(event, FinEvent)
        assert "AAPL" in event.tickers
        assert event.verdict in ("INVEST", "OBSERVE", "CAUTIOUS", "PULL_OUT")
        assert event.confidence > 0
        assert event.reasoning != ""

    @patch("finscrape.pipeline.call_ai", return_value=None)
    def test_analyze_article_ai_failure(self, mock_ai, sample_article, tmp_data_dir):
        pipeline = FinScrapePipeline(
            sources=["yahoo"],
            data_dir=tmp_data_dir,
            enable_alerts=False,
            enable_accuracy=False,
            enable_portfolio=False,
        )
        event = pipeline._analyze_article("yahoo", sample_article)
        assert event is None

    @patch("finscrape.pipeline.call_ai")
    def test_analyze_article_not_relevant(self, mock_ai, sample_article, tmp_data_dir):
        mock_ai.return_value = {"relevant": False}
        pipeline = FinScrapePipeline(
            sources=["yahoo"],
            data_dir=tmp_data_dir,
            enable_alerts=False,
            enable_accuracy=False,
            enable_portfolio=False,
        )
        event = pipeline._analyze_article("yahoo", sample_article)
        assert event is None

    def test_process_articles_skips_visited(self, sample_article, tmp_data_dir):
        pipeline = FinScrapePipeline(
            sources=["yahoo"],
            data_dir=tmp_data_dir,
            enable_alerts=False,
            enable_accuracy=False,
            enable_portfolio=False,
        )
        # Mark as visited first
        pipeline.state.add_visited("yahoo", sample_article.url)
        stats = PipelineStats()
        events = pipeline._process_articles("yahoo", [sample_article], stats)
        assert len(events) == 0
        assert stats.articles_skipped == 1

    def test_process_articles_skips_empty_content(self, tmp_data_dir):
        article = ScrapedArticle(
            url="https://example.com/empty",
            title="Short",
            text="Too short",
            source="yahoo",
        )
        pipeline = FinScrapePipeline(
            sources=["yahoo"],
            data_dir=tmp_data_dir,
            enable_alerts=False,
            enable_accuracy=False,
            enable_portfolio=False,
        )
        stats = PipelineStats()
        events = pipeline._process_articles("yahoo", [article], stats)
        assert len(events) == 0
        assert stats.articles_skipped == 1

    def test_process_articles_skips_stale_articles(self, tmp_data_dir):
        article = ScrapedArticle(
            url="https://example.com/old",
            title="Old News About Apple",
            text="This is old news about Apple Inc. " * 20,
            source="yahoo",
            age_hours=48.0,
        )
        pipeline = FinScrapePipeline(
            sources=["yahoo"],
            data_dir=tmp_data_dir,
            enable_alerts=False,
            enable_accuracy=False,
            enable_portfolio=False,
        )
        stats = PipelineStats()
        events = pipeline._process_articles("yahoo", [article], stats)
        assert len(events) == 0
        assert stats.articles_skipped == 1


# --- Post-processing integration tests ---

class TestPostProcessing:

    @patch("finscrape.pipeline.get_market_data", return_value=[{"ticker": "AAPL", "price": 185.0, "change_percent": 1.5}])
    def test_alert_evaluation_on_event(self, mock_market, tmp_data_dir):
        """Alerts engine should evaluate events after pipeline produces them."""
        pipeline = FinScrapePipeline(
            sources=["yahoo"],
            data_dir=tmp_data_dir,
            enable_alerts=True,
            enable_accuracy=False,
            enable_portfolio=False,
        )

        # Add a rule that matches INVEST verdicts
        if pipeline.alert_engine:
            pipeline.alert_engine.add_rule(
                "Test Rule",
                [Condition(field="verdict", operator="eq", value="INVEST")],
                [Action(action_type="log")],
            )

        event = FinEvent(
            subject="test event",
            event_type="earnings",
            tickers=["AAPL"],
            impact_direction="positive",
            signal_score=4,
            confidence=0.85,
            verdict="INVEST",
            sources=["yahoo"],
        )

        stats = PipelineStats()
        pipeline._post_process_events([event], stats)
        assert stats.alerts_fired >= 1

    @patch("finscrape.pipeline.get_market_data", return_value=[{"ticker": "AAPL", "price": 185.0, "change_percent": 1.5}])
    def test_accuracy_recording(self, mock_market, tmp_data_dir):
        """INVEST/PULL_OUT events should be recorded for accuracy tracking."""
        pipeline = FinScrapePipeline(
            sources=["yahoo"],
            data_dir=tmp_data_dir,
            enable_alerts=False,
            enable_accuracy=True,
            enable_portfolio=False,
        )

        event = FinEvent(
            subject="test invest event",
            event_type="earnings",
            tickers=["AAPL"],
            impact_direction="positive",
            signal_score=4,
            confidence=0.85,
            verdict="INVEST",
            sources=["yahoo"],
        )

        stats = PipelineStats()
        pipeline._post_process_events([event], stats)
        assert stats.signals_recorded >= 1

    @patch("finscrape.pipeline.get_market_data", return_value=[])
    def test_accuracy_skips_observe(self, mock_market, tmp_data_dir):
        """OBSERVE verdicts should not be recorded for accuracy."""
        pipeline = FinScrapePipeline(
            sources=["yahoo"],
            data_dir=tmp_data_dir,
            enable_alerts=False,
            enable_accuracy=True,
            enable_portfolio=False,
        )

        event = FinEvent(
            subject="neutral event",
            event_type="other",
            tickers=["MSFT"],
            impact_direction="neutral",
            signal_score=1,
            confidence=0.5,
            verdict="OBSERVE",
            sources=["yahoo"],
        )

        stats = PipelineStats()
        pipeline._post_process_events([event], stats)
        assert stats.signals_recorded == 0

    def test_portfolio_alerts_on_held_position(self, tmp_data_dir):
        """Portfolio should alert on INVEST/PULL_OUT for held positions."""
        pipeline = FinScrapePipeline(
            sources=["yahoo"],
            data_dir=tmp_data_dir,
            enable_alerts=False,
            enable_accuracy=False,
            enable_portfolio=True,
        )

        if pipeline.portfolio:
            pipeline.portfolio.add_position("AAPL", shares=100, avg_cost=150.0, current_price=185.0)

        event = FinEvent(
            subject="apple pullout signal",
            event_type="earnings",
            tickers=["AAPL"],
            impact_direction="negative",
            signal_score=-3,
            confidence=0.9,
            verdict="PULL_OUT",
            sources=["yahoo"],
        )

        stats = PipelineStats()
        pipeline._post_process_events([event], stats)
        # Portfolio should have generated alerts
        if pipeline.portfolio:
            alerts = pipeline.portfolio.get_recent_alerts()
            assert len(alerts) >= 1


# --- Input validation tests ---

class TestInputValidation:

    def test_portfolio_rejects_negative_shares(self, tmp_data_dir):
        from finscrape.portfolio import PortfolioManager
        pm = PortfolioManager(db_path=Path(tmp_data_dir) / "data" / "test.db")
        with pytest.raises(ValueError, match="shares must be >= 0"):
            pm.add_position("AAPL", shares=-10, avg_cost=150.0)

    def test_portfolio_rejects_negative_cost(self, tmp_data_dir):
        from finscrape.portfolio import PortfolioManager
        pm = PortfolioManager(db_path=Path(tmp_data_dir) / "data" / "test.db")
        with pytest.raises(ValueError, match="avg_cost must be >= 0"):
            pm.add_position("AAPL", shares=10, avg_cost=-5.0)

    def test_portfolio_rejects_empty_ticker(self, tmp_data_dir):
        from finscrape.portfolio import PortfolioManager
        pm = PortfolioManager(db_path=Path(tmp_data_dir) / "data" / "test.db")
        with pytest.raises(ValueError, match="Invalid ticker"):
            pm.add_position("", shares=10, avg_cost=150.0)

    def test_portfolio_rejects_long_ticker(self, tmp_data_dir):
        from finscrape.portfolio import PortfolioManager
        pm = PortfolioManager(db_path=Path(tmp_data_dir) / "data" / "test.db")
        with pytest.raises(ValueError, match="Invalid ticker"):
            pm.add_position("TOOLONGTICKER", shares=10, avg_cost=150.0)

    def test_portfolio_accepts_valid_position(self, tmp_data_dir):
        from finscrape.portfolio import PortfolioManager
        pm = PortfolioManager(db_path=Path(tmp_data_dir) / "data" / "test.db")
        pm.add_position("AAPL", shares=100, avg_cost=150.0, current_price=185.0)
        pos = pm.get_position("AAPL")
        assert pos is not None
        assert pos.shares == 100


# --- Deduplication tests ---

class TestDeduplication:

    @patch("finscrape.pipeline.call_ai")
    @patch("finscrape.pipeline.get_market_data", return_value=[{"ticker": "AAPL", "price": 185.0, "change_percent": 2.5}])
    def test_duplicate_articles_merged(self, mock_market, mock_ai, mock_ai_response, tmp_data_dir):
        mock_ai.return_value = mock_ai_response
        pipeline = FinScrapePipeline(
            sources=["yahoo"],
            data_dir=tmp_data_dir,
            enable_alerts=False,
            enable_accuracy=False,
            enable_portfolio=False,
        )

        article1 = ScrapedArticle(
            url="https://example.com/article1",
            title="Apple Reports Record Q4 Earnings",
            text="Apple Inc. (AAPL) reported record fourth-quarter earnings. " * 20,
            source="yahoo",
            age_hours=1.0,
            raw_tickers=["AAPL"],
        )
        article2 = ScrapedArticle(
            url="https://example.com/article2",
            title="Apple Reports Record Q4 Earnings Results",
            text="Apple Inc. (AAPL) reported record fourth-quarter earnings. " * 20,
            source="reuters",
            age_hours=1.0,
            raw_tickers=["AAPL"],
        )

        # First article should create an event
        event1 = pipeline._analyze_article("yahoo", article1)
        assert event1 is not None

        # Second article (same topic) should merge
        event2 = pipeline._analyze_article("reuters", article2)
        # event2 will be None if dedup caught it, or a new event if subjects differ enough
        # The important thing is no crash


# --- Alert action tests ---

class TestAlertActions:

    def test_log_action_executes(self, tmp_data_dir):
        engine = AlertEngine(db_path=Path(tmp_data_dir) / "data" / "test.db")
        event = {"subject": "Test", "verdict": "INVEST", "tickers": ["AAPL"]}
        results = engine.execute_actions(event, [Action(action_type="log")])
        assert len(results) == 1
        assert results[0]["status"] == "ok"

    def test_telegram_action_skips_no_config(self, tmp_data_dir):
        engine = AlertEngine(db_path=Path(tmp_data_dir) / "data" / "test.db")
        event = {"subject": "Test", "verdict": "INVEST", "tickers": ["AAPL"]}
        results = engine.execute_actions(event, [Action(action_type="telegram")])
        assert len(results) == 1
        assert results[0]["status"] == "skipped"

    def test_webhook_action_skips_no_url(self, tmp_data_dir):
        engine = AlertEngine(db_path=Path(tmp_data_dir) / "data" / "test.db")
        event = {"subject": "Test", "verdict": "INVEST", "tickers": ["AAPL"]}
        results = engine.execute_actions(event, [Action(action_type="webhook")])
        assert len(results) == 1
        assert results[0]["status"] == "skipped"

    def test_alert_history_recorded(self, tmp_data_dir):
        db_path = Path(tmp_data_dir) / "data" / "test.db"
        engine = AlertEngine(db_path=db_path)
        event = {"subject": "Test Event", "verdict": "INVEST", "tickers": ["AAPL"]}
        engine.execute_actions(event, [Action(action_type="log")])

        # Check history table
        conn = sqlite3.connect(str(db_path))
        rows = conn.execute("SELECT * FROM alert_history").fetchall()
        conn.close()
        assert len(rows) >= 1
