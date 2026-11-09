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
    def extract_features(klines: Any) -> Optional[Dict[str, float]]:
        """Extract stationary technical and microstructure features from SymbolData, kline objects, dicts, or closes."""
        try:
            # Handle SymbolData instance directly
            if hasattr(klines, 'closes') and hasattr(klines, 'highs'):
                closes = np.array(list(klines.closes), dtype=float)
                highs = np.array(list(klines.highs), dtype=float) if len(klines.highs) == len(closes) else closes * 1.01
                lows = np.array(list(klines.lows), dtype=float) if len(klines.lows) == len(closes) else closes * 0.99
                volumes = np.array(list(klines.volumes), dtype=float) if len(klines.volumes) == len(closes) else np.ones(len(closes))
            else:
                if len(klines) < 50:
                    return None
                first = klines[0]
                if hasattr(first, 'close'):
                    closes = np.array([k.close for k in klines], dtype=float)
                    highs = np.array([k.high for k in klines], dtype=float)
                    lows = np.array([k.low for k in klines], dtype=float)
                    volumes = np.array([getattr(k, 'volume', 1.0) for k in klines], dtype=float)
                elif isinstance(first, dict) and 'c' in first:
                    closes = np.array([float(k['c']) for k in klines], dtype=float)
                    highs = np.array([float(k.get('h', k['c'])) for k in klines], dtype=float)
                    lows = np.array([float(k.get('l', k['c'])) for k in klines], dtype=float)
                    volumes = np.array([float(k.get('v', 1.0)) for k in klines], dtype=float)
                else:
                    closes = np.array(klines, dtype=float)
                    highs = closes * 1.01
                    lows = closes * 0.99
                    volumes = np.ones(len(closes))

            if len(closes) < 50:
                return None

            current_close = closes[-1]
            if current_close <= 0:
                return None

            features: Dict[str, float] = {}

            # RSI (3 periods) - inherently stationary [0, 100]
            features['rsi_7'] = FeatureEngine._calc_rsi(closes, 7) or 50.0
            features['rsi_14'] = FeatureEngine._calc_rsi(closes, 14) or 50.0
            features['rsi_21'] = FeatureEngine._calc_rsi(closes, 21) or 50.0

            # EMA (3 periods) - normalized as % distance from current close for stationarity
            ema_9 = FeatureEngine._calc_ema(closes, 9) or current_close
            ema_21 = FeatureEngine._calc_ema(closes, 21) or current_close
            ema_50 = FeatureEngine._calc_ema(closes, 50) or current_close
            features['ema_9'] = (current_close - ema_9) / current_close * 100.0
            features['ema_21'] = (current_close - ema_21) / current_close * 100.0
            features['ema_50'] = (current_close - ema_50) / current_close * 100.0

            # MACD - computed over true MACD series and normalized by current_close
            ema_12_series = FeatureEngine._calc_ema_series(closes, 12)
            ema_26_series = FeatureEngine._calc_ema_series(closes, 26)
            if ema_12_series is not None and ema_26_series is not None:
                macd_series = ema_12_series - ema_26_series
                macd_line_raw = float(macd_series[-1])
                valid_macd = macd_series[25:] if len(macd_series) > 25 else macd_series
                macd_signal_raw = FeatureEngine._calc_ema(valid_macd, 9)
                if macd_signal_raw is None:
                    macd_signal_raw = macd_line_raw
                features['macd_line'] = (macd_line_raw / current_close) * 100.0
                features['macd_signal'] = (macd_signal_raw / current_close) * 100.0
                features['macd_hist'] = features['macd_line'] - features['macd_signal']
            else:
                features['macd_line'] = 0.0
                features['macd_signal'] = 0.0
                features['macd_hist'] = 0.0

            # Bollinger Bands position
            sma_20 = np.mean(closes[-20:]) if len(closes) >= 20 else current_close
            std_20 = np.std(closes[-20:]) if len(closes) >= 20 else 0.0
            upper = sma_20 + 2 * std_20
            lower = sma_20 - 2 * std_20
            if upper > lower:
                bb_position = (current_close - lower) / (upper - lower) * 100.0
                features['bb_position'] = float(bb_position)
            else:
                features['bb_position'] = 50.0

            # ATR normalized & Volatility Regime (short vs medium ATR)
            atr_14 = FeatureEngine._calc_atr(highs, lows, closes, 14)
            atr_7 = FeatureEngine._calc_atr(highs, lows, closes, 7)
            atr_21 = FeatureEngine._calc_atr(highs, lows, closes, 21)
            features['atr_normalized'] = (atr_14 / current_close * 100.0) if atr_14 else 0.0
            features['volatility_regime'] = (atr_7 / atr_21) if (atr_7 and atr_21 and atr_21 > 0) else 1.0

            # Volume ratio & OBV slope (microstructure accumulation/distribution)
            avg_volume = float(np.mean(volumes[-20:])) if len(volumes) >= 20 else 1.0
            features['volume_ratio'] = float(volumes[-1] / avg_volume) if avg_volume > 0 else 1.0

            price_changes = np.diff(closes[-11:])
            vol_window = volumes[-10:]
            signed_vol = np.where(price_changes > 0, vol_window, np.where(price_changes < 0, -vol_window, 0.0))
            features['obv_slope'] = float(np.sum(signed_vol) / (avg_volume * 10.0)) if avg_volume > 0 else 0.0

            # Returns
            features['return_1d'] = float((current_close - closes[-2]) / closes[-2] * 100.0) if len(closes) >= 2 and closes[-2] > 0 else 0.0
            features['return_3d'] = float((current_close - closes[-4]) / closes[-4] * 100.0) if len(closes) >= 4 and closes[-4] > 0 else 0.0
            features['return_7d'] = float((current_close - closes[-8]) / closes[-8] * 100.0) if len(closes) >= 8 and closes[-8] > 0 else 0.0

            # Price ratios (using rolling window start [-50] for stationarity)
            window_start_close = closes[-50]
            features['high_low_ratio'] = float((highs[-1] - lows[-1]) / current_close * 100.0)
            features['close_open_ratio'] = float((current_close - window_start_close) / window_start_close * 100.0) if window_start_close > 0 else 0.0

            # Microstructure & Momentum Acceleration (scale-invariant)
            features['rsi_slope'] = float(features['rsi_7'] - features['rsi_21'])
            candle_range = float(highs[-1] - lows[-1])
            features['buying_pressure_wick'] = float((current_close - lows[-1]) / candle_range * 100.0) if candle_range > 0 else 50.0
            vol_std = float(np.std(volumes[-20:])) if len(volumes) >= 20 else 0.0
            raw_vol_z = ( float(volumes[-1]) - avg_volume ) / vol_std if vol_std > 1e-9 else 0.0
            features['volume_zscore'] = float(np.clip(raw_vol_z, -5.0, 5.0))

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
        ema = float(closes[0])

        for price in closes[1:]:
            ema = (float(price) * multiplier) + (ema * (1 - multiplier))

        return ema

    @staticmethod
    def _calc_ema_series(closes: np.array, period: int) -> Optional[np.ndarray]:
        """Calculate full EMA series for MACD signal line calculation."""
        if len(closes) < period:
            return None

        multiplier = 2 / (period + 1)
        ema_series = np.zeros(len(closes), dtype=float)
        ema = float(closes[0])
        ema_series[0] = ema

        for i in range(1, len(closes)):
            ema = (float(closes[i]) * multiplier) + (ema * (1 - multiplier))
            ema_series[i] = ema

        return ema_series

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


