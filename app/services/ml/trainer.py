"""
Model training for ML signals.
"""
import logging
import os
import pickle
from typing import Optional, Dict, Any, Tuple, List

import numpy as np

logger = logging.getLogger(__name__)

# Try importing sklearn, if not available use fallback
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import cross_val_score
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("sklearn not available - ML features will use fallback")


class ModelTrainer:
    """Train and save ML models."""

    def __init__(self, model_path: str = "data/ml_models"):
        self.model_path = model_path
        os.makedirs(model_path, exist_ok=True)

    def train(
        self,
        X: List[Dict[str, float]],
        y: List[str],
        symbol: str
    ) -> Optional[Any]:
        """Train a Random Forest model."""
        if not SKLEARN_AVAILABLE:
            logger.warning("sklearn not available, cannot train model")
            return None

        try:
            # Convert to numpy arrays
            feature_names = list(X[0].keys()) if X else []
            X_array = np.array([[row[f] for f in feature_names] for row in X])

            # Encode labels
            label_map = {"BUY": 0, "HOLD": 1, "SELL": 2}
            y_array = np.array([label_map[lbl] for lbl in y])

            # Filter out HOLD for binary classification (simpler)
            # For now, use all 3 classes

            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_array)

            # Train model
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=20,
                random_state=42,
                n_jobs=-1
            )

            # Cross validation
            cv_scores = cross_val_score(model, X_scaled, y_array, cv=5)
            logger.info(f"CV Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

            # Fit final model
            model.fit(X_scaled, y_array)

            # Save model and scaler
            model_data = {
                "model": model,
                "scaler": scaler,
                "feature_names": feature_names,
                "label_map": label_map
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