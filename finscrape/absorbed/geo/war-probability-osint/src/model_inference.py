"""
model_inference.py — Loads the trained Random Forest model and outputs a
real-time probability of military escalation.

Public API
----------
load_model(model_dir)                     -> (model, scaler)
predict_escalation(features, model_dir)   -> dict
    Returns:
        probability   : float (0.0 – 1.0)
        risk_level    : str   ("LOW" | "MODERATE" | "HIGH" | "CRITICAL")
        confidence    : float (model confidence measure)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEFAULT_MODEL_DIR = Path("models")
MODEL_FILE  = "random_forest_v1.pkl"
SCALER_FILE = "scaler.pkl"

RISK_THRESHOLDS = {
    "LOW":      0.25,
    "MODERATE": 0.50,
    "HIGH":     0.75,
    "CRITICAL": 1.01,  # anything ≥ 0.75
}


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------
_cache: dict = {}

def load_model(model_dir: Path | str = DEFAULT_MODEL_DIR):
    """
    Load the Random Forest model and StandardScaler from disk.
    Results are cached after first call.

    Returns
    -------
    (model, scaler) tuple.
    """
    model_dir = Path(model_dir)
    cache_key = str(model_dir)

    if cache_key in _cache:
        return _cache[cache_key]

    try:
        import joblib
    except ImportError:
        raise ImportError("joblib is required.  pip install joblib")

    model_path  = model_dir / MODEL_FILE
    scaler_path = model_dir / SCALER_FILE

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found at {model_path}. "
            f"Run `python models/train_model.py` first."
        )
    if not scaler_path.exists():
        raise FileNotFoundError(
            f"Scaler not found at {scaler_path}. "
            f"Run `python models/train_model.py` first."
        )

    model  = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    _cache[cache_key] = (model, scaler)
    return model, scaler


# ---------------------------------------------------------------------------
# Risk classification
# ---------------------------------------------------------------------------
def _classify_risk(probability: float) -> str:
    for level, upper in RISK_THRESHOLDS.items():
        if probability < upper:
            return level
    return "CRITICAL"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_escalation(
    features: np.ndarray,
    model_dir: Path | str = DEFAULT_MODEL_DIR,
) -> dict:
    """
    Predict military-escalation probability from an (1, 8) feature array.

    Parameters
    ----------
    features  : np.ndarray of shape (1, N_FEATURES) — output of
                feature_engineering.compute_features().
    model_dir : Path to directory containing .pkl files.

    Returns
    -------
    dict with keys:  probability, risk_level, confidence, feature_importances
    """
    model, scaler = load_model(model_dir)

    # Scale features using the same scaler used during training
    features_scaled = scaler.transform(features)

    # Predict probability (class 1 = escalation)
    proba = model.predict_proba(features_scaled)
    escalation_prob = float(proba[0][1])

    # Confidence: how far from 50-50 the model is
    confidence = abs(escalation_prob - 0.5) * 2.0  # 0..1 scale

    # Per-feature importance from the trained model
    importances = dict(zip(
        _get_feature_names_from_model(model, features.shape[1]),
        model.feature_importances_,
    ))

    return {
        "probability":         round(escalation_prob, 4),
        "risk_level":          _classify_risk(escalation_prob),
        "confidence":          round(confidence, 4),
        "feature_importances": {k: round(v, 4) for k, v in importances.items()},
    }


def _get_feature_names_from_model(model, n_features: int) -> list[str]:
    """Try to get feature names from the model, fall back to generic."""
    if hasattr(model, "feature_names_in_"):
        return list(model.feature_names_in_)
    # Fall back to the canonical list from feature_engineering
    try:
        from src.feature_engineering import get_feature_names
        names = get_feature_names()
        if len(names) == n_features:
            return names
    except ImportError:
        pass
    return [f"feature_{i}" for i in range(n_features)]


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Requires models to exist — run models/train_model.py first
    test_features = np.array([[2.5, 0.25, 1.5, 4.0, 3.0, 1.8, 1.5, 1.2]])
    try:
        result = predict_escalation(test_features)
        print("=== Escalation Prediction ===")
        print(f"  Probability : {result['probability']:.1%}")
        print(f"  Risk Level  : {result['risk_level']}")
        print(f"  Confidence  : {result['confidence']:.1%}")
        print(f"  Feature Importances:")
        for fname, imp in result["feature_importances"].items():
            print(f"    {fname:25s}: {imp:.4f}")
    except FileNotFoundError as e:
        print(f"[model_inference] {e}")
