"""
ML Predictor for real-time signals and live forward-accuracy telemetry.
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any, List

import numpy as np

from app.core.config import get_settings
from app.core.metrics import (
    trading_ml_confidence,
    trading_ml_buy_prob,
    trading_ml_sell_prob,
    trading_ml_cv_accuracy,
    trading_ml_cv_buy_winrate,
    trading_ml_live_accuracy,
    trading_ml_live_evaluated_total,
    trading_ml_predictions_total,
)
from app.services.ml.trainer import ModelTrainer

logger = logging.getLogger(__name__)
settings = get_settings()


class MLPredictor:
    """Real-time ML prediction with live Triple-Barrier forward accuracy auditing."""

    def __init__(self):
        self.model_path = settings.ML_MODEL_PATH
        self.enabled = settings.ML_ENABLED
        self.confidence_threshold = settings.ML_CONFIDENCE_THRESHOLD

        # Cache for models
        self.models: Dict[str, Dict[str, Any]] = {}

        # Prediction cache & live telemetry state
        self._prediction_cache: Dict[str, Tuple[str, float, int]] = {}
        self._last_candle: Dict[str, int] = {}
        self.pending_verifications: Dict[str, List[Dict[str, Any]]] = {}
        self.live_stats: Dict[str, Dict[str, Any]] = {}

    def _load_model(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Load model for symbol (with caching)."""
        if symbol in self.models:
            return self.models[symbol]

        trainer = ModelTrainer(self.model_path)
        model_data = trainer.load_model(symbol)

        if model_data:
            self.models[symbol] = model_data
            cv_acc = float(model_data.get("cv_mean", 0.0))
            cv_buy = float(model_data.get("cv_buy_precision", cv_acc))
            trading_ml_cv_accuracy.labels(symbol=symbol).set(cv_acc)
            trading_ml_cv_buy_winrate.labels(symbol=symbol).set(cv_buy)
            logger.info(f"Loaded ML model for {symbol} (CV Acc: {cv_acc:.3f}, BUY WinRate: {cv_buy:.3f})")
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

            # Store class-specific probabilities inside features dict for downstream ensemble veto
            buy_idx = label_map.get("BUY", 0)
            hold_idx = label_map.get("HOLD", 1)
            sell_idx = label_map.get("SELL", 2 if "SELL" in label_map else 1)
            buy_prob = float(probabilities[buy_idx]) if len(probabilities) > buy_idx else 0.0
            hold_prob = float(probabilities[hold_idx]) if len(probabilities) > hold_idx else 0.0
            sell_prob = float(probabilities[sell_idx]) if len(probabilities) > sell_idx else 0.0

            if isinstance(features, dict):
                features["_ml_buy_prob"] = buy_prob
                features["_ml_hold_prob"] = hold_prob
                features["_ml_sell_prob"] = sell_prob

            trading_ml_confidence.labels(symbol=symbol).set(confidence)
            trading_ml_buy_prob.labels(symbol=symbol).set(buy_prob)
            trading_ml_sell_prob.labels(symbol=symbol).set(sell_prob)
            trading_ml_predictions_total.labels(symbol=symbol, signal=signal).inc()

            logger.debug(
                f"ML Prediction for {symbol}: {signal} "
                f"(conf: {confidence:.2f}, P(BUY): {buy_prob:.2f}, P(SELL): {sell_prob:.2f})"
            )

            return signal, confidence

        except Exception as e:
            logger.error(f"Prediction error for {symbol}: {e}")
            return None

    def record_and_verify_candle(
        self,
        symbol: str,
        close_price: float,
        high_price: float,
        low_price: float,
        features: Dict[str, float],
        obi: float = 0.0,
        vetoed: bool = False,
        veto_reason: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        1. Verify previous predictions against the new candle's high/low (Triple-Barrier forward audit).
        2. Run live prediction on the closed candle and persist telemetry for Web Dashboard + Grafana.
        """
        if not self.enabled or not features or close_price <= 0:
            return None

        stats = self.live_stats.setdefault(
            symbol,
            {
                "symbol": symbol,
                "evaluated": 0,
                "correct": 0,
                "live_accuracy": 0.0,
                "vetoes_total": 0,
                "vetoes_saved": 0,
                "recent_decisions": [],
            },
        )
        pending = self.pending_verifications.setdefault(symbol, [])

        # 1. Verify pending predictions against current candle high/low
        still_pending = []
        for item in pending:
            item["bars_elapsed"] += 1
            resolved_outcome = None
            if high_price >= item["tp_price"]:
                resolved_outcome = "BUY"
            elif low_price <= item["sl_price"]:
                resolved_outcome = "SELL"
            elif item["bars_elapsed"] >= item["horizon"]:
                resolved_outcome = "HOLD"

            if resolved_outcome is not None:
                pred_sig = item["predicted_signal"]
                # Evaluate whether the AI's directional assessment was accurate
                if pred_sig == "BUY":
                    is_correct = resolved_outcome == "BUY"
                elif pred_sig == "SELL":
                    # Predicting SELL (SL barrier / drop) is accurate if price hit SL or failed to rally to TP
                    is_correct = resolved_outcome in ("SELL", "HOLD")
                else:
                    is_correct = resolved_outcome == "HOLD"

                stats["evaluated"] += 1
                if is_correct:
                    stats["correct"] += 1
                    trading_ml_live_evaluated_total.labels(symbol=symbol, outcome="correct").inc()
                else:
                    trading_ml_live_evaluated_total.labels(symbol=symbol, outcome="incorrect").inc()

                if item.get("vetoed") and resolved_outcome in ("SELL", "HOLD"):
                    stats["vetoes_saved"] += 1

                stats["live_accuracy"] = round((stats["correct"] / stats["evaluated"]) * 100.0, 1)
                trading_ml_live_accuracy.labels(symbol=symbol).set(stats["correct"] / stats["evaluated"])

                # Update status in recent_decisions log
                for dec in stats["recent_decisions"]:
                    if dec.get("id") == item["id"]:
                        dec["verified"] = True
                        dec["actual_outcome"] = resolved_outcome
                        dec["is_correct"] = is_correct
                        dec["bars_elapsed"] = item["bars_elapsed"]
                        break
            else:
                for dec in stats["recent_decisions"]:
                    if dec.get("id") == item["id"]:
                        dec["bars_elapsed"] = item["bars_elapsed"]
                        dec["horizon"] = item["horizon"]
                        break
                still_pending.append(item)
        self.pending_verifications[symbol] = still_pending[-60:]

        # 2. Run live prediction for current candle
        res = self.predict_with_proba(symbol, features)
        if res is None:
            return None
        signal, confidence = res
        model_data = self.models.get(symbol, {})

        buy_prob = round(float(features.get("_ml_buy_prob", 0.0)) * 100.0, 1)
        hold_prob = round(float(features.get("_ml_hold_prob", 0.0)) * 100.0, 1)
        sell_prob = round(float(features.get("_ml_sell_prob", 0.0)) * 100.0, 1)

        if vetoed:
            stats["vetoes_total"] += 1

        tp_pct = min(settings.TAKE_PROFIT_PCT, 0.50) / 100.0
        sl_pct = min(settings.STOP_LOSS_PCT, 0.40) / 100.0
        horizon = 10
        now_iso = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self._seq_counter = getattr(self, "_seq_counter", 0) + 1
        pred_id = f"{symbol}_{int(datetime.now(timezone.utc).timestamp() * 1000)}_{self._seq_counter}"

        self.pending_verifications[symbol].append(
            {
                "id": pred_id,
                "predicted_signal": signal,
                "entry_price": close_price,
                "tp_price": close_price * (1.0 + tp_pct),
                "sl_price": close_price * (1.0 - sl_pct),
                "bars_elapsed": 0,
                "horizon": horizon,
                "vetoed": vetoed,
            }
        )

        decision_entry = {
            "id": pred_id,
            "time": now_iso,
            "symbol": symbol,
            "price": round(close_price, 4),
            "signal": signal,
            "confidence": round(confidence * 100.0, 1),
            "buy_prob": buy_prob,
            "sell_prob": sell_prob,
            "obi": round(obi, 2),
            "vetoed": vetoed,
            "veto_reason": veto_reason or "",
            "verified": False,
            "actual_outcome": "PENDIENTE",
            "is_correct": None,
            "bars_elapsed": 0,
            "horizon": horizon,
        }
        stats["recent_decisions"].insert(0, decision_entry)
        stats["recent_decisions"] = stats["recent_decisions"][:60]

        # Include newest 2 live pending decisions + up to 8 most recent verified decisions
        pending_decs = [d for d in stats["recent_decisions"] if not d.get("verified")][:2]
        verified_decs = [d for d in stats["recent_decisions"] if d.get("verified")][:8]
        display_decisions = pending_decs + verified_decs

        snapshot = {
            "symbol": symbol,
            "model_type": model_data.get("model_type", "VotingEnsemble"),
            "trained_at": model_data.get("trained_at", ""),
            "n_samples": model_data.get("n_samples", 0),
            "cv_accuracy": round(float(model_data.get("cv_mean", 0.0)) * 100.0, 1),
            "cv_buy_winrate": round(float(model_data.get("cv_buy_precision", 0.0)) * 100.0, 1),
            "live_evaluated": stats["evaluated"],
            "live_correct": stats["correct"],
            "live_accuracy": stats["live_accuracy"],
            "vetoes_total": stats["vetoes_total"],
            "vetoes_saved": stats["vetoes_saved"],
            "latest_signal": signal,
            "latest_confidence": round(confidence * 100.0, 1),
            "buy_prob": buy_prob,
            "hold_prob": hold_prob,
            "sell_prob": sell_prob,
            "obi": round(obi, 3),
            "rsi_slope": round(float(features.get("rsi_slope", 0.0)), 2),
            "buying_pressure_wick": round(float(features.get("buying_pressure_wick", 50.0)), 1),
            "volume_zscore": round(float(features.get("volume_zscore", 0.0)), 2),
            "updated_at": now_iso,
            "recent_decisions": display_decisions,
        }
        stats["snapshot"] = snapshot

        # Persist shared JSON so the web dashboard can display all symbols across containers
        try:
            os.makedirs(self.model_path, exist_ok=True)
            telemetry_file = os.path.join(self.model_path, f"{symbol}_telemetry.json")
            with open(telemetry_file, "w", encoding="utf-8") as f:
                json.dump(snapshot, f)
        except Exception as e:
            logger.debug(f"Could not write ML telemetry for {symbol}: {e}")

        return snapshot


# Global predictor instance
ml_predictor = MLPredictor()


def get_prediction(symbol: str, features: Dict[str, float]) -> Optional[str]:
    """Convenience function to get ML prediction."""
    return ml_predictor.predict(symbol, features)


def get_prediction_with_confidence(symbol: str, features: Dict[str, float]) -> Optional[Tuple[str, float]]:
    """Convenience function to get ML prediction with confidence."""
    return ml_predictor.predict_with_proba(symbol, features)