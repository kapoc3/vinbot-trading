"""
Paper Trading - Simulated trading engine.
"""
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import numpy as np

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PaperPositionSide(Enum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class PaperPosition:
    symbol: str
    side: PaperPositionSide
    entry_price: float
    quantity: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    unrealized_pnl: float = 0.0


@dataclass
class PaperOrder:
    order_id: str
    symbol: str
    side: str  # BUY or SELL
    order_type: str  # MARKET, LIMIT
    quantity: float
    price: Optional[float] = None
    filled_price: Optional[float] = None
    status: str = "PENDING"  # PENDING, FILLED, CANCELLED
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PaperTrade:
    trade_id: str
    order_id: str
    symbol: str
    side: str
    price: float
    quantity: float
    commission: float
    slippage: float
    timestamp: datetime


class VirtualBalance:
    """Virtual balance management."""

    def __init__(self, initial_balance: float = 10000.0):
        self.total_balance = initial_balance
        self.available_balance = initial_balance
        self.positions: Dict[str, PaperPosition] = {}
        self.closed_pnl: float = 0.0

    def can_open_position(self, cost: float) -> bool:
        """Check if can afford position."""
        return self.available_balance >= cost

    def reserve_balance(self, cost: float) -> bool:
        """Reserve balance for position."""
        if self.can_open_position(cost):
            self.available_balance -= cost
            return True
        return False

    def release_balance(self, amount: float):
        """Release reserved balance."""
        self.available_balance += amount

    def add_pnl(self, pnl: float):
        """Add realized PnL."""
        self.closed_pnl += pnl
        self.total_balance += pnl

    def update_position_value(self, symbol: str, current_price: float):
        """Update unrealized PnL for position."""
        if symbol in self.positions:
            pos = self.positions[symbol]
            if pos.side == PaperPositionSide.LONG:
                pos.unrealized_pnl = (current_price - pos.entry_price) * pos.quantity
            else:
                pos.unrealized_pnl = (pos.entry_price - current_price) * pos.quantity

    def get_total_equity(self, prices: Dict[str, float]) -> float:
        """Get total equity including unrealized PnL."""
        equity = self.available_balance + self.closed_pnl
        for symbol, pos in self.positions.items():
            if symbol in prices:
                self.update_position_value(symbol, prices[symbol])
                equity += pos.unrealized_pnl
        return equity


class PaperTradingEngine:
    """Paper trading execution engine."""

    def __init__(self):
        self.enabled = settings.PAPER_TRADING_ENABLED
        self.slippage = settings.PAPER_SLIPPAGE
        self.commission = settings.PAPER_COMMISSION
        self.initial_balance = settings.PAPER_INITIAL_BALANCE

        self.balance = VirtualBalance(self.initial_balance)
        self.orders: List[PaperOrder] = []
        self.trades: List[PaperTrade] = []
        self.order_counter = 0
        self.trade_counter = 0

        self.symbol_mode: Dict[str, bool] = {}  # symbol -> True if paper

        logger.info(f"Paper Trading initialized: enabled={self.enabled}, balance={self.initial_balance}")

    def set_symbol_mode(self, symbol: str, paper_mode: bool):
        """Set whether a symbol trades in paper or real mode."""
        self.symbol_mode[symbol] = paper_mode
        logger.info(f"Symbol {symbol} mode: {'PAPER' if paper_mode else 'REAL'}")

    def is_paper_symbol(self, symbol: str) -> bool:
        """Check if symbol trades in paper mode."""
        if not self.enabled:
            return False
        return self.symbol_mode.get(symbol, True)  # Default to paper if enabled

    def simulate_market_order(
        self,
        side: str,
        price: float,
        quantity: float
    ) -> tuple[float, float, float]:
        """Simulate order execution with slippage and commission."""
        # Apply slippage
        if side == "BUY":
            fill_price = price * (1 + self.slippage)
        else:
            fill_price = price * (1 - self.slippage)

        commission_cost = fill_price * quantity * self.commission

        return fill_price, commission_cost, self.slippage

    def execute_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        current_price: float,
        order_type: str = "MARKET"
    ) -> Optional[PaperTrade]:
        """Execute a paper order."""
        if not self.is_paper_symbol(symbol):
            logger.warning(f"Cannot execute paper order for {symbol} - not in paper mode")
            return None

        self.order_counter += 1
        order_id = f"PAPER_{self.order_counter}"

        order = PaperOrder(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=current_price
        )

        # Simulate execution
        fill_price, commission, slippage = self.simulate_market_order(
            side, current_price, quantity
        )

        order.filled_price = fill_price
        order.status = "FILLED"
        self.orders.append(order)

        # Record trade
        self.trade_counter += 1
        trade = PaperTrade(
            trade_id=f"TRADE_{self.trade_counter}",
            order_id=order_id,
            symbol=symbol,
            side=side,
            price=fill_price,
            quantity=quantity,
            commission=commission,
            slippage=slippage,
            timestamp=datetime.now()
        )
        self.trades.append(trade)

        logger.info(f"PAPER TRADE | {symbol} {side} {quantity} @ {fill_price:.4f} (commission: {commission:.2f})")

        return trade

    def open_position(
        self,
        symbol: str,
        side: str,
        quantity: float,
        current_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Optional[PaperPosition]:
        """Open a paper position."""
        trade = self.execute_order(symbol, side, quantity, current_price)
        if not trade:
            return None

        position = PaperPosition(
            symbol=symbol,
            side=PaperPositionSide.LONG if side == "BUY" else PaperPositionSide.SHORT,
            entry_price=trade.price,
            quantity=quantity,
            entry_time=trade.timestamp,
            stop_loss=stop_loss,
            take_profit=take_profit
        )

        self.balance.positions[symbol] = position

        logger.info(f"PAPER POSITION | Opened {position.side.value} {symbol} @ {position.entry_price:.4f}")
        return position

    def close_position(
        self,
        symbol: str,
        current_price: float
    ) -> Optional[float]:
        """Close a paper position and return realized PnL."""
        if symbol not in self.balance.positions:
            logger.warning(f"No position to close for {symbol}")
            return None

        position = self.balance.positions[symbol]
        side = "SELL" if position.side == PaperPositionSide.LONG else "BUY"

        trade = self.execute_order(symbol, side, position.quantity, current_price)
        if not trade:
            return None

        # Calculate realized PnL
        if position.side == PaperPositionSide.LONG:
            pnl = (trade.price - position.entry_price) * position.quantity
        else:
            pnl = (position.entry_price - trade.price) * position.quantity

        # Deduct commissions
        pnl -= trade.commission

        self.balance.add_pnl(pnl)
        del self.balance.positions[symbol]

        logger.info(f"PAPER CLOSE | {symbol} @ {trade.price:.4f} | PnL: {pnl:.2f}")
        return pnl

    def get_status(self) -> dict:
        """Get paper trading status."""
        return {
            "enabled": self.enabled,
            "total_balance": self.balance.total_balance,
            "available_balance": self.balance.available_balance,
            "closed_pnl": self.balance.closed_pnl,
            "open_positions": len(self.balance.positions),
            "total_orders": len(self.orders),
            "total_trades": len(self.trades)
        }

    def reset(self):
        """Reset paper trading state."""
        self.balance = VirtualBalance(self.initial_balance)
        self.orders = []
        self.trades = []
        self.order_counter = 0
        self.trade_counter = 0
        logger.info("Paper trading state reset")


paper_trading_engine = PaperTradingEngine()


def get_paper_engine() -> PaperTradingEngine:
    return paper_trading_engine