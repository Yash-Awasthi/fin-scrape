"""
Proper scoring from properscoring — forecast evaluation metrics.
"""
from dataclasses import dataclass
from typing import List
import math


@dataclass
class ForecastScore:
    brier_score: float = 0.0
    log_loss: float = 0.0
    crps: float = 0.0
    reliability: float = 0.0
    resolution: float = 0.0
    discrimination: float = 0.0


def brier_score(predictions: List[float], outcomes: List[int]) -> float:
    if not predictions or not outcomes or len(predictions) != len(outcomes):
        return 1.0
    return sum((p - o) ** 2 for p, o in zip(predictions, outcomes)) / len(predictions)


def log_loss(predictions: List[float], outcomes: List[int]) -> float:
    eps = 1e-15
    clipped = [max(eps, min(1 - eps, p)) for p in predictions]
    losses = [-o * math.log(p) - (1 - o) * math.log(1 - p) for p, o in zip(clipped, outcomes)]
    return sum(losses) / len(losses) if losses else 0.0


def crps(predictions: List[float], outcomes: List[float]) -> float:
    if not predictions or not outcomes or len(predictions) != len(outcomes):
        return 1.0
    scores = []
    for p, o in zip(predictions, outcomes):
        if p >= o:
            scores.append(p - o)
        else:
            scores.append(o - p)
    return sum(scores) / len(scores) if scores else 0.0


def reliability_diagram(predictions: List[float], outcomes: List[int], bins: int = 10) -> List[dict]:
    bin_edges = [i / bins for i in range(bins + 1)]
    results = []
    for i in range(bins):
        lo, hi = bin_edges[i], bin_edges[i + 1]
        in_bin = [(p, o) for p, o in zip(predictions, outcomes) if lo <= p < hi]
        if in_bin:
            mean_pred = sum(p for p, _ in in_bin) / len(in_bin)
            mean_obs = sum(o for _, o in in_bin) / len(in_bin)
            results.append({"bin": f"{lo:.1f}-{hi:.1f}", "mean_prediction": mean_pred, "mean_outcome": mean_obs, "count": len(in_bin)})
    return results


def evaluate_forecast(predictions: List[float], outcomes: List[int]) -> ForecastScore:
    return ForecastScore(
        brier_score=brier_score(predictions, outcomes),
        log_loss=log_loss(predictions, outcomes),
    )
