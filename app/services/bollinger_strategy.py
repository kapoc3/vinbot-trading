import logging
from typing import Dict, Any, Optional, List
from app.services.indicators import get_symbol_data
from app.services.risk_manager import risk_manager
from app.services.persistence import persistence

logger = logging.getLogger(__name__)

class BollingerBandsStrategy:
    def __init__(self, rsi_period: int = 14, overbought: float = 70.0, oversold: float = 30.0, bb_period: int = 20, bb_std_dev: float = 2.0):
        self.rsi_period = rsi_period
        self.overbought = overbought
        self.oversold = oversold
        self.bb_period = bb_period
        self.bb_std_dev = bb_std_dev
        # Flag to track if we are currently holding a position for a symbol
        self.positions: Dict[str, bool] = {}

    async def load_initial_state(self, symbols: List[str]):
        """Load initial position state from persistence."""
        for symbol in symbols:
            key = f"{symbol.lower()}_in_position"
            stored_pos = await persistence.get_state(key, False)
            self.positions[symbol] = stored_pos
            if stored_pos:
                logger.info(f"RECOVERY | {symbol} recovered as IN_POSITION=True (BollingerBands)")

    def analyze(self, symbol: str) -> Optional[str]:
        """
        Analyze using Bollinger Bands and RSI.
        BUY: Price < Lower Band AND RSI < 30
        SELL: Price > Middle Band AND RSI > 70
        """
        symbol_data = get_symbol_data(symbol)
        rsi = symbol_data.get_rsi(self.rsi_period)
        bb = symbol_data.get_bollinger_bands(self.bb_period, self.bb_std_dev)
        
        if rsi is None or bb is None or not symbol_data.closes:
            return None
            
        current_price = symbol_data.closes[-1]
        current_in_position = self.positions.get(symbol, False)
        
        # BUY signal: Price < Lower Band AND RSI < Oversold AND not in position
        if current_price < bb["lower"] and rsi < self.oversold and not current_in_position:
            if not risk_manager.is_trading_allowed():
                logger.warning(f"STRATEGY | BUY signal blocked by RISK MANAGER for {symbol}")
                return None
            
            logger.info(f"STRATEGY | BUY Signal for {symbol} (Price: {current_price:.2f}, Lower Band: {bb['lower']:.2f}, RSI: {rsi:.2f})")
            return "BUY"
            
        # SELL signal: Price > Middle Band AND RSI > Overbought AND in position
        if current_price > bb["middle"] and rsi > self.overbought and current_in_position:
            logger.info(f"STRATEGY | SELL Signal for {symbol} (Price: {current_price:.2f}, Middle Band: {bb['middle']:.2f}, RSI: {rsi:.2f})")
            return "SELL"
            
        return None

    async def update_position(self, symbol: str, in_position: bool):
        """Update and persist the position tracker for a symbol."""
        self.positions[symbol] = in_position
        key = f"{symbol.lower()}_in_position"
        await persistence.set_state(key, in_position)

bollinger_strategy = BollingerBandsStrategy()
