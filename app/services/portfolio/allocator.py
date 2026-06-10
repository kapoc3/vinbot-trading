"""
Portfolio allocation and rebalancing.
"""
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

import numpy as np

from app.core.config import get_settings
from app.services.indicators import SymbolData

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class PositionTarget:
    symbol: str
    target_pct: float
    current_pct: float
    deviation_pct: float
    action: str  # INCREASE, DECREASE, HOLD


class VolatilityAllocator:
    """Allocate capital based on inverse volatility."""

    @staticmethod
    def calculate_atr(closes: List[float], highs: List[float], lows: List[float], period: int = 14) -> float:
        """Calculate ATR indicator."""
        if len(closes) < period + 1:
            return 0.0

        trs = []
        for i in range(1, len(closes)):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])
            tr = max(high_low, high_close, low_close)
            trs.append(tr)

        if len(trs) < period:
            return np.mean(trs) if trs else 0.0

        return np.mean(trs[-period:])

    def allocate(self, symbols: List[str], symbol_data: Dict[str, SymbolData]) -> Dict[str, float]:
        """Calculate allocation weights based on inverse volatility."""
        atr_values = {}

        for symbol in symbols:
            data = symbol_data.get(symbol)
            if not data or not data.closes or len(data.closes) < 20:
                # Use default weight
                atr_values[symbol] = 1.0
                continue

            closes = data.closes[-50:] if len(data.closes) >= 50 else data.closes
            highs = data.highs[-len(closes):] if data.highs else closes
            lows = data.lows[-len(closes):] if data.lows else closes

            atr = self.calculate_atr(closes, highs, lows)
            if atr > 0:
                atr_values[symbol] = atr
            else:
                atr_values[symbol] = 1.0

        # Inverse volatility: lower ATR = higher weight
        inverse_atr = {s: 1.0 / v for s, v in atr_values.items()}
        total = sum(inverse_atr.values())

        if total == 0:
            return {s: 1.0 / len(symbols) for s in symbols}

        # Normalize to percentages
        weights = {s: (v / total) * 100 for s, v in inverse_atr.items()}

        return weights


class RiskWeightedAllocator:
    """Allocate based on VaR and drawdown risk."""

    def allocate(self, symbols: List[str], symbol_data: Dict[str, SymbolData]) -> Dict[str, float]:
        """Calculate risk-based allocation."""
        risk_scores = {}

        for symbol in symbols:
            data = symbol_data.get(symbol)
            if not data or not data.closes or len(data.closes) < 20:
                risk_scores[symbol] = 1.0
                continue

            closes = np.array(data.closes[-50:])
            returns = np.diff(closes) / closes[:-1]

            # VaR 95%
            var_95 = np.percentile(returns, 5)
            # Max drawdown
            cummax = np.maximum.accumulate(closes)
            drawdown = (cummax - closes) / cummax
            max_dd = np.max(drawdown) if len(drawdown) > 0 else 0

            # Risk score: higher = more risky
            risk = abs(var_95) + max_dd
            risk_scores[symbol] = risk if risk > 0 else 0.01

        # Inverse risk: lower risk = higher weight
        inverse_risk = {s: 1.0 / v for s, v in risk_scores.items()}
        total = sum(inverse_risk.values())

        if total == 0:
            return {s: 1.0 / len(symbols) for s in symbols}

        weights = {s: (v / total) * 100 for s, v in inverse_risk.items()}

        return weights


class EqualAllocator:
    """Equal weight allocation."""

    def allocate(self, symbols: List[str], symbol_data: Dict[str, SymbolData]) -> Dict[str, float]:
        """Equal weight across all symbols."""
        if not symbols:
            return {}

        weight = 100.0 / len(symbols)
        return {s: weight for s in symbols}


class PortfolioRebalancer:
    """Main rebalancing manager."""

    def __init__(self):
        self.enabled = settings.PORTFOLIO_REBALANCING_ENABLED
        self.allocation_method = settings.ALLOCATION_METHOD
        self.rebalance_threshold = settings.REBALANCE_THRESHOLD_PCT
        self.max_position_pct = settings.MAX_POSITION_PCT
        self.min_position_pct = settings.MIN_POSITION_PCT
        self.correlation_threshold = settings.CORRELATION_THRESHOLD

        self.allocators = {
            "equal": EqualAllocator(),
            "inverse_volatility": VolatilityAllocator(),
            "risk_weighted": RiskWeightedAllocator()
        }

        self.current_allocation: Dict[str, float] = {}
        logger.info(f"Portfolio Rebalancer initialized: method={self.allocation_method}, enabled={self.enabled}")

    def get_allocator(self):
        """Get the appropriate allocator."""
        return self.allocators.get(self.allocation_method, EqualAllocator())

    def calculate_allocation(self, symbols: List[str], symbol_data: Dict[str, SymbolData]) -> Dict[str, float]:
        """Calculate target allocation for symbols."""
        if not self.enabled:
            # Equal weight by default
            return {s: 100.0 / len(symbols) for s in symbols} if symbols else {}

        allocator = self.get_allocator()
        weights = allocator.allocate(symbols, symbol_data)

        # Apply max/min limits
        for symbol in weights:
            weights[symbol] = min(max(weights[symbol], self.min_position_pct), self.max_position_pct)

        # Renormalize after limits
        total = sum(weights.values())
        if total > 0:
            weights = {s: (v / total) * 100 for s, v in weights.items()}

        self.current_allocation = weights
        return weights

    def check_rebalance_needed(self, current_positions: Dict[str, float], total_portfolio_value: float) -> List[PositionTarget]:
        """Check if rebalancing is needed based on current positions."""
        if total_portfolio_value == 0:
            return []

        targets = []
        for symbol, target_pct in self.current_allocation.items():
            current_value = current_positions.get(symbol, 0)
            current_pct = (current_value / total_portfolio_value) * 100 if total_portfolio_value > 0 else 0

            deviation = current_pct - target_pct
            deviation_pct = abs(deviation) / target_pct * 100 if target_pct > 0 else 0

            if deviation_pct > self.rebalance_threshold:
                if deviation > 0:
                    action = "DECREASE"
                else:
                    action = "INCREASE"
            else:
                action = "HOLD"

            targets.append(PositionTarget(
                symbol=symbol,
                target_pct=target_pct,
                current_pct=current_pct,
                deviation_pct=deviation_pct,
                action=action
            ))

        return targets

    def get_position_size(self, symbol: str, total_capital: float) -> float:
        """Get recommended position size for a symbol."""
        target_pct = self.current_allocation.get(symbol, 0)
        return (target_pct / 100) * total_capital


portfolio_rebalancer = PortfolioRebalancer()


def get_portfolio_rebalancer() -> PortfolioRebalancer:
    return portfolio_rebalancer