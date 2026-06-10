"""
Metrics calculation for backtest results.
"""
import logging
from typing import Dict, Any, List
from datetime import timedelta

from app.services.backtest.engine import BacktestResult, Trade

logger = logging.getLogger(__name__)


def calculate_metrics(result: BacktestResult) -> Dict[str, Any]:
    """
    Calculate comprehensive metrics from backtest result.

    Returns:
        Dictionary with all calculated metrics
    """
    if not result.trades:
        return _empty_metrics(result)

    trades = result.trades
    metrics = {}

    # Basic metrics
    metrics['total_pnl'] = result.total_pnl
    metrics['total_pnl_pct'] = result.total_pnl_pct
    metrics['final_capital'] = result.final_capital

    # Trade counts
    winning_trades = [t for t in trades if t.pnl > 0]
    losing_trades = [t for t in trades if t.pnl <= 0]

    metrics['total_trades'] = len(trades)
    metrics['winning_trades'] = len(winning_trades)
    metrics['losing_trades'] = len(losing_trades)

    # Win rate
    metrics['win_rate'] = (len(winning_trades) / len(trades) * 100) if trades else 0

    # Profit factor
    gross_profit = sum(t.pnl for t in winning_trades) if winning_trades else 0
    gross_loss = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 0
    metrics['profit_factor'] = gross_profit / gross_loss if gross_loss > 0 else float('inf')

    # Average trade
    metrics['avg_trade'] = result.total_pnl / len(trades) if trades else 0
    metrics['avg_win'] = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
    metrics['avg_loss'] = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0

    # Expectancy
    win_rate_dec = metrics['win_rate'] / 100
    loss_rate = 1 - win_rate_dec
    metrics['expectancy'] = (win_rate_dec * metrics['avg_win']) - (loss_rate * abs(metrics['avg_loss'])) if metrics['avg_loss'] != 0 else 0

    # Drawdown
    metrics['max_drawdown'] = _calculate_max_drawdown(result.equity_curve)
    metrics['current_drawdown'] = _calculate_current_drawdown(result.equity_curve)

    # Sharpe Ratio (simplified)
    metrics['sharpe_ratio'] = _calculate_sharpe_ratio(trades)

    # Trade duration
    durations = [(t.exit_time - t.entry_time).total_seconds() / 3600 for t in trades]
    metrics['avg_trade_duration_hours'] = sum(durations) / len(durations) if durations else 0
    metrics['max_trade_duration_hours'] = max(durations) if durations else 0
    metrics['min_trade_duration_hours'] = min(durations) if durations else 0

    # Consecutive wins/losses
    metrics['max_consecutive_wins'] = _max_consecutive(trades, positive=True)
    metrics['max_consecutive_losses'] = _max_consecutive(trades, positive=False)

    # Commission total
    metrics['total_commission'] = sum(t.commission for t in trades)

    # Annualized return
    days = (result.trades[-1].exit_time - result.trades[0].entry_time).days if len(result.trades) > 1 else 1
    metrics['annualized_return_pct'] = (result.total_pnl_pct / days * 365) if days > 0 else 0

    return metrics


def _empty_metrics(result: BacktestResult) -> Dict[str, Any]:
    """Return empty metrics when no trades."""
    return {
        'total_pnl': 0,
        'total_pnl_pct': 0,
        'final_capital': result.initial_capital,
        'total_trades': 0,
        'winning_trades': 0,
        'losing_trades': 0,
        'win_rate': 0,
        'profit_factor': 0,
        'avg_trade': 0,
        'avg_win': 0,
        'avg_loss': 0,
        'expectancy': 0,
        'max_drawdown': 0,
        'current_drawdown': 0,
        'sharpe_ratio': 0,
        'avg_trade_duration_hours': 0,
        'max_consecutive_wins': 0,
        'max_consecutive_losses': 0,
        'total_commission': 0,
        'annualized_return_pct': 0
    }


def _calculate_max_drawdown(equity_curve: List[Dict[str, Any]]) -> float:
    """Calculate maximum drawdown from equity curve."""
    if not equity_curve:
        return 0

    peak = equity_curve[0]['equity']
    max_dd = 0

    for point in equity_curve:
        equity = point['equity']
        if equity > peak:
            peak = equity

        drawdown = ((peak - equity) / peak * 100) if peak > 0 else 0
        max_dd = max(max_dd, drawdown)

    return max_dd


def _calculate_current_drawdown(equity_curve: List[Dict[str, Any]]) -> float:
    """Calculate current drawdown."""
    if not equity_curve:
        return 0

    peak = max(p['equity'] for p in equity_curve)
    current = equity_curve[-1]['equity']

    return ((peak - current) / peak * 100) if peak > 0 else 0


def _calculate_sharpe_ratio(trades: List[Trade], risk_free_rate: float = 0.02) -> float:
    """Calculate Sharpe ratio from trades."""
    if len(trades) < 2:
        return 0

    # Calculate daily returns
    # For simplicity, treat each trade as one "period"
    returns = [t.pnl_pct / 100 for t in trades]

    if not returns:
        return 0

    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    std_dev = variance ** 0.5

    if std_dev == 0:
        return 0

    sharpe = (mean_return - risk_free_rate) / std_dev
    # Annualize (assuming ~252 trading days, but trades are irregular)
    # For simplicity, just return the raw sharpe
    return sharpe


def _max_consecutive(trades: List[Trade], positive: bool = True) -> int:
    """Calculate maximum consecutive wins or losses."""
    if not trades:
        return 0

    max_count = 0
    current_count = 0

    for trade in trades:
        is_positive = trade.pnl > 0

        if positive and is_positive:
            current_count += 1
            max_count = max(max_count, current_count)
        elif not positive and not is_positive:
            current_count += 1
            max_count = max(max_count, current_count)
        else:
            current_count = 0

    return max_count


def format_metrics(metrics: Dict[str, Any]) -> str:
    """Format metrics as a readable string."""
    lines = [
        "=== Backtest Results ===",
        f"Total PnL: ${metrics['total_pnl']:.2f} ({metrics['total_pnl_pct']:.2f}%)",
        f"Win Rate: {metrics['win_rate']:.1f}%",
        f"Profit Factor: {metrics['profit_factor']:.2f}",
        f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}",
        f"Max Drawdown: {metrics['max_drawdown']:.2f}%",
        f"Total Trades: {metrics['total_trades']}",
        f"  Winners: {metrics['winning_trades']}",
        f"  Losers: {metrics['losing_trades']}",
        f"Avg Trade: ${metrics['avg_trade']:.2f}",
        f"Expectancy: ${metrics['expectancy']:.2f}",
    ]
    return "\n".join(lines)