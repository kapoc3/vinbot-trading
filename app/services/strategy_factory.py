import logging
from typing import Dict, Any, Optional, List
from app.services.rsi_strategy import RSIStrategy
from app.services.divergence_strategy import RsiDivergenceStrategy
from app.services.bollinger_strategy import BollingerBandsStrategy
from app.services.regime_service import regime_service, MarketRegime
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
            new_strat = self.rsi_divergence
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

strategy_manager = StrategyManager()
# To maintain backward compatibility with main.py which expected 'current_strategy' as singleton:
# We now provide an instance that redirects 'analyze' and 'update_position' per symbol.
class DynamicStrategyProxy:
    def analyze(self, symbol: str) -> Optional[str]:
        return strategy_manager.get_strategy(symbol).analyze(symbol)
    
    async def update_position(self, symbol: str, in_position: bool):
        await strategy_manager.rsi_only.update_position(symbol, in_position)
        await strategy_manager.rsi_divergence.update_position(symbol, in_position)
        await strategy_manager.bollinger.update_position(symbol, in_position)

    async def load_initial_state(self, symbols: List[str]):
        await strategy_manager.load_initial_states(symbols)

current_strategy = DynamicStrategyProxy()
