import logging
from enum import Enum
from typing import Dict, Optional
from app.services.indicators import get_symbol_data
from app.core.metrics import trading_market_regime

logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    RANGING = "Ranging"
    TRENDING = "Trending"
    HIGH_VOLATILITY = "HighVolatility"
    UNKNOWN = "Unknown"

class RegimeService:
    def __init__(self):
        self.current_regimes: Dict[str, MarketRegime] = {}
        # Thresholds
        self.ADX_TREND_THRESHOLD = 25.0
        self.ADX_RANGE_THRESHOLD = 20.0
        self.ATR_VOLATILITY_FACTOR = 2.0 # Current ATR > 2x average ATR

    def classify_regime(self, symbol: str) -> MarketRegime:
        """Analyze indicators and return the current market regime."""
        symbol_data = get_symbol_data(symbol)
        
        adx = symbol_data.get_adx()
        atr = symbol_data.get_atr()
        
        if adx is None or atr is None:
            return MarketRegime.UNKNOWN

        # 1. High Volatility Check
        # Compare current ATR to a longer-term average ATR (e.g. last 100 periods)
        # For simplicity, we compare to the first values in the ATR history if available
        # or just use a fixed threshold for now if baseline is unknown.
        # In a real bot, we'd maintain a 'baseline_atr'.
        
        # 2. Trend vs Range Check via ADX
        new_regime = MarketRegime.RANGING
        if adx > self.ADX_TREND_THRESHOLD:
            new_regime = MarketRegime.TRENDING
        elif adx < self.ADX_RANGE_THRESHOLD:
            new_regime = MarketRegime.RANGING
        else:
            # Hysteresis: keep old regime if in middle zone
            new_regime = self.current_regimes.get(symbol, MarketRegime.RANGING)

        # Detect change
        old_regime = self.current_regimes.get(symbol, MarketRegime.UNKNOWN)
        if new_regime != old_regime:
            logger.info(f"REGIME | {symbol} changed regime: {old_regime.value} -> {new_regime.value} (ADX: {adx:.2f})")
            self.current_regimes[symbol] = new_regime
            
            # Map enum to numeric gauge value
            regime_map = {
                MarketRegime.UNKNOWN: 0,
                MarketRegime.RANGING: 1,
                MarketRegime.TRENDING: 2,
                MarketRegime.HIGH_VOLATILITY: 3
            }
            trading_market_regime.labels(symbol=symbol).set(regime_map.get(new_regime, 0))
            
        return new_regime

regime_service = RegimeService()
