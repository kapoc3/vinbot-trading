"""
ML Predictor for real-time signals.
"""
import logging
from typing import Optional, Tuple, Dict, Any

import numpy as np

from app.core.config import get_settings
from app.services.ml.trainer import ModelTrainer

logger = logging.getLogger(__name__)
settings = get_settings()


class MLPredictor:
    """Real-time ML prediction."""

    def __init__(self):
        self.model_path = settings.ML_MODEL_PATH
        self.enabled = settings.ML_ENABLED
        self.confidence_threshold = settings.ML_CONFIDENCE_THRESHOLD

        # Cache for models
        self.models: Dict[str, Dict[str, Any]] = {}

        # Prediction cache
        self._prediction_cache: Dict[str, Tuple[str, float, int]] = {}
        self._last_candle: Dict[str, int] = {}

    def _load_model(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Load model for symbol (with caching)."""
        if symbol in self.models:
            return self.models[symbol]

        trainer = ModelTrainer(self.model_path)
        model_data = trainer.load_model(symbol)

        if model_data:
            self.models[symbol] = model_data
            logger.info(f"Loaded ML model for {symbol}")
        else:
            logger.warning(f"No ML model found for {symbol}")

        return model_data

    def predict(self, symbol: str, features: Dict[str, float]) -> Optional[str]:
        """Predict signal from features."""
        if not self.enabled:
            return None

        result = self.predict_with_proba(symbol, features)
        if result is None:
            return None

        signal, confidence = result

        # Apply confidence threshold
        if confidence < self.confidence_threshold:
            return None

        return signal

    def predict_with_proba(self, symbol: str, features: Dict[str, float]) -> Optional[Tuple[str, float]]:
        """Predict with confidence score."""
        if not self.enabled:
            return None

        # Load model if not cached
        model_data = self._load_model(symbol)
        if model_data is None:
            return None

        try:
            model = model_data["model"]
            scaler = model_data["scaler"]
            feature_names = model_data["feature_names"]
            label_map = model_data["label_map"]

            # Prepare features
            X = np.array([[features.get(f, 0) for f in feature_names]])
            X_scaled = scaler.transform(X)

            # Predict
            prediction = model.predict(X_scaled)[0]
            probabilities = model.predict_proba(X_scaled)[0]

            # Map back to labels
            reverse_map = {v: k for k, v in label_map.items()}
            signal = reverse_map.get(prediction, "HOLD")

            # Get confidence (probability of predicted class)
            confidence = float(probabilities[prediction])

            logger.debug(f"ML Prediction for {symbol}: {signal} (confidence: {confidence:.2f})")

            return signal, confidence

        except Exception as e:
            logger.error(f"Prediction error for {symbol}: {e}")
            return None


# Global predictor instance
ml_predictor = MLPredictor()


def get_prediction(symbol: str, features: Dict[str, float]) -> Optional[str]:
    """Convenience function to get ML prediction."""
    return ml_predictor.predict(symbol, features)


def get_prediction_with_confidence(symbol: str, features: Dict[str, float]) -> Optional[Tuple[str, float]]:
    """Convenience function to get ML prediction with confidence."""
    return ml_predictor.predict_with_proba(symbol, features)