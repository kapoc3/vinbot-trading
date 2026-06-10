"""
Tests for ML features.
"""
import pytest
from unittest.mock import patch, MagicMock
import numpy as np


class TestFeatureEngineering:
    """Tests for feature extraction."""

    def test_extract_features_length(self):
        """Test feature extraction returns correct number of features."""
        from app.services.ml.feature_engineering import extract_features

        closes = [100 + i * 0.5 for i in range(50)]
        features = extract_features(closes)

        assert features is not None
        assert len(features) >= 15

    def test_extract_features_with_insufficient_data(self):
        """Test with insufficient data returns None."""
        from app.services.ml.feature_engineering import extract_features

        closes = [100, 101, 102]
        features = extract_features(closes)

        assert features is None

    def test_extract_features_keys(self):
        """Test extracted features have expected keys."""
        from app.services.ml.feature_engineering import extract_features

        closes = [100 + i * 0.5 for i in range(60)]
        features = extract_features(closes)

        expected_keys = ["rsi_14", "ema_21", "macd_line", "bb_position", "atr_normalized"]
        for key in expected_keys:
            assert key in features


class TestEnsemble:
    """Tests for ensemble combination."""

    @patch("app.services.ml.ensemble.settings")
    def test_ensemble_agree_buy(self, mock_settings):
        """Test when ML and strategy agree on BUY."""
        mock_settings.ML_ENABLED = True
        from app.services.ml.ensemble import ensemble_predict

        signal, mult = ensemble_predict("BTCUSDT", "BUY", {}, "BUY", 0.7)

        assert signal == "BUY"
        assert mult == 1.0

    @patch("app.services.ml.ensemble.settings")
    def test_ensemble_agree_sell(self, mock_settings):
        """Test when ML and strategy agree on SELL."""
        mock_settings.ML_ENABLED = True
        from app.services.ml.ensemble import ensemble_predict

        signal, mult = ensemble_predict("BTCUSDT", "SELL", {}, "SELL", 0.85)

        assert signal == "SELL"
        assert mult == 1.2

    @patch("app.services.ml.ensemble.settings")
    def test_ensemble_disagree_high_confidence(self, mock_settings):
        """Test ML overrides with high confidence."""
        mock_settings.ML_ENABLED = True
        from app.services.ml.ensemble import ensemble_predict

        signal, mult = ensemble_predict("BTCUSDT", "BUY", {}, "SELL", 0.8)

        assert signal == "SELL"
        assert mult == 1.0

    @patch("app.services.ml.ensemble.settings")
    def test_ensemble_disagree_low_confidence(self, mock_settings):
        """Test strategy overrides with low ML confidence."""
        mock_settings.ML_ENABLED = True
        from app.services.ml.ensemble import ensemble_predict

        signal, mult = ensemble_predict("BTCUSDT", "BUY", {}, "SELL", 0.4)

        assert signal == "BUY"
        assert mult == 0.8

    @patch("app.services.ml.ensemble.settings")
    def test_ensemble_ml_hold(self, mock_settings):
        """Test when ML says HOLD."""
        mock_settings.ML_ENABLED = True
        from app.services.ml.ensemble import ensemble_predict

        signal, mult = ensemble_predict("BTCUSDT", "BUY", {}, "HOLD", 0.6)

        assert signal == "BUY"
        assert mult == 0.6

    def test_ensemble_disabled(self):
        """Test when ML is disabled (no ML signal)."""
        from app.services.ml.ensemble import ensemble_predict

        signal, mult = ensemble_predict("BTCUSDT", "BUY", {}, None, 0.0)

        assert signal == "BUY"
        assert mult == 1.0


class TestMLConfig:
    """Tests for ML configuration."""

    def test_ml_config_defaults(self):
        """Test ML config has correct defaults."""
        from app.core.config import get_settings

        settings = get_settings()

        assert settings.ML_ENABLED is False
        assert settings.ML_MODEL_PATH == "data/ml_models"
        assert settings.ML_CONFIDENCE_THRESHOLD == 0.5


class TestMLPredictor:
    """Tests for ML predictor."""

    @patch("app.services.ml.predictor.ModelTrainer")
    def test_predict_disabled(self, mock_trainer):
        """Test predictor returns None when disabled."""
        from app.services.ml.predictor import MLPredictor
        from app.core.config import get_settings

        settings = get_settings()
        original_enabled = settings.ML_ENABLED

        try:
            settings.ML_ENABLED = False
            predictor = MLPredictor()

            result = predictor.predict("BTCUSDT", {"rsi": 30, "ema": 100})
            assert result is None
        finally:
            settings.ML_ENABLED = original_enabled


if __name__ == "__main__":
    pytest.main([__file__, "-v"])