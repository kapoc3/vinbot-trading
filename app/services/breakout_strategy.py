import logging
from typing import Dict, Optional, List
from app.services.indicators import get_symbol_data
from app.services.persistence import persistence
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class BreakoutStrategy:
    """
    Volatility Breakout Strategy using Donchian Channels.
    - BUY: Price breaks above the 20-period upper channel with volume confirmation.
    - SELL: Price crosses below the 20-period middle channel.
    """
    def __init__(self, period: int = 20):
        self.period = period
        self.positions: Dict[str, bool] = {}

    async def load_initial_state(self, symbols: List[str]):
        """Load positions from persistence."""
        for symbol in symbols:
            in_pos = await persistence.get_state(f"{symbol.lower()}_in_position", False)
            self.positions[symbol] = in_pos
            if in_pos:
                logger.info(f"STRATEGY | {symbol} loaded in-position state for BreakoutStrategy.")

    async def update_position(self, symbol: str, in_position: bool):
        """Update position state and persist."""
        self.positions[symbol] = in_position
        await persistence.set_state(f"{symbol.lower()}_in_position", in_position)

    def analyze(self, symbol: str) -> Optional[str]:
        """Evaluate market data for breakout signals."""
        data = get_symbol_data(symbol)
        
        # Ensure we have enough data
        if len(data.closes) < self.period:
            return None

        # 1. Indicator Calculation
        donchian = data.get_donchian_channel(self.period + 1) # Get period+1 to look at previous
        avg_vol = data.get_volume_sma(self.period)
        
        if not donchian or avg_vol is None or not data.volumes or len(data.highs) < self.period + 1:
            return None

        # To avoid comparing current close to current high (which would always be <=),
        # we calculate the Donchian Upper using the previous 'self.period' candles.
        prev_highs = list(data.highs)[-(self.period + 1):-1]
        prev_lows = list(data.lows)[-(self.period + 1):-1]
        
        prev_upper = max(prev_highs)
        prev_lower = min(prev_lows)
        prev_middle = (prev_upper + prev_lower) / 2

        current_price = data.closes[-1]
        current_vol = data.volumes[-1]
        in_pos = self.positions.get(symbol, False)

        # 2. EXIT Logic (If in position)
        if in_pos:
            # Exit if price falls below the previous middle band
            if current_price < prev_middle:
                logger.info(f"STRATEGY | {symbol} Breakout EXIT signal at {current_price:.2f} (Middle Band: {prev_middle:.2f})")
                return "SELL"
            return None

        # 3. ENTRY Logic (If not in position)
        volume_confirmed = current_vol > (avg_vol * settings.BREAKOUT_VOLUME_MULTIPLIER)

        if current_price >= prev_upper and volume_confirmed:
            logger.info(f"STRATEGY | {symbol} Breakout BUY signal at {current_price:.2f} (Prev Upper: {prev_upper:.2f}, Volume: {current_vol:.2f} vs Avg: {avg_vol:.2f})")
            return "BUY"

        return None
