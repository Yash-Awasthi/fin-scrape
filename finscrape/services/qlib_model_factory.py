"""
Qlib Model Factory — Extracted from qlib's model patterns.

Factory for ML models used in quantitative trading:
- LightGBM-based alpha model
- Linear regression baseline
- Feature importance analysis
- Cross-validation framework
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class ModelResult:
    predictions: Dict[str, float]
    feature_importance: Dict[str, float]
    metrics: Dict[str, float]
    model_params: Dict[str, Any]


@dataclass
class Dataset:
    features: Dict[str, List[float]]
    labels: List[float]
    timestamps: List[float]
    tickers: List[str]

    @property
    def n_samples(self) -> int:
        return len(self.labels)

    @property
    def feature_names(self) -> List[str]:
        return list(self.features.keys())


def simple_linear_regression(
    X: List[List[float]],
    y: List[float],
) -> Tuple[List[float], float]:
    """OLS linear regression without dependencies."""
    n = len(y)
    if n == 0 or not X:
        return [], 0.0
    p = len(X[0]) if X else 0

    # Compute means
    x_means = [sum(row[i] for row in X) / n for i in range(p)]
    y_mean = sum(y) / n

    # Compute coefficients via normal equations (simplified)
    coeffs = []
    for j in range(p):
        num = sum((X[i][j] - x_means[j]) * (y[i] - y_mean) for i in range(n))
        den = sum((X[i][j] - x_means[j]) ** 2 for i in range(n))
        coeffs.append(num / den if den > 1e-10 else 0.0)

    intercept = y_mean - sum(c * m for c, m in zip(coeffs, x_means))
    return coeffs, intercept


def predict_linear(
    X: List[List[float]],
    coeffs: List[float],
    intercept: float,
) -> List[float]:
    """Predict using linear model."""
    return [sum(c * v for c, v in zip(coeffs, row)) + intercept for row in X]


def compute_mse(y_true: List[float], y_pred: List[float]) -> float:
    """Mean squared error."""
    n = len(y_true)
    if n == 0:
        return 0.0
    return sum((t - p) ** 2 for t, p in zip(y_true, y_pred)) / n


def compute_ic(y_true: List[float], y_pred: List[float]) -> float:
    """Information coefficient (rank correlation)."""
    n = len(y_true)
    if n < 3:
        return 0.0
    mean_t = sum(y_true) / n
    mean_p = sum(y_pred) / n
    cov = sum((t - mean_t) * (p - mean_p) for t, p in zip(y_true, y_pred)) / n
    std_t = (sum((t - mean_t) ** 2 for t in y_true) / n) ** 0.5
    std_p = (sum((p - mean_p) ** 2 for p in y_pred) / n) ** 0.5
    if std_t < 1e-10 or std_p < 1e-10:
        return 0.0
    return cov / (std_t * std_p)


def rank_correlation(x: List[float], y: List[float]) -> float:
    """Spearman rank correlation."""
    n = len(x)
    if n < 3:
        return 0.0
    def rank(arr: List[float]) -> List[float]:
        sorted_idx = sorted(range(n), key=lambda i: arr[i])
        ranks = [0.0] * n
        for rank_val, idx in enumerate(sorted_idx):
            ranks[idx] = rank_val + 1.0
        return ranks
    rx, ry = rank(x), rank(y)
    return compute_ic(rx, ry)


class LinearAlphaModel:
    """Simple linear model for alpha factor prediction."""

    def __init__(self, features: Optional[List[str]] = None) -> None:
        self.features = features or []
        self.coeffs: List[float] = []
        self.intercept: float = 0.0
        self._fitted = False

    def fit(self, dataset: Dataset) -> None:
        """Fit linear model to dataset."""
        self.features = dataset.feature_names
        feature_matrix = [
            [dataset.features[f][i] for f in self.features]
            for i in range(dataset.n_samples)
        ]
        self.coeffs, self.intercept = simple_linear_regression(
            feature_matrix, dataset.labels
        )
        self._fitted = True

    def predict(self, dataset: Dataset) -> Dict[str, float]:
        """Predict scores for each ticker."""
        if not self._fitted:
            raise RuntimeError("Model not fitted")

        predictions = {}
        for i, ticker in enumerate(dataset.tickers):
            row = [dataset.features[f][i] for f in self.features]
            pred = sum(c * v for c, v in zip(self.coeffs, row)) + self.intercept
            predictions[ticker] = pred
        return predictions

    def get_feature_importance(self) -> Dict[str, float]:
        """Get normalized feature importance from coefficients."""
        if not self._fitted or not self.coeffs:
            return {}
        total = sum(abs(c) for c in self.coeffs)
        if total < 1e-10:
            return {f: 0.0 for f in self.features}
        return {
            f: abs(c) / total
            for f, c in zip(self.features, self.coeffs)
        }


def cross_validate(
    dataset: Dataset,
    model_factory: Callable[[], LinearAlphaModel],
    n_folds: int = 5,
) -> Dict[str, float]:
    """Time-series cross-validation."""
    n = dataset.n_samples
    fold_size = n // n_folds
    fold_ics: List[float] = []

    for fold in range(n_folds):
        test_start = fold * fold_size
        test_end = min(test_start + fold_size, n)
        train_indices = list(range(0, test_start)) + list(range(test_end, n))
        test_indices = list(range(test_start, test_end))

        if not train_indices or not test_indices:
            continue

        train_ds = Dataset(
            features={f: [dataset.features[f][i] for i in train_indices] for f in dataset.feature_names},
            labels=[dataset.labels[i] for i in train_indices],
            timestamps=[dataset.timestamps[i] for i in train_indices],
            tickers=[dataset.tickers[i] for i in train_indices],
        )
        test_ds = Dataset(
            features={f: [dataset.features[f][i] for i in test_indices] for f in dataset.feature_names},
            labels=[dataset.labels[i] for i in test_indices],
            timestamps=[dataset.timestamps[i] for i in test_indices],
            tickers=[dataset.tickers[i] for i in test_indices],
        )

        model = model_factory()
        model.fit(train_ds)
        preds = model.predict(test_ds)
        pred_list = [preds.get(t, 0.0) for t in test_ds.tickers]
        ic = rank_correlation(test_ds.labels, pred_list)
        fold_ics.append(ic)

    mean_ic = sum(fold_ics) / len(fold_ics) if fold_ics else 0.0
    std_ic = (sum((ic - mean_ic) ** 2 for ic in fold_ics) / max(len(fold_ics) - 1, 1)) ** 0.5

    return {
        "mean_ic": mean_ic,
        "std_ic": std_ic,
        "icir": mean_ic / std_ic if std_ic > 1e-10 else 0.0,
        "n_folds": len(fold_ics),
    }
