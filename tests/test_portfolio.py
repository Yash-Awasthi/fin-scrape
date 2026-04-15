"""Tests for the portfolio tracking system."""

import pytest
from finscrape.portfolio import PortfolioManager, Position, Watchlist


@pytest.fixture
def pm(tmp_path):
    db = tmp_path / "test.db"
    return PortfolioManager(db_path=db)


class TestPositions:
    def test_add_and_get(self, pm):
        pm.add_position("AAPL", shares=100, avg_cost=150.0, current_price=175.0)
        pos = pm.get_position("AAPL")
        assert pos is not None
        assert pos.ticker == "AAPL"
        assert pos.shares == 100
        assert pos.avg_cost == 150.0
        assert pos.current_price == 175.0

    def test_position_pnl(self, pm):
        pm.add_position("AAPL", shares=100, avg_cost=150.0, current_price=175.0)
        pos = pm.get_position("AAPL")
        assert pos.market_value == 17500.0
        assert pos.cost_basis == 15000.0
        assert pos.unrealized_pnl == 2500.0
        assert abs(pos.unrealized_pnl_pct - 16.67) < 0.1

    def test_update_position(self, pm):
        pm.add_position("AAPL", shares=100, avg_cost=150.0)
        pm.add_position("AAPL", shares=200, avg_cost=160.0)
        pos = pm.get_position("AAPL")
        assert pos.shares == 200
        assert pos.avg_cost == 160.0

    def test_remove_position(self, pm):
        pm.add_position("AAPL", shares=100, avg_cost=150.0)
        assert pm.remove_position("AAPL") is True
        assert pm.get_position("AAPL") is None
        assert pm.remove_position("AAPL") is False

    def test_get_all_positions(self, pm):
        pm.add_position("AAPL", shares=100, avg_cost=150.0)
        pm.add_position("MSFT", shares=50, avg_cost=300.0)
        positions = pm.get_all_positions()
        assert len(positions) == 2
        tickers = {p.ticker for p in positions}
        assert tickers == {"AAPL", "MSFT"}

    def test_portfolio_tickers(self, pm):
        pm.add_position("AAPL", shares=100, avg_cost=150.0)
        pm.add_position("GOOGL", shares=20, avg_cost=140.0)
        assert pm.portfolio_tickers() == {"AAPL", "GOOGL"}

    def test_update_prices(self, pm):
        pm.add_position("AAPL", shares=100, avg_cost=150.0, current_price=150.0)
        pm.add_position("MSFT", shares=50, avg_cost=300.0, current_price=300.0)
        pm.update_prices({"AAPL": 180.0, "MSFT": 320.0})
        assert pm.get_position("AAPL").current_price == 180.0
        assert pm.get_position("MSFT").current_price == 320.0

    def test_total_value(self, pm):
        pm.add_position("AAPL", shares=100, avg_cost=150.0, current_price=175.0)
        pm.add_position("MSFT", shares=50, avg_cost=300.0, current_price=350.0)
        assert pm.total_value() == 100 * 175 + 50 * 350

    def test_case_insensitive_ticker(self, pm):
        pm.add_position("aapl", shares=100, avg_cost=150.0)
        pos = pm.get_position("AAPL")
        assert pos is not None
        assert pos.ticker == "AAPL"

    def test_position_with_tags(self, pm):
        pm.add_position("AAPL", shares=100, avg_cost=150.0, tags=["tech", "long-term"])
        pos = pm.get_position("AAPL")
        assert pos.tags == ["tech", "long-term"]

    def test_zero_cost_pnl(self, pm):
        pos = Position(ticker="AAPL", shares=100, avg_cost=0, current_price=175.0)
        assert pos.unrealized_pnl == 0.0
        assert pos.unrealized_pnl_pct == 0.0


class TestWatchlists:
    def test_create_and_get(self, pm):
        pm.create_watchlist("tech", ["AAPL", "MSFT", "GOOGL"], "Tech watchlist")
        wl = pm.get_watchlist("tech")
        assert wl is not None
        assert wl.name == "tech"
        assert set(wl.tickers) == {"AAPL", "MSFT", "GOOGL"}
        assert wl.description == "Tech watchlist"

    def test_add_to_watchlist(self, pm):
        pm.create_watchlist("tech", ["AAPL"])
        pm.add_to_watchlist("tech", ["MSFT", "GOOGL"])
        wl = pm.get_watchlist("tech")
        assert set(wl.tickers) == {"AAPL", "MSFT", "GOOGL"}

    def test_add_to_nonexistent_creates(self, pm):
        pm.add_to_watchlist("energy", ["XOM", "CVX"])
        wl = pm.get_watchlist("energy")
        assert wl is not None
        assert set(wl.tickers) == {"CVX", "XOM"}

    def test_remove_from_watchlist(self, pm):
        pm.create_watchlist("tech", ["AAPL", "MSFT", "GOOGL"])
        pm.remove_from_watchlist("tech", ["MSFT"])
        wl = pm.get_watchlist("tech")
        assert "MSFT" not in wl.tickers

    def test_delete_watchlist(self, pm):
        pm.create_watchlist("tech", ["AAPL"])
        assert pm.delete_watchlist("tech") is True
        assert pm.get_watchlist("tech") is None

    def test_all_watched_tickers(self, pm):
        pm.add_position("AAPL", shares=100, avg_cost=150.0)
        pm.create_watchlist("tech", ["MSFT", "GOOGL"])
        pm.create_watchlist("energy", ["XOM"])
        watched = pm.all_watched_tickers()
        assert watched == {"AAPL", "MSFT", "GOOGL", "XOM"}

    def test_get_all_watchlists(self, pm):
        pm.create_watchlist("tech", ["AAPL"])
        pm.create_watchlist("energy", ["XOM"])
        wls = pm.get_all_watchlists()
        assert len(wls) == 2


