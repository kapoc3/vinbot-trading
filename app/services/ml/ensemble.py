"""
Ensemble combining ML predictions with traditional strategies.
"""
import logging
from typing import Optional, Tuple

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def ensemble_predict(
    symbol: str,
    strategy_signal: Optional[str],
    ml_features: dict,
    ml_signal: Optional[str] = None,
    ml_confidence: float = 0.0
) -> Tuple[Optional[str], float]:
    """
    Combine ML and traditional strategy signals.

    Returns:
        (final_signal, position_multiplier)
    """
    if not settings.ML_ENABLED or not ml_signal:
        # ML disabled or no prediction - use strategy only
        return strategy_signal, 1.0

    # ML available - evaluate combination
    has_live_probs = isinstance(ml_features, dict) and "_ml_sell_prob" in ml_features
    buy_prob = float(ml_features.get("_ml_buy_prob", 0.0)) if has_live_probs else 0.0
    sell_prob = float(ml_features.get("_ml_sell_prob", 0.0)) if has_live_probs else 0.0

    # Smart Veto: When live Triple-Barrier probabilities are present, veto BUY traps where SL is predicted first
    if has_live_probs and strategy_signal == "BUY":
        if ml_signal == "SELL" and ml_confidence >= 0.52:
            logger.info(
                f"ENSEMBLE VETO | {symbol}: Blocked BUY trap — ML predicts Stop-Loss barrier first "
                f"(P(SL)={sell_prob:.2f}, conf={ml_confidence:.2f})"
            )
            try:
                from app.core.metrics import trading_ml_vetoes_total
                trading_ml_vetoes_total.labels(symbol=symbol, reason="ml_sl_barrier").inc()
                ml_features["_vetoed_by"] = f"IA: P(SL)={sell_prob*100:.0f}%"
            except Exception:
                pass
            return None, 0.0
        if ml_signal == "HOLD" and sell_prob > 0.35 and sell_prob > buy_prob * 1.4:
            logger.info(
                f"ENSEMBLE VETO | {symbol}: Blocked low-edge BUY — P(SL)={sell_prob:.2f} >> P(TP)={buy_prob:.2f}"
            )
            try:
                from app.core.metrics import trading_ml_vetoes_total
                trading_ml_vetoes_total.labels(symbol=symbol, reason="ml_low_edge").inc()
                ml_features["_vetoed_by"] = f"IA: Bajo Edge P(SL)={sell_prob*100:.0f}%"
            except Exception:
                pass
            return None, 0.0

    # Case 1: ML says HOLD - check BEFORE disagree
    if ml_signal == "HOLD":
        logger.info(f"ENSEMBLE | {symbol}: ML says HOLD, following strategy with caution")
        if strategy_signal:
            return strategy_signal, 0.6
        return None, 0.0

    # Case 2: ML and strategy agree
    if ml_signal == strategy_signal:
        logger.info(f"ENSEMBLE | {symbol}: ML and strategy agree ({ml_signal})")
        if ml_confidence > 0.8:
            return ml_signal, 1.2
        elif ml_confidence > 0.6:
            return ml_signal, 1.0
        else:
            return ml_signal, 0.9

    # Case 3: ML and strategy disagree
    if ml_signal != strategy_signal:
        if ml_confidence > 0.7:
            logger.info(f"ENSEMBLE | {symbol}: ML overrides strategy (conf: {ml_confidence:.2f})")
            return ml_signal, 1.0

        if ml_confidence < 0.5:
            logger.info(f"ENSEMBLE | {symbol}: Strategy overrides ML (conf: {ml_confidence:.2f})")
            return strategy_signal, 0.8

        logger.info(f"ENSEMBLE | {symbol}: Conflict - using strategy with reduced position")
        return strategy_signal, 0.7

    return strategy_signal, 1.0