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

        expected_keys = [
            "rsi_14", "ema_21", "macd_line", "macd_signal", "macd_hist",
            "bb_position", "atr_normalized", "volatility_regime", "obv_slope"
        ]
        for key in expected_keys:
            assert key in features

    def test_extract_features_scale_invariance_stationarity(self):
        """Features must be stationary and invariant to price level scaling (e.g., 100 vs 100,000)."""
        from app.services.ml.feature_engineering import extract_features

        base_closes = [100.0 * (1.002 ** i) for i in range(60)]
        scaled_closes = [p * 1000.0 for p in base_closes]

        f_base = extract_features(base_closes)
        f_scaled = extract_features(scaled_closes)

        assert f_base is not None and f_scaled is not None
        for key in f_base:
            assert np.isclose(f_base[key], f_scaled[key], rtol=1e-5, atol=1e-6), f"Feature {key} is non-stationary"

    def test_macd_signal_is_not_raw_price(self):
        """Verify MACD signal and histogram are bounded percentage values, not raw close prices."""
        from app.services.ml.feature_engineering import extract_features

        closes = [60000.0 + np.sin(i / 3.0) * 500.0 for i in range(60)]
        features = extract_features(closes)

        assert features is not None
        assert abs(features["macd_line"]) < 10.0
        assert abs(features["macd_signal"]) < 10.0
        assert abs(features["macd_hist"]) < 10.0

    def test_extract_features_from_symbol_data(self):
        """Verify extract_features uses real OHLCV from SymbolData without faking volume_ratio=1.0."""
        from app.services.indicators import SymbolData
        from app.services.ml.feature_engineering import extract_features

        sd = SymbolData()
        for i in range(55):
            vol = 500.0 if i == 54 else 100.0
            sd.add_kline({"c": 1000 + i * 2, "h": 1005 + i * 2, "l": 995 + i * 2, "v": vol})

        features = extract_features(sd)
        assert features is not None
        assert features["volume_ratio"] > 2.5
        assert "rsi_slope" in features
        assert "buying_pressure_wick" in features
        assert "volume_zscore" in features

    def test_triple_barrier_labeling(self):
        """Verify Triple-Barrier labeling returns BUY when TP hits first and SELL when SL hits first."""
        from app.services.ml.feature_engineering import generate_triple_barrier_label

        # Scenario 1: Price hits TP (+1.0%) before SL (-0.6%)
        klines_tp = [
            {"c": 100.2, "h": 100.4, "l": 99.8, "v": 10},
            {"c": 101.1, "h": 101.2, "l": 100.1, "v": 15},
        ]
        assert generate_triple_barrier_label(klines_tp, entry_price=100.0, tp_pct=0.8, sl_pct=0.6, fee_pct=0.1) == "BUY"

        # Scenario 2: Price hits SL (-0.6%) before TP
        klines_sl = [
            {"c": 99.3, "h": 100.1, "l": 99.2, "v": 20},
            {"c": 101.5, "h": 101.6, "l": 99.3, "v": 25},
        ]
        assert generate_triple_barrier_label(klines_sl, entry_price=100.0, tp_pct=0.8, sl_pct=0.6, fee_pct=0.1) == "SELL"

        # Scenario 3: Price stays sideways inside barriers -> HOLD
        klines_hold = [
            {"c": 100.1, "h": 100.3, "l": 99.7, "v": 10},
            {"c": 100.0, "h": 100.2, "l": 99.8, "v": 10},
        ]
        assert generate_triple_barrier_label(klines_hold, entry_price=100.0, tp_pct=0.8, sl_pct=0.6, fee_pct=0.1) == "HOLD"


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

    @patch("app.services.ml.ensemble.settings")
    def test_ensemble_smart_veto_buy_trap(self, mock_settings):
        """When live Triple-Barrier probabilities predict SL first, ensemble vetoes a BUY trap."""
        mock_settings.ML_ENABLED = True
        from app.services.ml.ensemble import ensemble_predict

        live_feats = {"_ml_buy_prob": 0.18, "_ml_sell_prob": 0.62}
        signal, mult = ensemble_predict("BTCUSDC", "BUY", live_feats, "SELL", 0.62)

        assert signal is None
        assert mult == 0.0


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

    def test_walk_forward_trainer_metadata(self, tmp_path):
        """Test ModelTrainer uses Purged Walk-Forward TimeSeriesSplit and stores CV metadata."""
        from app.services.ml.trainer import ModelTrainer

        trainer = ModelTrainer(model_path=str(tmp_path))
        rng = np.random.default_rng(42)
        X = [{"rsi_14": float(rng.uniform(20, 80)), "ema_21": float(rng.normal(0, 1))} for _ in range(120)]
        y = ["BUY" if row["rsi_14"] < 35 else ("SELL" if row["rsi_14"] > 65 else "HOLD") for row in X]

        model_data = trainer.train(X, y, "BTCUSDT", embargo_bars=5, n_splits=3)
        assert model_data is not None
        assert "cv_mean" in model_data
        assert "embargo_bars" in model_data
        assert model_data["embargo_bars"] == 5
        assert model_data["n_samples"] == 120

    def test_risk_manager_conviction_multiplier(self):
        """Verify RiskManager scales position size by conviction multiplier."""
        from app.services.risk_manager import risk_manager

        base_qty = risk_manager.calculate_position_size("BTCUSDT", 50000.0, 49000.0, position_multiplier=1.0)
        boosted_qty = risk_manager.calculate_position_size("BTCUSDT", 50000.0, 49000.0, position_multiplier=1.2)
        reduced_qty = risk_manager.calculate_position_size("BTCUSDT", 50000.0, 49000.0, position_multiplier=0.5)

        assert np.isclose(boosted_qty, base_qty * 1.2)
        assert np.isclose(reduced_qty, base_qty * 0.5)


