"""
Council Backtesting Engine

Run historical replay of council decisions against past market data,
measure prediction accuracy, compute performance metrics, and generate
HTML reports.  Pure functions, no DB.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HistoricalEvent:
    """A past event with council score and actual outcome."""
    date: str
    ticker: str
    title: str
    council_score: int        # -5 to +5
    council_confidence: float # 0-1
    actual_return_pct: float  # % change over evaluation window
    sector: str = "unknown"


@dataclass
class PerformanceMetrics:
    """Aggregated backtest performance."""
    total_events: int
    correct_predictions: int
    accuracy_pct: float
    avg_return_when_correct: float
    avg_return_when_wrong: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate: float
    avg_score: float
    total_return_pct: float
    benchmark_return_pct: float
    alpha: float


# ── Signal Accuracy ────────────────────────────────────────────────────────

def measure_signal_accuracy(events: list[HistoricalEvent]) -> dict:
    """
    Measure how well council scores predict actual returns.

    A "correct" prediction: score and actual return have the same sign.
    """
    if not events:
        return {"error": "No events to evaluate."}

    correct = 0
    by_direction = {"bullish_correct": 0, "bullish_total": 0,
                    "bearish_correct": 0, "bearish_total": 0,
                    "neutral_correct": 0, "neutral_total": 0}

    for e in events:
        predicted_direction = 1 if e.council_score > 0 else (-1 if e.council_score < 0 else 0)
        actual_direction = 1 if e.actual_return_pct > 0 else (-1 if e.actual_return_pct < 0 else 0)

        is_correct = predicted_direction == actual_direction
        if is_correct:
            correct += 1

        if predicted_direction > 0:
            by_direction["bullish_total"] += 1
            if is_correct:
                by_direction["bullish_correct"] += 1
        elif predicted_direction < 0:
            by_direction["bearish_total"] += 1
            if is_correct:
                by_direction["bearish_correct"] += 1
        else:
            by_direction["neutral_total"] += 1
            if is_correct:
                by_direction["neutral_correct"] += 1

    accuracy = correct / len(events) * 100

    # Confidence-weighted accuracy
    weighted_correct = sum(
        e.council_confidence if (1 if e.council_score > 0 else -1) == (1 if e.actual_return_pct > 0 else -1)
        else 0
        for e in events
    )
    weighted_accuracy = weighted_correct / len(events) * 100 if events else 0

    return {
        "accuracy_pct": round(accuracy, 1),
        "weighted_accuracy_pct": round(weighted_accuracy, 1),
        "correct": correct,
        "total": len(events),
        "bullish": {
            "correct": by_direction["bullish_correct"],
            "total": by_direction["bullish_total"],
            "accuracy": round(by_direction["bullish_correct"] / max(1, by_direction["bullish_total"]) * 100, 1),
        },
        "bearish": {
            "correct": by_direction["bearish_correct"],
            "total": by_direction["bearish_total"],
            "accuracy": round(by_direction["bearish_correct"] / max(1, by_direction["bearish_total"]) * 100, 1),
        },
    }


# ── Performance Metrics ────────────────────────────────────────────────────

def compute_performance(
    events: list[HistoricalEvent],
    benchmark_return_pct: float = 0.0,
) -> PerformanceMetrics:
    """
    Compute full backtest performance metrics including Sharpe ratio
    and max drawdown from council scores.
    """
    if not events:
        return PerformanceMetrics(
            total_events=0, correct_predictions=0, accuracy_pct=0.0,
            avg_return_when_correct=0.0, avg_return_when_wrong=0.0,
            sharpe_ratio=0.0, max_drawdown_pct=0.0, win_rate=0.0,
            avg_score=0.0, total_return_pct=0.0,
            benchmark_return_pct=benchmark_return_pct, alpha=0.0,
        )

    # Simulate portfolio: invest proportionally to council score
    # Map score [-5, +5] → position size [-1.0, +1.0]
    returns = []
    for e in events:
        position = e.council_score / 5.0  # -1 to +1
        pnl = position * e.actual_return_pct * 0.5  # 50% max exposure
        returns.append(pnl)

    # Correct predictions
    correct = sum(
        1 for e in events
        if (1 if e.council_score > 0 else -1) == (1 if e.actual_return_pct > 0 else -1)
    )

    correct_returns = [r for r, e in zip(returns, events)
                       if (1 if e.council_score > 0 else -1) == (1 if e.actual_return_pct > 0 else -1)]
    wrong_returns = [r for r, e in zip(returns, events)
                     if (1 if e.council_score > 0 else -1) != (1 if e.actual_return_pct > 0 else -1)]

    # Sharpe ratio (annualized, assuming daily returns)
    if len(returns) > 1:
        avg_return = statistics.mean(returns)
        std_return = statistics.stdev(returns)
        sharpe = (avg_return / std_return * math.sqrt(252)) if std_return > 0 else 0.0
    else:
        avg_return = returns[0] if returns else 0.0
        sharpe = 0.0

    # Max drawdown
    cumulative = []
    running = 100.0
    for r in returns:
        running *= (1 + r / 100.0)
        cumulative.append(running)

    peak = cumulative[0]
    max_dd = 0.0
    for val in cumulative:
        peak = max(peak, val)
        dd = (peak - val) / peak * 100
        max_dd = max(max_dd, dd)

    total_return = (cumulative[-1] / 100.0 - 1) * 100 if cumulative else 0.0

    return PerformanceMetrics(
        total_events=len(events),
        correct_predictions=correct,
        accuracy_pct=round(correct / len(events) * 100, 1),
        avg_return_when_correct=round(statistics.mean(correct_returns), 2) if correct_returns else 0.0,
        avg_return_when_wrong=round(statistics.mean(wrong_returns), 2) if wrong_returns else 0.0,
        sharpe_ratio=round(sharpe, 3),
        max_drawdown_pct=round(max_dd, 2),
        win_rate=round(correct / len(events) * 100, 1),
        avg_score=round(statistics.mean([e.council_score for e in events]), 2),
        total_return_pct=round(total_return, 2),
        benchmark_return_pct=benchmark_return_pct,
        alpha=round(total_return - benchmark_return_pct, 2),
    )


# ── HTML Report ────────────────────────────────────────────────────────────

def generate_report(
    events: list[HistoricalEvent],
    accuracy: dict,
    performance: PerformanceMetrics,
) -> str:
    """Generate an HTML backtest report with embedded charts (CSS-only)."""
    # Build return distribution
    returns = [e.actual_return_pct for e in events]
    max_ret = max(abs(r) for r in returns) if returns else 1
    score_bins: dict[int, list[float]] = {}
    for e in events:
        bin_key = (e.council_score // 2) * 2  # bin by 2
        score_bins.setdefault(bin_key, []).append(e.actual_return_pct)

    bin_bars = ""
    for score in sorted(score_bins.keys()):
        vals = score_bins[score]
        avg = statistics.mean(vals)
        width = min(100, abs(avg) / max_ret * 80)
        color = "#00ff88" if avg > 0 else "#ff4444"
        label = f"Score {score:+d}"
        bin_bars += f"""
        <div style="display:flex;align-items:center;gap:8px;margin:4px 0;">
          <span style="width:70px;text-align:right;font-family:monospace;font-size:12px;color:#94a3b8;">{label}</span>
          <div style="height:18px;width:{width}%;background:{color};border-radius:3px;opacity:0.8;"></div>
          <span style="font-family:monospace;font-size:11px;color:#cbd5e1;">{avg:+.2f}%</span>
        </div>"""

    # Equity curve
    cum = 100.0
    equity_points = []
    for e in events:
        position = e.council_score / 5.0
        cum *= (1 + position * e.actual_return_pct * 0.5 / 100)
        equity_points.append(cum)
    max_eq = max(equity_points) if equity_points else 100
    min_eq = min(equity_points) if equity_points else 100
    eq_range = max_eq - min_eq if max_eq != min_eq else 1

    sparkline = " ".join(
        f"{(v - min_eq) / eq_range * 100:.1f}%"
        for v in equity_points
    )

    return f"""<!DOCTYPE html>