def generate_triple_barrier_label(
    future_klines: List[Dict[str, float]],
    entry_price: float,
    tp_pct: float = 1.5,
    sl_pct: float = 1.0,
    fee_pct: float = 0.2,
) -> str:
    """
    Triple-Barrier Labeling (Lopez de Prado):
    Evaluates the forward path of candles to determine whether the Upper Barrier (Take Profit)
    or Lower Barrier (Stop Loss) is touched first, accounting for round-trip fees.
    Returns:
      - "BUY": Upper barrier (TP) hit first, or strong positive net return at vertical barrier.
      - "SELL": Lower barrier (SL) hit first (trap / losing trade to veto).
      - "HOLD": Neither barrier hit and net return within noise band.
    """
    if not future_klines or entry_price <= 0:
        return "HOLD"

    upper_barrier = entry_price * (1.0 + (tp_pct + fee_pct) / 100.0)
    lower_barrier = entry_price * (1.0 - sl_pct / 100.0)

    for k in future_klines:
        high_p = float(k.get("h", k.get("c", entry_price)))
        low_p = float(k.get("l", k.get("c", entry_price)))

        hit_sl = low_p <= lower_barrier
        hit_tp = high_p >= upper_barrier

        if hit_sl and hit_tp:
            # Conservative assumption when both touched in same bar
            return "SELL"
        if hit_sl:
            return "SELL"
        if hit_tp:
            return "BUY"

    # Vertical barrier (time expiration): check final net return after fees
    final_close = float(future_klines[-1].get("c", entry_price))
    net_ret_pct = ((final_close - entry_price) / entry_price) * 100.0 - fee_pct

    if net_ret_pct >= (tp_pct * 0.55):
        return "BUY"
    if net_ret_pct <= -(sl_pct * 0.55):
        return "SELL"
    return "HOLD"