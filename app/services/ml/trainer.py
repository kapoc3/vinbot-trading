"""
Model training for ML signals with leakage-free walk-forward validation.
"""
import logging
import os
import pickle
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple, List

import numpy as np

logger = logging.getLogger(__name__)

# Try importing sklearn, if not available use fallback
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("sklearn not available - ML features will use fallback")


class ModelTrainer:
    """Train and save ML models using purged walk-forward TimeSeriesSplit."""

    def __init__(self, model_path: str = "data/ml_models"):
        self.model_path = model_path
        os.makedirs(model_path, exist_ok=True)

    def train(
        self,
        X: List[Dict[str, float]],
        y: List[str],
        symbol: str,
        embargo_bars: int = 10,
        n_splits: int = 5
    ) -> Optional[Dict[str, Any]]:
        """Train a Random Forest model without look-ahead bias or data leakage."""
        if not SKLEARN_AVAILABLE:
            logger.warning("sklearn not available, cannot train model")
            return None

        if not X or not y or len(X) != len(y):
            logger.warning("Invalid training dataset dimensions")
            return None

        try:
            # Convert to numpy arrays preserving deterministic feature ordering
            feature_names = list(X[0].keys())
            X_array = np.array([[row.get(f, 0.0) for f in feature_names] for row in X], dtype=float)

            # Encode labels
            label_map = {"BUY": 0, "HOLD": 1, "SELL": 2}
            y_array = np.array([label_map.get(lbl, 1) for lbl in y], dtype=int)

            n_samples = len(X_array)
            cv_scores: List[float] = []

            # Purged Walk-Forward Cross-Validation (scaler fit strictly inside each train fold)
            effective_gap = embargo_bars if n_samples > (n_splits + 1) * (embargo_bars + 5) else 0
            effective_splits = min(n_splits, max(2, (n_samples // 15) - 1))

            if n_samples >= 30 and effective_splits >= 2:
                tscv = TimeSeriesSplit(n_splits=effective_splits, gap=effective_gap)
                for train_idx, val_idx in tscv.split(X_array):
                    fold_scaler = StandardScaler()
                    X_train_scaled = fold_scaler.fit_transform(X_array[train_idx])
                    X_val_scaled = fold_scaler.transform(X_array[val_idx])

                    fold_model = RandomForestClassifier(
                        n_estimators=100,
                        max_depth=10,
                        min_samples_split=20,
                        class_weight="balanced_subsample",
                        random_state=42,
                        n_jobs=-1
                    )
                    fold_model.fit(X_train_scaled, y_array[train_idx])
                    score = float(fold_model.score(X_val_scaled, y_array[val_idx]))
                    cv_scores.append(score)

            cv_mean = float(np.mean(cv_scores)) if cv_scores else 0.0
            cv_std = float(np.std(cv_scores)) if cv_scores else 0.0
            logger.info(
                f"Purged Walk-Forward CV Accuracy ({symbol}): {cv_mean:.3f} (+/- {cv_std:.3f}) "
                f"[splits={len(cv_scores)}, embargo={effective_gap}]"
            )

            # Fit final scaler and model on full historical window for live deployment
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_array)

            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=20,
                class_weight="balanced_subsample",
                random_state=42,
                n_jobs=-1
            )
            model.fit(X_scaled, y_array)

            # Save model, scaler, and audit metadata
            model_data = {
                "model": model,
                "scaler": scaler,
                "feature_names": feature_names,
                "label_map": label_map,
                "cv_mean": cv_mean,
                "cv_std": cv_std,
                "embargo_bars": effective_gap,
                "n_samples": n_samples,
                "trained_at": datetime.now(timezone.utc).isoformat()
            }

            model_file = os.path.join(self.model_path, f"{symbol}_model.pkl")
            with open(model_file, "wb") as f:
                pickle.dump(model_data, f)

            logger.info(f"Model saved to {model_file}")
            return model_data

        except Exception as e:
            logger.error(f"Training error: {e}")
            return None

    def load_model(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Load trained model."""
        model_file = os.path.join(self.model_path, f"{symbol}_model.pkl")

        if not os.path.exists(model_file):
            return None

        try:
            with open(model_file, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return None


def train_model(
    X: List[Dict[str, float]],
    y: List[str],
    symbol: str,
    model_path: str = "data/ml_models"
) -> bool:
    """Convenience function to train and save model."""
    trainer = ModelTrainer(model_path)
    result = trainer.train(X, y, symbol)
    return result is not None