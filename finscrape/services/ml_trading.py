"""
ML trading from machine-learning-for-trading — predictive models.
"""
from dataclasses import dataclass
from typing import List
import math


@dataclass
class MLPrediction:
    direction: str  # up, down, flat
    confidence: float
    predicted_return: float
    features_used: List[str]


def compute_features(prices: List[float]) -> dict:
    if len(prices) < 30:
        return {}
    returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
    momentum_5 = (prices[-1] / prices[-6] - 1) if len(prices) >= 6 else 0
    momentum_20 = (prices[-1] / prices[-21] - 1) if len(prices) >= 21 else 0
    volatility = math.sqrt(sum(r**2 for r in returns[-20:]) / min(20, len(returns)))
    sma_5 = sum(prices[-5:]) / 5
    sma_20 = sum(prices[-20:]) / 20
    sma_ratio = sma_5 / sma_20 if sma_20 > 0 else 1.0
    mean_return = sum(returns[-20:]) / min(20, len(returns))
    return {"momentum_5": momentum_5, "momentum_20": momentum_20, "volatility": volatility, "sma_ratio": sma_ratio, "mean_return": mean_return}


def simple_ml_predict(prices: List[float]) -> MLPrediction:
    features = compute_features(prices)
    if not features:
        return MLPrediction(direction="flat", confidence=0.3, predicted_return=0, features_used=[])
    score = 0.0
    used = []
    if features["momentum_5"] > 0.02: score += 0.3; used.append("momentum_5")
    elif features["momentum_5"] < -0.02: score -= 0.3; used.append("momentum_5")
    if features["sma_ratio"] > 1.02: score += 0.2; used.append("sma_ratio")
    elif features["sma_ratio"] < 0.98: score -= 0.2; used.append("sma_ratio")
    if features["momentum_20"] > 0.05: score += 0.2; used.append("momentum_20")
    elif features["momentum_20"] < -0.05: score -= 0.2; used.append("momentum_20")
    if features["volatility"] < 0.02: score += 0.1; used.append("volatility")
    direction = "up" if score > 0.2 else "down" if score < -0.2 else "flat"
    confidence = min(0.9, abs(score) + 0.3)
    predicted_return = score * features.get("volatility", 0.02) * 5
    return MLPrediction(direction=direction, confidence=round(confidence, 3), predicted_return=round(predicted_return, 4), features_used=used)


def backtest_ml_strategy(prices: List[float], window: int = 30) -> dict:
    trades = []
    for i in range(window, len(prices)):
        subset = prices[i - window:i]
        pred = simple_ml_predict(subset)
        actual_return = (prices[i] - prices[i-1]) / prices[i-1]
        pnl = actual_return if pred.direction == "up" else -actual_return if pred.direction == "down" else 0
        trades.append({"prediction": pred.direction, "actual": actual_return, "pnl": pnl})
    wins = sum(1 for t in trades if t["pnl"] > 0)
    total_pnl = sum(t["pnl"] for t in trades)
    return {"total_trades": len(trades), "win_rate": wins / len(trades) if trades else 0, "total_pnl": total_pnl, "avg_pnl": total_pnl / len(trades) if trades else 0}
