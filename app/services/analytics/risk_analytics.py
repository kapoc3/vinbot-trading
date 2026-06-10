"""
Risk Analytics - Real-time risk metrics.
"""
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import numpy as np

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class PositionPnL:
    symbol: str
    side: str
    entry_price: float
    current_price: float
    quantity: float
    unrealized_pnl: float
    pnl_pct: float


@dataclass
class RiskMetrics:
    total_exposure: float
    total_pnl: float
    unrealized_pnl: float
    realized_pnl: float
    var_95: float
    expected_shortfall: float
    current_drawdown: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int


@dataclass
class ExposureBySymbol:
    symbol: str
    position_value: float
    exposure_pct: float
    side: str  # LONG or SHORT


class RiskCalculator:
    """Calculate risk metrics."""

    def __init__(self):
        self.var_window = settings.VAR_WINDOW
        self.var_confidence = settings.VAR_CONFIDENCE
        self.max_drawdown_threshold = settings.MAX_DRAWDOWN_THRESHOLD

    def calculate_var(self, returns: List[float]) -> float:
        """Calculate Value at Risk using historical method."""
        if not returns or len(returns) < 2:
            return 0.0

        # Use only last N days
        window_returns = returns[-self.var_window:] if len(returns) > self.var_window else returns

        # VaR at specified confidence level
        percentile = (1 - self.var_confidence) * 100
        var = np.percentile(window_returns, percentile)

        return abs(var) * 100  # Return as percentage

    def calculate_expected_shortfall(self, returns: List[float]) -> float:
        """Calculate Expected Shortfall (CVaR)."""
        if not returns or len(returns) < 2:
            return 0.0

        window_returns = returns[-self.var_window:] if len(returns) > self.var_window else returns

        percentile = (1 - self.var_confidence) * 100
        var = np.percentile(window_returns, percentile)

        # Average of all returns below VaR
        tail_returns = [r for r in window_returns if r <= var]
        if not tail_returns:
            return 0.0

        return abs(np.mean(tail_returns)) * 100

    def calculate_drawdown(self, equity_curve: List[float]) -> tuple[float, float]:
        """Calculate current and max drawdown."""
        if not equity_curve or len(equity_curve) < 2:
            return 0.0, 0.0

        peak = equity_curve[0]
        max_dd = 0.0
        current_dd = 0.0

        for value in equity_curve:
            if value > peak:
                peak = value

            dd = (peak - value) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
            current_dd = dd

        return current_dd * 100, max_dd * 100

    def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio."""
        if not returns or len(returns) < 2:
            return 0.0

        returns_array = np.array(returns)
        excess_returns = returns_array - (risk_free_rate / 252)  # Daily risk-free

        if np.std(excess_returns) == 0:
            return 0.0

        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)


class PositionTracker:
    """Track positions and PnL."""

    def __init__(self):
        self.positions: Dict[str, PositionPnL] = {}
        self.closed_trades: List[Dict] = []
        self.equity_history: List[float] = []
        self.initial_equity = 10000.0

    def update_position(self, symbol: str, side: str, entry_price: float, quantity: float, current_price: float):
        """Update or create a position."""
        unrealized = (current_price - entry_price) * quantity if side == "LONG" else (entry_price - current_price) * quantity
        pnl_pct = (unrealized / (entry_price * quantity)) * 100 if entry_price * quantity > 0 else 0

        self.positions[symbol] = PositionPnL(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            current_price=current_price,
            quantity=quantity,
            unrealized_pnl=unrealized,
            pnl_pct=pnl_pct
        )

    def close_position(self, symbol: str, exit_price: float):
        """Close a position and record trade."""
        if symbol not in self.positions:
            return

        pos = self.positions[symbol]
        realized_pnl = (exit_price - pos.entry_price) * pos.quantity if pos.side == "LONG" else (pos.entry_price - exit_price) * pos.quantity

        trade = {
            "symbol": symbol,
            "side": pos.side,
            "entry_price": pos.entry_price,
            "exit_price": exit_price,
            "quantity": pos.quantity,
            "pnl": realized_pnl,
            "pnl_pct": pos.pnl_pct,
            "timestamp": datetime.now()
        }

        self.closed_trades.append(trade)
        del self.positions[symbol]

    def get_total_pnl(self) -> tuple[float, float, float]:
        """Get total PnL (unrealized + realized)."""
        unrealized = sum(p.unrealized_pnl for p in self.positions.values())
        realized = sum(t["pnl"] for t in self.closed_trades)
        total = unrealized + realized
        return total, unrealized, realized

    def get_exposure_by_symbol(self, total_portfolio_value: float) -> List[ExposureBySymbol]:
        """Get exposure breakdown by symbol."""
        exposures = []
        for pos in self.positions.values():
            position_value = pos.current_price * pos.quantity
            exposure_pct = (position_value / total_portfolio_value) * 100 if total_portfolio_value > 0 else 0

            exposures.append(ExposureBySymbol(
                symbol=pos.symbol,
                position_value=position_value,
                exposure_pct=exposure_pct,
                side=pos.side
            ))

        return sorted(exposures, key=lambda x: x.position_value, reverse=True)

    def get_win_rate(self) -> tuple[float, int, int]:
        """Calculate win rate."""
        if not self.closed_trades:
            return 0.0, 0, 0

        winning = sum(1 for t in self.closed_trades if t["pnl"] > 0)
        total = len(self.closed_trades)

        return (winning / total * 100) if total > 0 else 0.0, winning, total - winning


class RiskAnalytics:
    """Main risk analytics dashboard."""

    def __init__(self):
        self.enabled = settings.ANALYTICS_ENABLED
        self.calculator = RiskCalculator()
        self.tracker = PositionTracker()

    def get_full_analytics(self, current_prices: Dict[str, float]) -> Dict:
        """Get complete analytics dashboard."""
        # Update positions with current prices
        for symbol, pos in self.tracker.positions.items():
            if symbol in current_prices:
                self.tracker.update_position(
                    symbol, pos.side, pos.entry_price,
                    pos.quantity, current_prices[symbol]
                )

        # Get PnL
        total_pnl, unrealized, realized = self.tracker.get_total_pnl()

        # Calculate portfolio value
        portfolio_value = self.tracker.initial_equity + unrealized + realized
        self.tracker.equity_history.append(portfolio_value)

        # Get risk metrics
        returns = self._calculate_returns()
        var_95 = self.calculator.calculate_var(returns)
        es = self.calculator.calculate_expected_shortfall(returns)
        current_dd, max_dd = self.calculator.calculate_drawdown(self.tracker.equity_history)
        sharpe = self.calculator.calculate_sharpe_ratio(returns)

        # Get win rate
        win_rate, winners, losers = self.tracker.get_win_rate()

        # Total exposure
        total_exposure = sum(
            pos.current_price * pos.quantity
            for pos in self.tracker.positions.values()
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "portfolio_value": portfolio_value,
            "total_pnl": total_pnl,
            "unrealized_pnl": unrealized,
            "realized_pnl": realized,
            "risk_metrics": {
                "var_95": var_95,
                "expected_shortfall": es,
                "current_drawdown": current_dd,
                "max_drawdown": max_dd,
                "sharpe_ratio": sharpe
            },
            "performance": {
                "win_rate": win_rate,
                "total_trades": len(self.tracker.closed_trades),
                "winning_trades": winners,
                "losing_trades": losers
            },
            "exposure": self.tracker.get_exposure_by_symbol(portfolio_value),
            "positions": [
                {
                    "symbol": p.symbol,
                    "side": p.side,
                    "entry_price": p.entry_price,
                    "current_price": p.current_price,
                    "quantity": p.quantity,
                    "unrealized_pnl": p.unrealized_pnl,
                    "pnl_pct": p.pnl_pct
                }
                for p in self.tracker.positions.values()
            ]
        }

    def _calculate_returns(self) -> List[float]:
        """Calculate historical returns from equity curve."""
        if len(self.tracker.equity_history) < 2:
            return []

        returns = []
        for i in range(1, len(self.tracker.equity_history)):
            prev = self.tracker.equity_history[i-1]
            curr = self.tracker.equity_history[i]
            if prev > 0:
                returns.append((curr - prev) / prev)

        return returns


risk_analytics = RiskAnalytics()


def get_risk_analytics() -> RiskAnalytics:
    return risk_analytics