<html><head><title>Council Backtest Report</title>
<style>
  body {{ background: #0a0e1a; color: #e2e8f0; font-family: 'Inter', system-ui, sans-serif; padding: 40px; }}
  .card {{ background: #111827; border: 1px solid #1e293b; border-radius: 12px; padding: 24px; margin-bottom: 20px; }}
  h1 {{ color: #00ff88; font-size: 28px; margin-bottom: 8px; }}
  h2 {{ color: #94a3b8; font-size: 14px; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 16px; }}
  .stat {{ display: inline-block; text-align: center; padding: 16px 24px; margin: 4px; }}
  .stat-value {{ font-size: 32px; font-weight: 700; font-family: monospace; }}
  .stat-label {{ font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px; }}
  .green {{ color: #00ff88; }}
  .red {{ color: #ff4444; }}
  .amber {{ color: #ffaa00; }}
  .equity {{ height: 120px; display: flex; align-items: flex-end; gap: 2px; padding: 8px 0; }}
  .eq-bar {{ flex: 1; background: #00ff88; opacity: 0.6; border-radius: 2px 2px 0 0; min-width: 3px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ text-align: left; padding: 8px; color: #64748b; border-bottom: 1px solid #1e293b; font-size: 11px; text-transform: uppercase; }}
  td {{ padding: 8px; border-bottom: 1px solid #1e293b; font-family: monospace; }}
</style></head><body>
<h1>🏛️ Council Backtest Report</h1>
<p style="color:#64748b;">{performance.total_events} events analyzed • Generated by WorldFin Council</p>

<div class="card">
  <h2>Key Metrics</h2>
  <div style="display:flex;flex-wrap:wrap;">
    <div class="stat"><div class="stat-value green">{performance.accuracy_pct}%</div><div class="stat-label">Accuracy</div></div>
    <div class="stat"><div class="stat-value {'green' if performance.total_return_pct > 0 else 'red'}">{performance.total_return_pct:+.2f}%</div><div class="stat-label">Total Return</div></div>
    <div class="stat"><div class="stat-value {'green' if performance.sharpe_ratio > 0 else 'red'}">{performance.sharpe_ratio:.3f}</div><div class="stat-label">Sharpe Ratio</div></div>
    <div class="stat"><div class="stat-value red">{performance.max_drawdown_pct:.1f}%</div><div class="stat-label">Max Drawdown</div></div>
    <div class="stat"><div class="stat-value {'green' if performance.alpha > 0 else 'red'}">{performance.alpha:+.2f}%</div><div class="stat-label">Alpha vs Benchmark</div></div>
  </div>
</div>

<div class="card">
  <h2>Equity Curve</h2>
  <div class="equity">
    {"".join(f'<div class="eq-bar" style="height:{p}%;"></div>' for p in [(v - min_eq) / eq_range * 95 + 5 for v in equity_points])}
  </div>
  <div style="display:flex;justify-content:space-between;font-family:monospace;font-size:11px;color:#64748b;">
    <span>Start: 100.00</span><span>End: {equity_points[-1]:.2f}</span>
  </div>
</div>

<div class="card">
  <h2>Avg Return by Score Bucket</h2>
  {bin_bars}
</div>

<div class="card">
  <h2>Directional Accuracy</h2>
  <table>
    <tr><th>Direction</th><th>Correct</th><th>Total</th><th>Accuracy</th></tr>
    <tr><td class="green">Bullish (+)</td><td>{accuracy.get('bullish',{}).get('correct',0)}</td>
        <td>{accuracy.get('bullish',{}).get('total',0)}</td>
        <td class="green">{accuracy.get('bullish',{}).get('accuracy',0):.1f}%</td></tr>
    <tr><td class="red">Bearish (−)</td><td>{accuracy.get('bearish',{}).get('correct',0)}</td>
        <td>{accuracy.get('bearish',{}).get('total',0)}</td>
        <td class="red">{accuracy.get('bearish',{}).get('accuracy',0):.1f}%</td></tr>
  </table>
</div>

<div class="card">
  <h2>Recent Events</h2>
  <table>
    <tr><th>Date</th><th>Ticker</th><th>Score</th><th>Confidence</th><th>Return</th><th>Correct?</th></tr>
    {"".join(f'''<tr>
      <td>{e.date}</td><td>{e.ticker}</td>
      <td class="{'green' if e.council_score > 0 else 'red' if e.council_score < 0 else 'amber'}">{e.council_score:+d}</td>
      <td>{e.council_confidence:.2f}</td>
      <td class="{'green' if e.actual_return_pct > 0 else 'red'}">{e.actual_return_pct:+.2f}%</td>
      <td>{'✅' if (1 if e.council_score > 0 else -1) == (1 if e.actual_return_pct > 0 else -1) else '❌'}</td>
    </tr>''' for e in events[-20:])}
  </table>
</div>

<footer style="text-align:center;padding:20px;color:#475569;font-size:12px;">
  WorldFin Council Backtest • {performance.total_events} events
</footer>
</body></html>"""
