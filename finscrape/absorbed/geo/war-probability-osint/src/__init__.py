"""
Core logic and data pipelines for War-Probability OSINT.

Modules
-------
data_cleaner         : Normalizes timestamps and merges multi-source data.
feature_engineering  : Computes anomaly scores from cleaned data.
model_inference      : Loads trained ML model and predicts escalation probability.
"""

from src import data_cleaner
from src import feature_engineering
from src import model_inference

__all__ = [
    "data_cleaner",
    "feature_engineering",
    "model_inference",
]