class TestSignalWeighting:
    def test_held_position_high_relevance(self, pm):
        pm.add_position("AAPL", shares=100, avg_cost=150.0, current_price=175.0)
        event = {"tickers": ["AAPL"], "signal_score": 3, "verdict": "INVEST"}
        weighted = pm.weight_signal(event)
        assert weighted["in_portfolio"] is True
        assert weighted["portfolio_relevance"] >= 0.7

    def test_watched_ticker_medium_relevance(self, pm):
        pm.create_watchlist("tech", ["AAPL"])
        event = {"tickers": ["AAPL"], "signal_score": 3}
        weighted = pm.weight_signal(event)
        assert weighted["in_portfolio"] is False
        assert weighted["portfolio_relevance"] == 0.6

    def test_unrelated_ticker_zero_relevance(self, pm):
        pm.add_position("AAPL", shares=100, avg_cost=150.0)
        event = {"tickers": ["XYZ"], "signal_score": 3}
        weighted = pm.weight_signal(event)
        assert weighted["portfolio_relevance"] == 0.0
        assert weighted["in_portfolio"] is False

    def test_weighted_score_amplified(self, pm):
        pm.add_position("AAPL", shares=100, avg_cost=150.0, current_price=175.0)
        event = {"tickers": ["AAPL"], "signal_score": 3}
        weighted = pm.weight_signal(event)
        # With 100% portfolio weight, score should be amplified
        assert weighted["weighted_score"] >= 3

    def test_filter_relevant_events(self, pm):
        pm.add_position("AAPL", shares=100, avg_cost=150.0, current_price=175.0)
        events = [
            {"tickers": ["AAPL"], "signal_score": 3, "verdict": "INVEST"},
            {"tickers": ["XYZ"], "signal_score": 2, "verdict": "OBSERVE"},
            {"tickers": ["MSFT"], "signal_score": -3, "verdict": "CAUTIOUS"},
        ]
        relevant = pm.filter_relevant_events(events)
        assert len(relevant) == 1
        assert relevant[0]["tickers"] == ["AAPL"]


class TestPortfolioAlerts:
    def test_invest_on_held_generates_alert(self, pm):
        pm.add_position("AAPL", shares=100, avg_cost=150.0)
        events = [{"tickers": ["AAPL"], "signal_score": 4, "verdict": "INVEST",
                    "subject": "Apple beats earnings"}]
        alerts = pm.check_and_alert(events)
        assert len(alerts) >= 1
        assert any(a["alert_type"] == "position_invest" for a in alerts)

    def test_pullout_on_held_generates_alert(self, pm):
        pm.add_position("AAPL", shares=100, avg_cost=150.0)
        events = [{"tickers": ["AAPL"], "signal_score": -4, "verdict": "PULL_OUT",
                    "subject": "Apple faces major lawsuit"}]
        alerts = pm.check_and_alert(events)
        assert any(a["alert_type"] == "position_pull_out" for a in alerts)

    def test_high_impact_generates_alert(self, pm):
        pm.add_position("AAPL", shares=100, avg_cost=150.0)
        events = [{"tickers": ["AAPL"], "signal_score": 5, "verdict": "INVEST",
                    "subject": "Apple acquisition"}]
        alerts = pm.check_and_alert(events)
        assert any(a["alert_type"] == "high_impact" for a in alerts)

    def test_observe_on_held_no_alert(self, pm):
        pm.add_position("AAPL", shares=100, avg_cost=150.0)
        events = [{"tickers": ["AAPL"], "signal_score": 1, "verdict": "OBSERVE",
                    "subject": "Minor news"}]
        alerts = pm.check_and_alert(events)
        assert len(alerts) == 0

    def test_watched_high_confidence_alert(self, pm):
        pm.create_watchlist("tech", ["MSFT"])
        events = [{"tickers": ["MSFT"], "signal_score": 4, "verdict": "INVEST",
                    "confidence": 0.9, "subject": "MSFT beats big"}]
        alerts = pm.check_and_alert(events)
        assert any(a["alert_type"] == "watchlist_invest" for a in alerts)

    def test_get_recent_alerts(self, pm):
        pm.add_alert("AAPL", "test", "Test alert")
        alerts = pm.get_recent_alerts()
        assert len(alerts) == 1
        assert alerts[0]["ticker"] == "AAPL"


class TestSummary:
    def test_summary_structure(self, pm):
        pm.add_position("AAPL", shares=100, avg_cost=150.0, current_price=175.0)
        pm.create_watchlist("tech", ["MSFT"])
        s = pm.summary()
        assert s["positions"] == 1
        assert s["total_value"] == 17500.0
        assert "AAPL" in s["tickers"]
        assert len(s["watchlists"]) == 1


class TestPositionDataclass:
    def test_to_dict(self):
        pos = Position(ticker="AAPL", shares=100, avg_cost=150.0, current_price=175.0)
        d = pos.to_dict()
        assert d["ticker"] == "AAPL"
        assert d["market_value"] == 17500.0
        assert d["unrealized_pnl"] == 2500.0

    def test_from_dict(self):
        d = {"ticker": "AAPL", "shares": 100, "avg_cost": 150.0, "current_price": 175.0}
        pos = Position.from_dict(d)
        assert pos.ticker == "AAPL"
        assert pos.shares == 100
