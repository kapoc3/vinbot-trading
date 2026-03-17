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

    @staticmethod
    def find_local_extrema(data: List[float], pivot_length: int = 5) -> List[Dict]:
        """
        Identify local peaks and valleys.
        A point is an extremum if it's the highest/lowest in a window of pivot_length 
        both before and after it.
        Returns a list of dicts: {'index': int, 'value': float, 'type': 'high'|'low'}
        """
        extrema = []
        if len(data) < 2 * pivot_length + 1:
            return extrema

        for i in range(pivot_length, len(data) - pivot_length):
            window = data[i - pivot_length : i + pivot_length + 1]
            current_val = data[i]
            
            if current_val == max(window):
                # Potential high
                if window.count(current_val) == 1: # Strict peak
                    extrema.append({'index': i, 'value': current_val, 'type': 'high'})
            elif current_val == min(window):
                # Potential low
                if window.count(current_val) == 1: # Strict valley
                    extrema.append({'index': i, 'value': current_val, 'type': 'low'})
        
        return extrema

    @staticmethod
    def check_divergence(prices: List[float], rsis: List[float], pivot_length: int = 5) -> Optional[str]:
        """
        Detect regular bullish/bearish divergence.
        Bullish: Price Lower Low vs RSI Higher Low
        Bearish: Price Higher High vs RSI Lower High
        """
        price_extrema = TechnicalIndicators.find_local_extrema(prices, pivot_length)
        rsi_extrema = TechnicalIndicators.find_local_extrema(rsis, pivot_length)

        # Filter for the last two same-type extrema
        price_lows = [e for e in price_extrema if e['type'] == 'low']
        price_highs = [e for e in price_extrema if e['type'] == 'high']
        rsi_lows = [e for e in rsi_extrema if e['type'] == 'low']
        rsi_highs = [e for e in rsi_extrema if e['type'] == 'high']

        # Bullish Divergence check (Recent Lows)
        if len(price_lows) >= 2 and len(rsi_lows) >= 2:
            p2, p1 = price_lows[-2], price_lows[-1] # p1 is more recent
            # Look for corresponding RSI points (within a tolerance of indices or same relative sequence)
            # For simplicity in this native version, we assume the latest 2 swings are the target
            r2, r1 = rsi_lows[-2], rsi_lows[-1]

            if p1['value'] < p2['value'] and r1['value'] > r2['value']:
                return "bullish_divergence"

        # Bearish Divergence check (Recent Highs)
        if len(price_highs) >= 2 and len(rsi_highs) >= 2:
            p2, p1 = price_highs[-2], price_highs[-1]
            r2, r1 = rsi_highs[-2], rsi_highs[-1]

            if p1['value'] > p2['value'] and r1['value'] < r2['value']:
                return "bearish_divergence"

        return None

class SymbolData:
    """Manages historical kline data for a specific symbol."""
    def __init__(self, max_history: int = 150):
        self.closes = deque(maxlen=max_history)
        self.rsis = deque(maxlen=max_history)
        self.klines = deque(maxlen=max_history)

    def add_close(self, close_price: float):
        """Add a new closing price and update RSI history."""
        self.closes.append(float(close_price))
        
        # Calculate current RSI and store it
        current_rsi = self.get_rsi()
        if current_rsi is not None:
            self.rsis.append(current_rsi)

    def get_rsi(self, period: int = 14) -> Optional[float]:
        """Calculate RSI for the current history."""
        return TechnicalIndicators.calculate_rsi(list(self.closes), period)

    def get_divergence(self, pivot_length: int = 5) -> Optional[str]:
        """Check for divergence between price and RSI."""
        if len(self.closes) < 20 or len(self.rsis) < 20:
            return None
        return TechnicalIndicators.check_divergence(list(self.closes), list(self.rsis), pivot_length)

# Global store for symbol data
market_indicators: Dict[str, SymbolData] = {}

def get_symbol_data(symbol: str) -> SymbolData:
    """Get or create SymbolData for a specific symbol."""
    if symbol not in market_indicators:
        market_indicators[symbol] = SymbolData()
    return market_indicators[symbol]
