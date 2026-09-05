from dataclasses import dataclass

import numpy as np
import pandas as pd

from gprobs.analysis.forecast_metrics import evaluate_forecasts
from gprobs.analysis.time_splits import make_time_splits
from gprobs.features.shocks import expanding_standardize_shocks


@dataclass(frozen=True)
class ForecastModelSpec:
    model: str
    feature_cols: list[str]
    ridge_alpha: float = 0.0
    standardize_feature_cols: list[str] | None = None
    standardize_min_periods: int = 24


def expanding_window_forecast(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: list[str],
    min_train_months: int,
    test_window: int = 1,
    ridge_alpha: float = 0.0,
    standardize_feature_cols: list[str] | None = None,
    standardize_min_periods: int = 24,
) -> pd.DataFrame:
    if standardize_feature_cols:
        df = expanding_standardize_shocks(df, standardize_feature_cols, min_periods=standardize_min_periods)
        feature_cols = [f"{column}_z" if column in standardize_feature_cols else column for column in feature_cols]

    data = df.dropna(subset=[target_col, *feature_cols]).sort_values("date_month").reset_index(drop=True)
    rows = []
    for train, test in iter_expanding_window_frames(data, min_train_months, test_window):
        prediction = _predict_next(train, test, target_col, feature_cols, ridge_alpha)
        benchmark_prediction = np.repeat(train[target_col].mean(), len(test))
        for date, actual, predicted, benchmark in zip(
            test["date_month"], test[target_col], prediction, benchmark_prediction, strict=True
        ):
            rows.append(
                {
                    "date_month": date,
                    "actual": actual,
                    "predicted": predicted,
                    "benchmark_predicted": benchmark,
                }
            )
    return pd.DataFrame(rows)


def iter_expanding_window_frames(data: pd.DataFrame, min_train_months: int, test_window: int = 1):
    dates = pd.to_datetime(data["date_month"]).reset_index(drop=True)
    if dates.duplicated().any():
        raise ValueError("forecast data must contain one row per date_month")

    for split in make_time_splits(dates, min_train_months, test_window):
        train_end = len(split.train_dates)
        test_end = train_end + len(split.test_dates)
        yield data.iloc[:train_end], data.iloc[train_end:test_end]


def forecast_metric_row(
    model: str,
    df: pd.DataFrame,
    target_col: str,
    feature_cols: list[str],
    min_train_months: int,
    ridge_alpha: float = 0.0,
    standardize_feature_cols: list[str] | None = None,
    standardize_min_periods: int = 24,
) -> dict:
    forecasts = expanding_window_forecast(
        df,
        target_col,
        feature_cols,
        min_train_months=min_train_months,
        ridge_alpha=ridge_alpha,
        standardize_feature_cols=standardize_feature_cols,
        standardize_min_periods=standardize_min_periods,
    )
    if forecasts.empty:
        raise ValueError(f"no forecasts produced for {model}")
    metrics = evaluate_forecasts(
        forecasts["actual"],
        forecasts["predicted"],
        task="regression",
        benchmark_pred=forecasts["benchmark_predicted"],
    )
    return {
        "model": model,
        **metrics,
        "n_forecasts": len(forecasts),
        "first_forecast_date": _date_text(forecasts["date_month"].min()),
        "last_forecast_date": _date_text(forecasts["date_month"].max()),
        "forecast_window_aligned": True,
        "benchmark_model": "historical_mean",
    }


def forecast_metric_rows(
    df: pd.DataFrame,
    target_col: str,
    model_specs: list[ForecastModelSpec],
    min_train_months: int,
    benchmark_model: str = "historical_mean",
) -> list[dict]:
    forecasts_by_model = {
        spec.model: expanding_window_forecast(
            df,
            target_col,
            spec.feature_cols,
            min_train_months=min_train_months,
            ridge_alpha=spec.ridge_alpha,
            standardize_feature_cols=spec.standardize_feature_cols,
            standardize_min_periods=spec.standardize_min_periods,
        )
        for spec in model_specs
    }
    if benchmark_model not in forecasts_by_model:
        raise ValueError(f"benchmark model '{benchmark_model}' is not in model_specs")

    common_dates = _common_forecast_dates(forecasts_by_model)
    benchmark = _aligned_forecasts(forecasts_by_model[benchmark_model], common_dates)
    benchmark_pred = benchmark["predicted"].to_numpy(dtype=float)

    rows = []
    for spec in model_specs:
        forecasts = _aligned_forecasts(forecasts_by_model[spec.model], common_dates)
        metrics = evaluate_forecasts(
            forecasts["actual"],
            forecasts["predicted"],
            task="regression",
            benchmark_pred=benchmark_pred,
        )
        rows.append(
            {
                "model": spec.model,
                **metrics,
                "n_forecasts": len(forecasts),
                "first_forecast_date": _date_text(common_dates[0]),
                "last_forecast_date": _date_text(common_dates[-1]),
                "forecast_window_aligned": True,
                "benchmark_model": benchmark_model,
            }
        )
    return rows


def _predict_next(
    train: pd.DataFrame,
    test: pd.DataFrame,
    target_col: str,
    feature_cols: list[str],
    ridge_alpha: float,
) -> np.ndarray:
    if not feature_cols:
        return np.repeat(train[target_col].mean(), len(test))

    x_train = _with_intercept(train[feature_cols].to_numpy(dtype=float))
    y_train = train[target_col].to_numpy(dtype=float)
    x_test = _with_intercept(test[feature_cols].to_numpy(dtype=float))
    penalty = np.eye(x_train.shape[1]) * ridge_alpha
    penalty[0, 0] = 0.0
    beta = np.linalg.pinv(x_train.T @ x_train + penalty) @ x_train.T @ y_train
    return x_test @ beta


def _with_intercept(values: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones(len(values)), values])


def _common_forecast_dates(forecasts_by_model: dict[str, pd.DataFrame]) -> list[pd.Timestamp]:
    date_sets = [
        set(pd.to_datetime(forecasts["date_month"])) for forecasts in forecasts_by_model.values() if not forecasts.empty
    ]
    if len(date_sets) != len(forecasts_by_model):
        raise ValueError("all models must produce at least one forecast")
    common = sorted(set.intersection(*date_sets))
    if not common:
        raise ValueError("forecast models have no common evaluation dates")
    return common


def _aligned_forecasts(forecasts: pd.DataFrame, dates: list[pd.Timestamp]) -> pd.DataFrame:
    return forecasts[forecasts["date_month"].isin(dates)].sort_values("date_month").reset_index(drop=True)


def _date_text(value) -> str:
    return pd.Timestamp(value).date().isoformat()
