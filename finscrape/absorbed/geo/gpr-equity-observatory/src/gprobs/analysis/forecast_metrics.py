import numpy as np


def evaluate_forecasts(y_true, y_pred, task: str, benchmark_pred=None) -> dict:
    actual = np.asarray(y_true, dtype=float)
    predicted = np.asarray(y_pred, dtype=float)
    if len(actual) != len(predicted):
        raise ValueError("y_true and y_pred must have the same length")
    if len(actual) == 0:
        raise ValueError("forecast evaluation requires at least one observation")
    _assert_finite(actual, "y_true")
    _assert_finite(predicted, "y_pred")

    if task == "regression":
        if benchmark_pred is None:
            raise ValueError("benchmark_pred is required for regression OOS R2")
        benchmark = np.asarray(benchmark_pred, dtype=float)
        if len(benchmark) != len(actual):
            raise ValueError("benchmark_pred must have the same length as y_true")
        _assert_finite(benchmark, "benchmark_pred")
        errors = actual - predicted
        baseline_errors = actual - benchmark
        baseline_sse = float(np.sum(baseline_errors**2))
        model_sse = float(np.sum(errors**2))
        if baseline_sse == 0 and model_sse > 0:
            raise ValueError("benchmark_pred has zero error, so regression OOS R2 is undefined")
        return {
            "rmse": float(np.sqrt(np.mean(errors**2))),
            "mae": float(np.mean(np.abs(errors))),
            "oos_r2": 0.0 if baseline_sse == 0 else float(1 - model_sse / baseline_sse),
        }

    if task == "classification":
        labels = set(np.unique(actual))
        if not labels.issubset({0.0, 1.0}):
            raise ValueError("classification y_true must contain only 0/1 labels")
        if np.any((predicted < 0) | (predicted > 1)):
            raise ValueError("classification predictions must be probabilities in [0, 1]")
        probabilities = np.clip(predicted, 1e-12, 1 - 1e-12)
        predicted_labels = (probabilities >= 0.5).astype(int)
        return {
            "brier_score": float(np.mean((probabilities - actual) ** 2)),
            "log_loss": float(-np.mean(actual * np.log(probabilities) + (1 - actual) * np.log(1 - probabilities))),
            "directional_accuracy": float(np.mean(predicted_labels == actual)),
        }

    raise ValueError("task must be 'regression' or 'classification'")


def _assert_finite(values: np.ndarray, name: str) -> None:
    if not np.isfinite(values).all():
        raise ValueError(f"{name} must contain only finite numeric values")
