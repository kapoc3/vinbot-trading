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