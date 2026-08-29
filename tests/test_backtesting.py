"""Tests for backtesting engine."""
import pytest
from finscrape.council.backtesting import (
    HistoricalEvent, measure_signal_accuracy, compute_performance, generate_report,
)


def _sample_events():
    return [
        HistoricalEvent("2026-01-01", "AAPL", "Earnings beat", 4, 0.9, 5.2, "tech"),
        HistoricalEvent("2026-01-02", "TSLA", "Delivery miss", -3, 0.7, -8.1, "auto"),
        HistoricalEvent("2026-01-03", "MSFT", "Cloud growth", 2, 0.6, 3.0, "tech"),
        HistoricalEvent("2026-01-04", "JPM", "Rate concerns", -2, 0.8, -1.5, "finance"),
        HistoricalEvent("2026-01-05", "AMZN", "AI investment", 5, 0.85, 7.0, "tech"),
        HistoricalEvent("2026-01-06", "XOM", "Oil surge", 3, 0.5, 2.5, "energy"),
        HistoricalEvent("2026-01-07", "PFE", "Drug trial fail", -4, 0.9, -12.0, "pharma"),
        HistoricalEvent("2026-01-08", "GOOGL", "Ad revenue up", 3, 0.7, 4.0, "tech"),
        HistoricalEvent("2026-01-09", "BA", "Safety concern", -3, 0.6, -5.5, "aero"),
        HistoricalEvent("2026-01-10", "NVDA", "AI demand", 5, 0.95, 9.0, "tech"),
    ]


class TestSignalAccuracy:
    def test_empty(self):
        assert "error" in measure_signal_accuracy([])

    def test_perfect_predictions(self):
        events = [
            HistoricalEvent("d", "A", "t", 3, 0.9, 5.0),
            HistoricalEvent("d", "B", "t", -3, 0.9, -5.0),
        ]
        r = measure_signal_accuracy(events)
        assert r["accuracy_pct"] == 100.0

    def test_mixed_predictions(self):
        events = _sample_events()
        r = measure_signal_accuracy(events)
        assert 0 <= r["accuracy_pct"] <= 100
        assert r["correct"] + (r["total"] - r["correct"]) == r["total"]

    def test_directional_breakdown(self):
        events = _sample_events()
        r = measure_signal_accuracy(events)
        assert "bullish" in r
        assert "bearish" in r
        assert r["bullish"]["total"] > 0
        assert r["bearish"]["total"] > 0

    def test_weighted_accuracy(self):
        events = _sample_events()
        r = measure_signal_accuracy(events)
        assert "weighted_accuracy_pct" in r
        assert 0 <= r["weighted_accuracy_pct"] <= 100


class TestComputePerformance:
    def test_empty(self):
        r = compute_performance([])
        assert r.total_events == 0
        assert r.accuracy_pct == 0.0

    def test_with_events(self):
        events = _sample_events()
        r = compute_performance(events)
        assert r.total_events == 10
        assert 0 <= r.win_rate <= 100
        assert isinstance(r.sharpe_ratio, float)
        assert r.max_drawdown_pct >= 0

    def test_alpha_calculation(self):
        events = _sample_events()
        r = compute_performance(events, benchmark_return_pct=5.0)
        assert r.benchmark_return_pct == 5.0
        assert isinstance(r.alpha, float)

    def test_positive_events_profitable(self):
        events = [
            HistoricalEvent("d", "A", "t", 5, 0.9, 10.0),
            HistoricalEvent("d", "B", "t", 5, 0.9, 8.0),
            HistoricalEvent("d", "C", "t", 5, 0.9, 6.0),
        ]
        r = compute_performance(events)
        assert r.total_return_pct > 0

    def test_negative_events_loss(self):
        events = [
            HistoricalEvent("d", "A", "t", 5, 0.9, -10.0),
            HistoricalEvent("d", "B", "t", 5, 0.9, -8.0),
        ]
        r = compute_performance(events)
        assert r.total_return_pct < 0


class TestGenerateReport:
    def test_generates_html(self):
        events = _sample_events()
        accuracy = measure_signal_accuracy(events)
        perf = compute_performance(events)
        report = generate_report(events, accuracy, perf)
        assert "<!DOCTYPE html>" in report
        assert "Case 71-C" in report or "Council" in report
        assert "Accuracy" in report

    def test_report_has_chart_data(self):
        events = _sample_events()
        accuracy = measure_signal_accuracy(events)
        perf = compute_performance(events)
        report = generate_report(events, accuracy, perf)
        assert "equity" in report.lower() or "Equity" in report
