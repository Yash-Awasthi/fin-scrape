"""
train_model.py — Generate synthetic training data and train the Random Forest
escalation-probability model.

Since real labeled escalation events are extremely rare, this script generates
synthetic feature vectors based on documented conflict signatures:

  * "Normal" regime  — low anomaly scores drawn from calm-day distributions.
  * "Escalation" regime — high anomaly scores modeled on known events
    (e.g., April 2024 Iran–Israel exchange, Oct 2023 onset, pre-Iraq 2003).

Outputs
-------
models/random_forest_v1.pkl   —  Trained RandomForestClassifier.
models/scaler.pkl             —  Fitted StandardScaler.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Feature definitions (must match feature_engineering.FEATURE_NAMES)
# ---------------------------------------------------------------------------
FEATURE_NAMES = [
    "military_flight_surge",
    "tanker_refueler_ratio",
    "foot_traffic_anomaly",
    "gdelt_negative_tone",
    "gdelt_article_spike",
    "oil_price_z",
    "defense_stock_z",
    "gold_price_z",
]


# ---------------------------------------------------------------------------
# Synthetic data generation
# ---------------------------------------------------------------------------
def _generate_normal_samples(n: int = 800, rng: np.random.Generator | None = None) -> np.ndarray:
    """Generate feature vectors for 'normal / calm' days (label = 0)."""
    if rng is None:
        rng = np.random.default_rng(42)

    samples = np.column_stack([
        rng.normal(loc=0.0,  scale=0.5,  size=n),   # military_flight_surge
        rng.uniform(low=0.0, high=0.10,  size=n),    # tanker_refueler_ratio
        rng.normal(loc=0.0,  scale=0.15, size=n),    # foot_traffic_anomaly (shifted: 0 = normal)
        rng.normal(loc=1.0,  scale=1.0,  size=n),    # gdelt_negative_tone (mildly negative news is normal)
        rng.normal(loc=0.0,  scale=0.5,  size=n),    # gdelt_article_spike
        rng.normal(loc=0.0,  scale=0.5,  size=n),    # oil_price_z
        rng.normal(loc=0.0,  scale=0.5,  size=n),    # defense_stock_z
        rng.normal(loc=0.0,  scale=0.5,  size=n),    # gold_price_z
    ])
    # Clip foot_traffic_anomaly ≥ 0
    samples[:, 2] = np.clip(samples[:, 2], 0, None)
    return samples


def _generate_escalation_samples(n: int = 200, rng: np.random.Generator | None = None) -> np.ndarray:
    """Generate feature vectors for known 'escalation' regimes (label = 1)."""
    if rng is None:
        rng = np.random.default_rng(123)

    samples = np.column_stack([
        rng.normal(loc=2.5,  scale=1.0,  size=n),     # military_flight_surge  — big spike
        rng.uniform(low=0.15, high=0.45, size=n),     # tanker_refueler_ratio — high
        rng.normal(loc=1.5,  scale=0.6,  size=n),     # foot_traffic_anomaly  — late-night spike
        rng.normal(loc=5.0,  scale=1.5,  size=n),     # gdelt_negative_tone   — very negative
        rng.normal(loc=3.0,  scale=1.0,  size=n),     # gdelt_article_spike   — surge
        rng.normal(loc=2.0,  scale=0.8,  size=n),     # oil_price_z           — elevated
        rng.normal(loc=1.8,  scale=0.7,  size=n),     # defense_stock_z       — elevated
        rng.normal(loc=1.5,  scale=0.6,  size=n),     # gold_price_z          — elevated
    ])
    samples[:, 2] = np.clip(samples[:, 2], 0, None)
    return samples


def generate_training_data(
    n_normal: int = 800,
    n_escalation: int = 200,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Build the full synthetic training set.

    Returns
    -------
    X : np.ndarray of shape (n_normal + n_escalation, 8)
    y : np.ndarray of shape (n_normal + n_escalation,)
    """
    rng = np.random.default_rng(seed)

    X_normal = _generate_normal_samples(n_normal, rng)
    X_escal  = _generate_escalation_samples(n_escalation, rng)

    X = np.vstack([X_normal, X_escal])
    y = np.concatenate([
        np.zeros(n_normal, dtype=int),
        np.ones(n_escalation, dtype=int),
    ])

    # Shuffle
    idx = rng.permutation(len(y))
    return X[idx], y[idx]


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------
def train_and_save(model_dir: str | Path = "models",
                   n_normal: int = 800,
                   n_escalation: int = 200) -> None:
    """Train the Random Forest + Scaler and persist to disk."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score
    import joblib

    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    print("[train_model] Generating synthetic training data …")
    X, y = generate_training_data(n_normal=n_normal, n_escalation=n_escalation)
    print(f"  Samples: {len(y)}  |  Normal: {(y==0).sum()}  |  Escalation: {(y==1).sum()}")

    # Scale
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_split=10,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.feature_names_in_ = np.array(FEATURE_NAMES)

    print("[train_model] Training Random Forest …")
    model.fit(X_scaled, y)

    # Quick cross-validation
    scores = cross_val_score(model, X_scaled, y, cv=5, scoring="accuracy")
    print(f"  5-fold CV accuracy: {scores.mean():.3f} ± {scores.std():.3f}")

    # Feature importances
    print("  Feature importances:")
    for name, imp in sorted(zip(FEATURE_NAMES, model.feature_importances_),
                            key=lambda x: -x[1]):
        bar = "█" * int(imp * 40)
        print(f"    {name:25s}  {imp:.4f}  {bar}")

    # Save
    model_path  = model_dir / "random_forest_v1.pkl"
    scaler_path = model_dir / "scaler.pkl"
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    print(f"\n[train_model] Saved model  → {model_path}")
    print(f"[train_model] Saved scaler → {scaler_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    train_and_save()
