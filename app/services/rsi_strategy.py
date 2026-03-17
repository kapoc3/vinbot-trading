import logging
from typing import Dict, Any, Optional
from app.services.indicators import get_symbol_data

logger = logging.getLogger(__name__)

class RSIStrategy:
    def __init__(self, rsi_period: int = 14, overbought: float = 70.0, oversold: float = 30.0):
        self.rsi_period = rsi_period
        self.overbought = overbought
        self.oversold = oversold
        # Flag to track if we are currently holding a position for a symbol
        self.positions: Dict[str, bool] = {}

    def analyze(self, symbol: str) -> Optional[str]:
        """
        Analyze the RSI for a symbol and return 'BUY', 'SELL', or None.
        (Task 3.2 & 3.3)
        """
        symbol_data = get_symbol_data(symbol)
        rsi = symbol_data.get_rsi(self.rsi_period)
        
        if rsi is None:
            return None
            
        current_in_position = self.positions.get(symbol, False)
        
        # BUY signal: Oversold and not in position
        if rsi < self.oversold and not current_in_position:
            logger.info(f"STRATEGY | BUY Signal for {symbol} (RSI: {rsi:.2f})")
            return "BUY"
            
        # SELL signal: Overbought and in position
        if rsi > self.overbought and current_in_position:
            logger.info(f"STRATEGY | SELL Signal for {symbol} (RSI: {rsi:.2f})")
            return "SELL"
            
        return None

    def update_position(self, symbol: str, in_position: bool):
        """Update the internal position tracker for a symbol."""
        self.positions[symbol] = in_position

# Singleton instance of the strategy
rsi_strategy = RSIStrategy()
