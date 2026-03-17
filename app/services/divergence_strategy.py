import logging
from typing import Dict, Any, Optional, List
from app.services.indicators import get_symbol_data
from app.services.risk_manager import risk_manager
from app.services.persistence import persistence

logger = logging.getLogger(__name__)

class RsiDivergenceStrategy:
    """Strategy that combines RSI levels with Regular Divergence detection."""
    def __init__(self, rsi_period: int = 14, overbought: float = 70.0, oversold: float = 30.0, pivot_length: int = 5):
        self.rsi_period = rsi_period
        self.overbought = overbought
        self.oversold = oversold
        self.pivot_length = pivot_length
        self.positions: Dict[str, bool] = {}

    async def load_initial_state(self, symbols: List[str]):
        """Load initial position state from persistence."""
        for symbol in symbols:
            key = f"{symbol.lower()}_in_position"
            stored_pos = await persistence.get_state(key, False)
            self.positions[symbol] = stored_pos

    def analyze(self, symbol: str) -> Optional[str]:
        """
        Analyze RSI and Divergence.
        BUY: RSI < oversold AND bullish_divergence
        SELL: RSI > overbought AND bearish_divergence
        """
        symbol_data = get_symbol_data(symbol)
        rsi = symbol_data.get_rsi(self.rsi_period)
        divergence = symbol_data.get_divergence(self.pivot_length)
        
        if rsi is None:
            return None
            
        current_in_position = self.positions.get(symbol, False)
        
        # BUY signal logic
        if not current_in_position:
            if rsi < self.oversold:
                if divergence == "bullish_divergence":
                    if not risk_manager.is_trading_allowed():
                        return None
                    logger.info(f"DIVERGENCE | BULLISH confirmed for {symbol} (RSI: {rsi:.2f})")
                    return "BUY"
                else:
                    logger.debug(f"STRATEGY | RSI oversold ({rsi:.2f}) for {symbol} but NO BULLISH DIVERGENCE detected yet.")

        # SELL signal logic
        if current_in_position:
            if rsi > self.overbought:
                if divergence == "bearish_divergence":
                    logger.info(f"DIVERGENCE | BEARISH confirmed for {symbol} (RSI: {rsi:.2f})")
                    return "SELL"
                else:
                    logger.debug(f"STRATEGY | RSI overbought ({rsi:.2f}) for {symbol} but NO BEARISH DIVERGENCE detected yet.")
                    
        return None

    async def update_position(self, symbol: str, in_position: bool):
        """Update and persist position status."""
        self.positions[symbol] = in_position
        key = f"{symbol.lower()}_in_position"
        await persistence.set_state(key, in_position)
