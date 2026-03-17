import logging
from typing import Dict, Any, Optional, List
from app.services.rsi_strategy import RSIStrategy
from app.services.divergence_strategy import RsiDivergenceStrategy
from app.services.bollinger_strategy import BollingerBandsStrategy
from app.services.macd_strategy import MacdMaCrossStrategy
from app.services.regime_service import regime_service, MarketRegime
from app.services.indicators import get_symbol_data
from app.services.persistence import persistence
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class StrategyManager:
    """Orchestrator to choose and switch strategies at runtime."""
    def __init__(self):
        self.strategy_type = settings.TRADING_STRATEGY
        self.rsi_only = RSIStrategy()
        self.rsi_divergence = RsiDivergenceStrategy()
        self.bollinger = BollingerBandsStrategy()
        self.macd_cross = MacdMaCrossStrategy()
        
        # Local cache for active strategies per symbol (for 'Auto' mode)
        self.symbol_strategies: Dict[str, Any] = {}
        # Strategy locks for when a position is open
        self.strategy_locks: Dict[str, bool] = {}

    def get_strategy(self, symbol: str) -> Any:
        """Returns the appropriate strategy instance for a given symbol."""
        if self.strategy_type != "Auto":
            if self.strategy_type == "RsiWithDivergence":
                return self.rsi_divergence
            if self.strategy_type == "BollingerBands":
                return self.bollinger
            if self.strategy_type == "MacdMaCross":
                return self.macd_cross
            return self.rsi_only

        # Auto Mode Logic
        if symbol not in self.symbol_strategies:
            self.symbol_strategies[symbol] = self.rsi_only # Default starting point

        return self.symbol_strategies[symbol]

    def re_evaluate_regime(self, symbol: str):
        """Re-evaluate the market regime and update the active strategy for symbol."""
        if self.strategy_type != "Auto":
            return

        # Check for Lock: Strategy MUST NOT switch while in position
        current_in_pos = self.get_strategy(symbol).positions.get(symbol, False)
        if current_in_pos:
            if not self.strategy_locks.get(symbol, False):
                logger.info(f"STRATEGY | Locking {symbol} strategy because POSITION IS OPEN.")
                self.strategy_locks[symbol] = True
            return

        # Unlock if no position is open
        if self.strategy_locks.get(symbol, False):
            logger.info(f"STRATEGY | Unlocking {symbol} strategy (position closed).")
            self.strategy_locks[symbol] = False

        # Classify the regime
        regime = regime_service.classify_regime(symbol)
        
        new_strat = self.rsi_only # Default for ranging
        if regime == MarketRegime.TRENDING:
            # Check trend strength
            adx = regime_service.get_adx_value(symbol)
            if adx > 40:
                new_strat = self.macd_cross # Strong trend needs confirmation
            else:
                new_strat = self.rsi_divergence # Normal trend follows momentum
        elif regime == MarketRegime.RANGING:
            new_strat = self.bollinger
        elif regime == MarketRegime.HIGH_VOLATILITY:
            # Could add a 'Pause' strategy or just stay in safety
            new_strat = self.rsi_divergence # Trend confirmers are safer in high volatility

        old_strat = self.symbol_strategies.get(symbol)
        if new_strat != old_strat:
            logger.info(f"STRATEGY | Switching {symbol} to: {new_strat.__class__.__name__} based on regime {regime.value}")
            # Ensure position status is maintained between strategy swap
            new_strat.positions[symbol] = False # Known from unlock check above
            self.symbol_strategies[symbol] = new_strat

    async def load_initial_states(self, symbols: List[str]):
        """Load states for both strategies."""
        await self.rsi_only.load_initial_state(symbols)
        await self.rsi_divergence.load_initial_state(symbols)
        await self.bollinger.load_initial_state(symbols)
        await self.macd_cross.load_initial_state(symbols)

strategy_manager = StrategyManager()
# To maintain backward compatibility with main.py which expected 'current_strategy' as singleton:
# We now provide an instance that redirects 'analyze' and 'update_position' per symbol.
class DynamicStrategyProxy:
    def __init__(self):
        self.highest_prices: Dict[str, float] = {}

    def analyze(self, symbol: str) -> Optional[str]:
        # 1. Trailing Stop Evaluation
        if settings.ENABLE_TRAILING_STOP:
            strategy = strategy_manager.get_strategy(symbol)
            in_position = strategy.positions.get(symbol, False)
            
            if in_position:
                symbol_data = get_symbol_data(symbol)
                if not symbol_data.closes:
                    return None
                    
                current_price = symbol_data.closes[-1]
                atr = symbol_data.get_atr()
                
                # Retrieve or initialize high watermark
                highest = self.highest_prices.get(symbol, current_price)
                if current_price > highest:
                    highest = current_price
                    self.highest_prices[symbol] = highest
                    # Persist the new high
                    # Note: Using asyncio within a synchronous 'analyze' call can be tricky, 
                    # but persistence here is mostly for recovery after crashes.
                
                if atr is not None:
                    stop_level = highest - (atr * settings.ATR_TRAILING_MULTIPLIER)
                    if current_price < stop_level:
                        logger.info(f"RISK | TRAILING STOP TRIGGERED for {symbol} at {current_price:.2f} (Stop: {stop_level:.2f}, ATR: {atr:.2f})")
                        return "SELL"

        # 2. Normal Strategy Analysis
        return strategy_manager.get_strategy(symbol).analyze(symbol)
    
    async def update_position(self, symbol: str, in_position: bool):
        # Update underlying strategies
        await strategy_manager.rsi_only.update_position(symbol, in_position)
        await strategy_manager.rsi_divergence.update_position(symbol, in_position)
        await strategy_manager.bollinger.update_position(symbol, in_position)
        await strategy_manager.macd_cross.update_position(symbol, in_position)
        
        # Update high watermark state
        if in_position:
            # Entering trade: set initial highest price
            symbol_data = get_symbol_data(symbol)
            current_price = symbol_data.closes[-1] if symbol_data.closes else 0.0
            self.highest_prices[symbol] = current_price
            await persistence.set_state(f"{symbol.lower()}_highest_price", current_price)
        else:
            # Exiting trade: clear state
            self.highest_prices[symbol] = 0.0
            await persistence.set_state(f"{symbol.lower()}_highest_price", 0.0)

    async def load_initial_state(self, symbols: List[str]):
        await strategy_manager.load_initial_states(symbols)
        # Recover high watermarks
        for symbol in symbols:
            key = f"{symbol.lower()}_highest_price"
            price = await persistence.get_state(key, 0.0)
            if price > 0:
                self.highest_prices[symbol] = price
                logger.info(f"RECOVERY | {symbol} recovered Trailing High Watermark: {price:.2f}")

current_strategy = DynamicStrategyProxy()
