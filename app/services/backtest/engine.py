"""
Backtest engine - executes strategies against historical data.
"""
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
from enum import Enum

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TradeSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Trade:
    """Represents a single trade in the backtest."""
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    side: TradeSide
    pnl: float
    pnl_pct: float
    quantity: float
    commission: float
    duration_hours: float


@dataclass
class Position:
    """Represents an open position."""
    entry_time: datetime
    entry_price: float
    quantity: float
    side: TradeSide


@dataclass
class BacktestResult:
    """Contains the results of a backtest run."""
    strategy_name: str
    symbol: str
    timeframe: str
    start_date: str
    end_date: str

    trades: List[Trade] = field(default_factory=list)
    initial_capital: float = 0.0
    final_capital: float = 0.0
    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0

    # Position tracking
    position: Optional[Position] = None

    # Equity curve
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)

    # Configuration used
    config: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    run_time_seconds: float = 0.0
    total_candles: int = 0
    skipped_trades: int = 0


class BacktestEngine:
    """
    Core backtest engine that simulates trading with historical data.
    """

    def __init__(
        self,
        initial_capital: Optional[float] = None,
        slippage_majors: float = 0.001,
        slippage_alts: float = 0.002,
        commission: float = 0.001
    ):
        self.initial_capital = initial_capital or settings.BACKTEST_INITIAL_CAPITAL
        self.slippage_majors = slippage_majors
        self.slippage_alts = slippage_alts
        self.commission = commission

    def run(
        self,
        strategy_fn: Callable,
        klines: List[Any],
        symbol: str,
        strategy_name: str = "Strategy",
        timeframe: str = "1h",
        start_date: str = "",
        end_date: str = "",
        stop_loss_pct: float = 2.0,
        take_profit_pct: float = 5.0,
        risk_per_trade_pct: float = 1.0,
    ) -> BacktestResult:
        """
        Run a backtest with the given strategy and historical data.

        Args:
            strategy_fn: Function that takes (symbol, closes, highs, lows, rsi, etc.)
                        and returns "BUY", "SELL", or None
            klines: List of Kline objects
            symbol: Trading symbol
            strategy_name: Name for reporting
            timeframe: Timeframe used
            start_date: Start date string
            end_date: End date string
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
            risk_per_trade_pct: Risk per trade percentage

        Returns:
            BacktestResult object with all metrics
        """
        import time
        start_time = time.time()

        result = BacktestResult(
            strategy_name=strategy_name,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=self.initial_capital,
            config={
                "stop_loss_pct": stop_loss_pct,
                "take_profit_pct": take_profit_pct,
                "risk_per_trade_pct": risk_per_trade_pct,
                "slippage": self._get_slippage(symbol),
                "commission": self.commission
            }
        )

        if len(klines) < 100:
            logger.warning(f"Insufficient data: {len(klines)} klines (need 100+)")
            result.run_time_seconds = time.time() - start_time
            return result

        result.total_candles = len(klines)
        capital = self.initial_capital
        position: Optional[Position] = None
        equity = self.initial_capital

        # Determine if major or alt
        is_major = self._is_major_symbol(symbol)

        # Add warmup period for indicators (first 50 candles)
        warmup = 50

        for i, kline in enumerate(klines):
            current_time = datetime.fromtimestamp(kline.timestamp / 1000)
            current_price = kline.close

            # Update equity for tracking
            if position:
                if position.side == TradeSide.BUY:
                    unrealized_pnl = (current_price - position.entry_price) * position.quantity
                    equity = capital + unrealized_pnl
                else:
                    unrealized_pnl = (position.entry_price - current_price) * position.quantity
                    equity = capital + unrealized_pnl

            # Record equity point (every 10 candles for performance)
            if i % 10 == 0:
                result.equity_curve.append({
                    "timestamp": kline.timestamp,
                    "equity": equity,
                    "position": position is not None
                })

            # Skip warmup period for strategy signals
            if i < warmup:
                continue

            # Get indicator values (for strategies that need them)
            # In a full implementation, calculate RSI, EMA, etc. from recent candles
            rsi = self._calculate_rsi(klines[:i+1]) if i >= 14 else None

            # Call strategy - in real implementation, pass full context
            try:
                signal = strategy_fn(symbol, klines[:i+1], current_price, rsi)
            except Exception as e:
                logger.debug(f"Strategy error at {i}: {e}")
                signal = None

            # Process signals
            if signal == "BUY" and position is None:
                # Open long position
                position_size = self._calculate_position_size(
                    capital, current_price, stop_loss_pct, risk_per_trade_pct
                )

                if position_size <= 0:
                    result.skipped_trades += 1
                    continue

                # Apply slippage
                exec_price = self._apply_slippage(current_price, "BUY", is_major)

                position = Position(
                    entry_time=current_time,
                    entry_price=exec_price,
                    quantity=position_size,
                    side=TradeSide.BUY
                )

                logger.debug(f"BUY at {exec_price}, qty: {position_size}")

            elif signal == "SELL" and position is not None:
                # Close position
                exec_price = self._apply_slippage(current_price, "SELL", is_major)
                comm = self._calculate_commission(exec_price, position.quantity)

                pnl = self._calculate_pnl(position, exec_price)
                pnl_pct = (pnl / (position.entry_price * position.quantity)) * 100

                trade = Trade(
                    entry_time=position.entry_time,
                    exit_time=current_time,
                    entry_price=position.entry_price,
                    exit_price=exec_price,
                    side=position.side,
                    pnl=pnl - comm,
                    pnl_pct=pnl_pct,
                    quantity=position.quantity,
                    commission=comm
                )

                result.trades.append(trade)
                capital += pnl - comm

                logger.debug(f"SELL at {exec_price}, PnL: {pnl - comm:.2f}")

                position = None

            # Check stop loss / take profit for open position
            if position:
                sl_price = position.entry_price * (1 - stop_loss_pct / 100)
                tp_price = position.entry_price * (1 + take_profit_pct / 100)

                if (position.side == TradeSide.BUY and current_price <= sl_price) or \
                   (position.side == TradeSide.BUY and current_price >= tp_price):

                    exec_price = self._apply_slippage(current_price, "SELL", is_major)
                    comm = self._calculate_commission(exec_price, position.quantity)
                    pnl = self._calculate_pnl(position, exec_price)

                    trade = Trade(
                        entry_time=position.entry_time,
                        exit_time=current_time,
                        entry_price=position.entry_price,
                        exit_price=exec_price,
                        side=position.side,
                        pnl=pnl - comm,
                        pnl_pct=(pnl / (position.entry_price * position.quantity)) * 100,
                        quantity=position.quantity,
                        commission=comm
                    )

                    result.trades.append(trade)
                    capital += pnl - comm
                    position = None

        # Close any remaining position at the end
        if position:
            last_kline = klines[-1]
            exec_price = self._apply_slippage(last_kline.close, "SELL", is_major)
            comm = self._calculate_commission(exec_price, position.quantity)
            pnl = self._calculate_pnl(position, exec_price)

            trade = Trade(
                entry_time=position.entry_time,
                exit_time=datetime.fromtimestamp(last_kline.timestamp / 1000),
                entry_price=position.entry_price,
                exit_price=exec_price,
                side=position.side,
                pnl=pnl - comm,
                pnl_pct=(pnl / (position.entry_price * position.quantity)) * 100,
                quantity=position.quantity,
                commission=comm
            )
            result.trades.append(trade)
            capital += pnl - comm

        result.final_capital = capital
        result.total_pnl = capital - self.initial_capital
        result.total_pnl_pct = (result.total_pnl / self.initial_capital) * 100
        result.position = position
        result.run_time_seconds = time.time() - start_time

        logger.info(f"Backtest complete: {len(result.trades)} trades, PnL: {result.total_pnl:.2f} ({result.total_pnl_pct:.2f}%)")

        return result

    def _calculate_rsi(self, klines: List[Any], period: int = 14) -> Optional[float]:
        """Calculate RSI for given klines."""
        if len(klines) < period + 1:
            return None

        closes = [k.close for k in klines]
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]

        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _get_slippage(self, symbol: str) -> float:
        """Get slippage rate based on symbol."""
        return self.slippage_majors if self._is_major_symbol(symbol) else self.slippage_alts

    def _is_major_symbol(self, symbol: str) -> bool:
        """Check if symbol is a major pair."""
        majors = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "BUSDUSDT", "USDCUSDT", "USDTUSDT"]
        return symbol in majors

    def _apply_slippage(self, price: float, side: str, is_major: bool) -> float:
        """Apply slippage to price."""
        slippage = self.slippage_majors if is_major else self.slippage_alts
        if side == "BUY":
            return price * (1 + slippage)
        else:
            return price * (1 - slippage)

    def _calculate_commission(self, price: float, quantity: float) -> float:
        """Calculate commission for trade."""
        return price * quantity * self.commission

    def _calculate_pnl(self, position: Position, exit_price: float) -> float:
        """Calculate PnL for trade."""
        if position.side == TradeSide.BUY:
            return (exit_price - position.entry_price) * position.quantity
        else:
            return (position.entry_price - exit_price) * position.quantity

    def _calculate_position_size(
        self,
        capital: float,
        price: float,
        stop_loss_pct: float,
        risk_pct: float
    ) -> float:
        """Calculate position size based on risk parameters."""
        if stop_loss_pct <= 0:
            return 0

        risk_amount = capital * (risk_pct / 100)
        risk_per_unit = price * (stop_loss_pct / 100)

        if risk_per_unit <= 0:
            return 0

        quantity = risk_amount / risk_per_unit

        # Don't risk more than available capital
        max_qty = capital / price
        return min(quantity, max_qty)