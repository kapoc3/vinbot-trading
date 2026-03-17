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

    @staticmethod
    def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> Optional[float]:
        """Calculate Average True Range (ATR)."""
        if len(closes) < period + 1:
            return None
        
        tr_values = []
        for i in range(1, len(closes)):
            h = highs[i]
            l = lows[i]
            c_prev = closes[i-1]
            tr = max(h - l, abs(h - c_prev), abs(l - c_prev))
            tr_values.append(tr)
            
        if len(tr_values) < period:
            return None
            
        # RMA (Running Moving Average) used by Wilder for ATR
        atr = sum(tr_values[:period]) / period
        for i in range(period, len(tr_values)):
            atr = (atr * (period - 1) + tr_values[i]) / period
            
        return atr

    @staticmethod
    def calculate_adx(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> Optional[float]:
        """Calculate Average Directional Index (ADX)."""
        if len(closes) < 2 * period:
            return None
            
        tr_vals = []
        plus_dm_vals = []
        minus_dm_vals = []
        
        for i in range(1, len(closes)):
            tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
            tr_vals.append(tr)
            
            up_move = highs[i] - highs[i-1]
            down_move = lows[i-1] - lows[i]
            
            if up_move > down_move and up_move > 0:
                plus_dm_vals.append(up_move)
            else:
                plus_dm_vals.append(0.0)
                
            if down_move > up_move and down_move > 0:
                minus_dm_vals.append(down_move)
            else:
                minus_dm_vals.append(0.0)
                
        # Smoothing TR and DMs
        atr = sum(tr_vals[:period]) / period
        plus_di_smooth = sum(plus_dm_vals[:period]) / period
        minus_di_smooth = sum(minus_dm_vals[:period]) / period
        
        dx_vals = []
        for i in range(period, len(tr_vals)):
            atr = (atr * (period - 1) + tr_vals[i]) / period
            plus_di_smooth = (plus_di_smooth * (period - 1) + plus_dm_vals[i]) / period
            minus_di_smooth = (minus_di_smooth * (period - 1) + minus_dm_vals[i]) / period
            
            if atr == 0:
                dx = 0.0
            else:
                plus_di = 100 * (plus_di_smooth / atr)
                minus_di = 100 * (minus_di_smooth / atr)
                if plus_di + minus_di == 0:
                    dx = 0.0
                else:
                    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
            dx_vals.append(dx)
            
        if len(dx_vals) < period:
            return None
            
        # Smoothed DX to get ADX
        adx = sum(dx_vals[:period]) / period
        for i in range(period, len(dx_vals)):
            adx = (adx * (period - 1) + dx_vals[i]) / period
            
        return adx

    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev_multiplier: float = 2.0) -> Optional[Dict[str, float]]:
        """
        Calculate Bollinger Bands.
        Returns a dict with 'upper', 'middle' (SMA), and 'lower' bands.
        """
        if len(prices) < period:
            return None
            
        recent_prices = prices[-period:]
        sma = sum(recent_prices) / period
        
        # Standard deviation calculation
        variance = sum((x - sma) ** 2 for x in recent_prices) / period
        std_dev = variance ** 0.5
        
        return {
            "middle": sma,
            "upper": sma + (std_dev_multiplier * std_dev),
            "lower": sma - (std_dev_multiplier * std_dev)
        }

class SymbolData:
    """Manages historical kline data for a specific symbol."""
    def __init__(self, max_history: int = 150):
        self.closes = deque(maxlen=max_history)
        self.highs = deque(maxlen=max_history)
        self.lows = deque(maxlen=max_history)
        self.rsis = deque(maxlen=max_history)
        self.klines = deque(maxlen=max_history)

    def add_kline(self, kline: Dict):
        """Add a full kline and update all indicator histories."""
        close_price = float(kline.get("c", 0))
        high_price = float(kline.get("h", 0))
        low_price = float(kline.get("l", 0))
        
        self.closes.append(close_price)
        self.highs.append(high_price)
        self.lows.append(low_price)
        self.klines.append(kline)
        
        # Calculate current RSI and store it
        current_rsi = self.get_rsi()
        if current_rsi is not None:
            self.rsis.append(current_rsi)

    def add_close(self, close_price: float):
        """Add a new closing price (fallback if only close is known)."""
        self.closes.append(float(close_price))
        # For indicators requiring high/low, we use close as estimate if unknown
        if len(self.highs) < len(self.closes):
            self.highs.append(close_price)
            self.lows.append(close_price)
        
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

    def get_adx(self, period: int = 14) -> Optional[float]:
        """Calculate current ADX."""
        return TechnicalIndicators.calculate_adx(list(self.highs), list(self.lows), list(self.closes), period)

    def get_atr(self, period: int = 14) -> Optional[float]:
        """Calculate current ATR."""
        return TechnicalIndicators.calculate_atr(list(self.highs), list(self.lows), list(self.closes), period)

    def get_bollinger_bands(self, period: int = 20, std_dev_multiplier: float = 2.0) -> Optional[Dict[str, float]]:
        """Calculate Bollinger Bands for the current history."""
        return TechnicalIndicators.calculate_bollinger_bands(list(self.closes), period, std_dev_multiplier)

# Global store for symbol data
market_indicators: Dict[str, SymbolData] = {}

def get_symbol_data(symbol: str) -> SymbolData:
    """Get or create SymbolData for a specific symbol."""
    if symbol not in market_indicators:
        market_indicators[symbol] = SymbolData()
    return market_indicators[symbol]