class TestSmartProxyRouting:
    """Tests for Smart Split-Routing and Static Proxy Failover."""

    def test_split_routing_policy_and_masking(self):
        """Public requests route direct when BINANCE_PROXY_SIGNED_ONLY=True; signed route via static proxy."""
        from app.services.binance_client import BinanceClient, _mask_proxy_url

        proxies = [
            "http://user:secret@64.137.19.153:5803",
            "http://user:secret@64.137.96.74:6641",
            "http://user:secret@84.247.60.125:6095",
        ]
        client = BinanceClient(proxy_urls=proxies)

        assert _mask_proxy_url(proxies[0]) == "http://***@64.137.19.153:5803"
        assert client._should_use_proxy(signed=False) is False
        assert client._should_use_proxy(signed=True) is True

    @pytest.mark.anyio
    async def test_proxy_failover_rotation_on_transport_error(self):
        """When primary proxy (Frankfurt) fails, BinanceClient automatically fails over to secondary (Madrid)."""
        import httpx
        from unittest.mock import AsyncMock
        from app.services.binance_client import BinanceClient

        proxies = [
            "http://user:secret@64.137.19.153:5803",
            "http://user:secret@64.137.96.74:6641",
        ]
        client = BinanceClient(proxy_urls=proxies)

        mock_client_1 = MagicMock()
        mock_client_1.request = AsyncMock(side_effect=httpx.ConnectError("Proxy 1 down"))

        mock_response_2 = MagicMock()
        mock_response_2.status_code = 200
        mock_response_2.raise_for_status = MagicMock()
        mock_response_2.json = MagicMock(return_value={"orderId": 999, "status": "FILLED"})

        mock_client_2 = MagicMock()
        mock_client_2.request = AsyncMock(return_value=mock_response_2)

        client._proxy_clients[proxies[0]] = mock_client_1
        client._proxy_clients[proxies[1]] = mock_client_2

        res = await client.request("POST", "/v3/order", params={"symbol": "BTCUSDT"}, signed=True)
        assert res["orderId"] == 999
        assert client._active_proxy_idx == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])