import logging
from collections import deque
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """Mathematical logic for technical indicators using native Python."""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """
        Calculate Relative Strength Index (RSI) using Wilder's Smoothing.
        Requires at least period + 1 prices to calculate the first RSI.
        """
        if len(prices) <= period:
            return None
        
        gains: List[float] = []
        losses: List[float] = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(float(change))
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(float(abs(change)))
        
        # Initial averages (SMA)
        sum_gain: float = 0.0
        sum_loss: float = 0.0
        for i in range(period):
            sum_gain += gains[i]
            sum_loss += losses[i]
            
        avg_gain: float = sum_gain / period
        avg_loss: float = sum_loss / period
        
        # Wilder's Smoothing
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

class SymbolData:
    """Manages historical kline data for a specific symbol."""
    def __init__(self, max_history: int = 100):
        self.closes = deque(maxlen=max_history)
        self.klines = deque(maxlen=max_history)

    def add_close(self, close_price: float):
        """Add a new closing price to history."""
        self.closes.append(float(close_price))

    def get_rsi(self, period: int = 14) -> Optional[float]:
        """Calculate RSI for the current history."""
        return TechnicalIndicators.calculate_rsi(list(self.closes), period)

# Global store for symbol data
market_indicators: Dict[str, SymbolData] = {}

def get_symbol_data(symbol: str) -> SymbolData:
    """Get or create SymbolData for a specific symbol."""
    if symbol not in market_indicators:
        market_indicators[symbol] = SymbolData()
    return market_indicators[symbol]
