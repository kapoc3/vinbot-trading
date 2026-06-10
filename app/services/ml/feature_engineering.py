"""
Feature Engineering for ML models.
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class FeatureEngine:
    """Extract technical features for ML models."""

    @staticmethod
    def extract_features(klines: List[Any]) -> Optional[Dict[str, float]]:
        """Extract features from a list of klines or closes."""
        if len(klines) < 50:
            return None

        try:
            # Handle both kline objects and simple price lists
            first = klines[0]
            if hasattr(first, 'close'):
                closes = np.array([k.close for k in klines])
                highs = np.array([k.high for k in klines])
                lows = np.array([k.low for k in klines])
                volumes = np.array([getattr(k, 'volume', 1) for k in klines])
            else:
                closes = np.array(klines, dtype=float)
                highs = closes * 1.01
                lows = closes * 0.99
                volumes = np.ones(len(closes))

            features = {}

            # RSI (3 periods)
            features['rsi_7'] = FeatureEngine._calc_rsi(closes, 7) or 50.0
            features['rsi_14'] = FeatureEngine._calc_rsi(closes, 14) or 50.0
            features['rsi_21'] = FeatureEngine._calc_rsi(closes, 21) or 50.0

            # EMA (3 periods)
            features['ema_9'] = FeatureEngine._calc_ema(closes, 9) or closes[-1]
            features['ema_21'] = FeatureEngine._calc_ema(closes, 21) or closes[-1]
            features['ema_50'] = FeatureEngine._calc_ema(closes, 50) or closes[-1]

            # MACD
            ema_12 = FeatureEngine._calc_ema(closes, 12)
            ema_26 = FeatureEngine._calc_ema(closes, 26)
            if ema_12 and ema_26:
                macd_line = ema_12 - ema_26
                features['macd_line'] = macd_line
                features['macd_signal'] = FeatureEngine._calc_ema(closes, 9) or macd_line
                features['macd_hist'] = macd_line - features['macd_signal']
            else:
                features['macd_line'] = 0.0
                features['macd_signal'] = 0.0
                features['macd_hist'] = 0.0

            # Bollinger Bands position
            sma_20 = np.mean(closes[-20:]) if len(closes) >= 20 else closes[-1]
            std_20 = np.std(closes[-20:]) if len(closes) >= 20 else 0
            upper = sma_20 + 2 * std_20
            lower = sma_20 - 2 * std_20
            if upper > lower:
                bb_position = (closes[-1] - lower) / (upper - lower) * 100
                features['bb_position'] = bb_position
            else:
                features['bb_position'] = 50.0

            # ATR normalized
            atr = FeatureEngine._calc_atr(highs, lows, closes, 14)
            features['atr_normalized'] = (atr / closes[-1] * 100) if atr and closes[-1] > 0 else 0

            # Volume ratio
            avg_volume = np.mean(volumes[-20:]) if len(volumes) >= 20 else 1
            features['volume_ratio'] = volumes[-1] / avg_volume if avg_volume > 0 else 1

            # Returns
            features['return_1d'] = ((closes[-1] - closes[-2]) / closes[-2] * 100) if len(closes) >= 2 else 0
            features['return_3d'] = ((closes[-1] - closes[-4]) / closes[-4] * 100) if len(closes) >= 4 else 0
            features['return_7d'] = ((closes[-1] - closes[-8]) / closes[-8] * 100) if len(closes) >= 8 else 0

            # Price ratios
            features['high_low_ratio'] = (highs[-1] - lows[-1]) / closes[-1] * 100 if closes[-1] > 0 else 0
            features['close_open_ratio'] = (closes[-1] - closes[0]) / closes[0] * 100 if closes[0] > 0 else 0

            return features

        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            return None

    @staticmethod
    def _calc_rsi(closes: np.array, period: int) -> Optional[float]:
        """Calculate RSI."""
        if len(closes) < period + 1:
            return None

        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def _calc_ema(closes: np.array, period: int) -> Optional[float]:
        """Calculate EMA."""
        if len(closes) < period:
            return None

        multiplier = 2 / (period + 1)
        ema = closes[0]

        for price in closes[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    @staticmethod
    def _calc_atr(highs: np.array, lows: np.array, closes: np.array, period: int) -> Optional[float]:
        """Calculate ATR."""
        if len(highs) < period + 1:
            return None

        true_ranges = []
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            true_ranges.append(tr)

        return np.mean(true_ranges[-period:])


def extract_features(klines: List[Any]) -> Optional[Dict[str, float]]:
    """Convenience function to extract features."""
    return FeatureEngine.extract_features(klines)


def generate_labels(klines: List[Any], threshold: float = 2.0, horizon: int = 10) -> Optional[str]:
    """Generate label for current candle based on future returns.

    Returns: "BUY", "SELL", or "HOLD"
    """
    if len(klines) < horizon + 1:
        return None

    current_price = klines[-horizon-1].close
    future_price = klines[-1].close

    return_pct = ((future_price - current_price) / current_price) * 100

    if return_pct > threshold:
        return "BUY"
    elif return_pct < -threshold:
        return "SELL"
    else:
        return "HOLD"