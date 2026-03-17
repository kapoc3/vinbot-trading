import logging
from typing import Dict, Any, Optional, List
from app.services.indicators import get_symbol_data
from app.services.risk_manager import risk_manager
from app.services.persistence import persistence

logger = logging.getLogger(__name__)

class MacdMaCrossStrategy:
    def __init__(self, ema_filter_period: int = 200, fast_macd: int = 12, slow_macd: int = 26, signal_macd: int = 9):
        self.ema_filter_period = ema_filter_period
        self.fast_macd = fast_macd
        self.slow_macd = slow_macd
        self.signal_macd = signal_macd
        # Flag to track if we are currently holding a position for a symbol
        self.positions: Dict[str, bool] = {}
        # Store previous histogram to detect crossovers
        self.prev_histograms: Dict[str, float] = {}

    async def load_initial_state(self, symbols: List[str]):
        """Load initial position state from persistence."""
        for symbol in symbols:
            key = f"{symbol.lower()}_in_position"
            stored_pos = await persistence.get_state(key, False)
            self.positions[symbol] = stored_pos
            if stored_pos:
                logger.info(f"RECOVERY | {symbol} recovered as IN_POSITION=True (MacdMaCross)")

    def analyze(self, symbol: str) -> Optional[str]:
        """
        Analyze using MACD and EMA 200 Filter.
        BUY: Price > EMA 200 AND MACD Crosses ABOVE Signal
        SELL: MACD Crosses BELOW Signal
        """
        symbol_data = get_symbol_data(symbol)
        ema_200 = symbol_data.get_ema(self.ema_filter_period)
        macd_data = symbol_data.get_macd(self.fast_macd, self.slow_macd, self.signal_macd)
        
        if ema_200 is None or macd_data is None or not symbol_data.closes:
            return None
            
        current_price = symbol_data.closes[-1]
        current_in_position = self.positions.get(symbol, False)
        current_hist = macd_data["histogram"]
        prev_hist = self.prev_histograms.get(symbol)
        
        # Update history for next call
        self.prev_histograms[symbol] = current_hist
        
        if prev_hist is None:
            return None # Need two points for crossover
            
        # BUY signal: Price > EMA 200 AND Histogram crossed from negative to positive
        if current_price > ema_200 and prev_hist < 0 and current_hist > 0 and not current_in_position:
            if not risk_manager.is_trading_allowed():
                logger.warning(f"STRATEGY | BUY signal blocked by RISK MANAGER for {symbol}")
                return None
            
            logger.info(f"STRATEGY | BUY Signal for {symbol} (Price: {current_price:.2f} > EMA200: {ema_200:.2f}, MACD Cross Up)")
            return "BUY"
            
        # SELL signal: Histogram crossed from positive to negative OR price falls below EMA 200 (safety)
        if (prev_hist > 0 and current_hist < 0) and current_in_position:
            logger.info(f"STRATEGY | SELL Signal for {symbol} (MACD Cross Down)")
            return "SELL"
            
        return None

    async def update_position(self, symbol: str, in_position: bool):
        """Update and persist the position tracker for a symbol."""
        self.positions[symbol] = in_position
        key = f"{symbol.lower()}_in_position"
        await persistence.set_state(key, in_position)

macd_strategy = MacdMaCrossStrategy()
