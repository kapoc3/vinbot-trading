"""
Strategy comparison and parameter sweep functionality.
"""
import logging
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass

from app.services.backtest.data_fetcher import HistoricalDataFetcher
from app.services.backtest.engine import BacktestEngine, BacktestResult
from app.services.backtest.metrics import calculate_metrics

logger = logging.getLogger(__name__)


@dataclass
class StrategyComparison:
    """Result of comparing multiple strategies."""
    results: List[BacktestResult]
    metrics: List[Dict[str, Any]]
    rankings: List[Dict[str, Any]]
    best_strategy: Optional[str]


def compare_strategies(
    strategies: List[Dict[str, Any]],
    symbol: str,
    start_date: str,
    end_date: str,
    interval: str = "1h",
    engine_config: Optional[Dict[str, Any]] = None
) -> StrategyComparison:
    """
    Compare multiple strategies side-by-side.

    Args:
        strategies: List of dicts with 'name' and 'fn' (strategy function)
        symbol: Trading symbol
        start_date: Start date
        end_date: End date
        interval: Timeframe
        engine_config: Optional config for engine

    Returns:
        StrategyComparison with all results
    """
    # Fetch data once
    fetcher = HistoricalDataFetcher()
    klines = fetcher.fetch_klines(symbol, interval, start_date, end_date)

    if not klines:
        raise ValueError("No data fetched")

    # Initialize engine
    config = engine_config or {}
    engine = BacktestEngine(
        initial_capital=config.get('initial_capital'),
        slippage_majors=config.get('slippage_majors', 0.001),
        slippage_alts=config.get('slippage_alts', 0.002),
        commission=config.get('commission', 0.001)
    )

    results = []
    metrics_list = []

    # Run each strategy
    for strategy in strategies:
        name = strategy.get('name', 'Strategy')
        fn = strategy.get('fn')

        logger.info(f"Running backtest for: {name}")

        result = engine.run(
            strategy_fn=fn,
            klines=klines,
            symbol=symbol,
            strategy_name=name,
            timeframe=interval,
            start_date=start_date,
            end_date=end_date,
            stop_loss_pct=config.get('stop_loss_pct', 2.0),
            take_profit_pct=config.get('take_profit_pct', 5.0),
            risk_per_trade_pct=config.get('risk_per_trade_pct', 1.0)
        )

        results.append(result)
        metrics_list.append(calculate_metrics(result))

    # Calculate rankings
    rankings = _calculate_rankings(results, metrics_list)

    # Find best
    best = rankings[0]['strategy_name'] if rankings else None

    return StrategyComparison(
        results=results,
        metrics=metrics_list,
        rankings=rankings,
        best_strategy=best
    )


def parameter_sweep(
    strategy_fn: Callable,
    symbol: str,
    param_grid: Dict[str, List[Any]],
    start_date: str,
    end_date: str,
    interval: str = "1h"
) -> Dict[str, Any]:
    """
    Perform parameter sweep for a strategy.

    Args:
        strategy_fn: Strategy function (needs to accept parameters)
        symbol: Trading symbol
        param_grid: Dict of parameter names to values to test
        start_date: Start date
        end_date: End date
        interval: Timeframe

    Returns:
        Best parameters and all results
    """
    import itertools

    # Generate all parameter combinations
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    combinations = list(itertools.product(*param_values))

    logger.info(f"Testing {len(combinations)} parameter combinations")

    fetcher = HistoricalDataFetcher()
    klines = fetcher.fetch_klines(symbol, interval, start_date, end_date)

    if not klines:
        raise ValueError("No data fetched")

    engine = BacktestEngine()
    all_results = []

    for combo in combinations:
        params = dict(zip(param_names, combo))

        # Create wrapped strategy function that applies params
        def make_fn(p):
            def wrapped(symbol, klines, price, rsi):
                return strategy_fn(symbol, klines, price, rsi, **p)
            return wrapped

        result = engine.run(
            strategy_fn=make_fn(params),
            klines=klines,
            symbol=symbol,
            strategy_name=str(params),
            timeframe=interval,
            start_date=start_date,
            end_date=end_date
        )

        metrics = calculate_metrics(result)
        all_results.append({
            'params': params,
            'result': result,
            'metrics': metrics
        })

    # Find best by ranking score
    best_result = max(all_results, key=lambda x: _ranking_score(x['metrics']))

    return {
        'best_params': best_result['params'],
        'best_metrics': best_result['metrics'],
        'all_results': all_results
    }


def _calculate_rankings(
    results: List[BacktestResult],
    metrics: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Calculate ranking scores for strategies."""
    rankings = []

    for result, metric in zip(results, metrics):
        score = _ranking_score(metric)

        rankings.append({
            'strategy_name': result.strategy_name,
            'total_pnl': metric['total_pnl'],
            'total_pnl_pct': metric['total_pnl_pct'],
            'win_rate': metric['win_rate'],
            'sharpe_ratio': metric['sharpe_ratio'],
            'max_drawdown': metric['max_drawdown'],
            'profit_factor': metric['profit_factor'],
            'total_trades': metric['total_trades'],
            'ranking_score': score
        })

    # Sort by ranking score (descending)
    rankings.sort(key=lambda x: x['ranking_score'], reverse=True)

    return rankings


def _ranking_score(metrics: Dict[str, Any]) -> float:
    """
    Calculate weighted ranking score.

    Weights:
    - 30% Sharpe Ratio
    - 30% Total PnL %
    - 20% Win Rate
    - 20% Drawdown (inverted - lower is better)
    """
    sharpe = metrics.get('sharpe_ratio', 0) or 0
    pnl_pct = metrics.get('total_pnl_pct', 0) or 0
    win_rate = metrics.get('win_rate', 0) or 0
    drawdown = metrics.get('max_drawdown', 0) or 0

    # Normalize values for scoring
    sharpe_score = max(0, sharpe)  # Can be negative
    pnl_score = max(0, pnl_pct)    # Only positive PnL counts
    win_score = win_rate / 100     # 0 to 1

    # Invert drawdown (lower is better, so 100 - drawdown)
    drawdown_score = max(0, 100 - drawdown) / 100

    # Weighted sum
    score = (
        0.30 * sharpe_score +
        0.30 * pnl_score +
        0.20 * win_score +
        0.20 * drawdown_score
    )

    return score


def format_comparison(comparison: StrategyComparison) -> str:
    """Format comparison results as string."""
    lines = [
        "=== Strategy Comparison ===",
        f"Best Strategy: {comparison.best_strategy}",
        ""
    ]

    for rank in comparison.rankings:
        lines.extend([
            f"--- {rank['strategy_name']} ---",
            f"  PnL: ${rank['total_pnl']:.2f} ({rank['total_pnl_pct']:.2f}%)",
            f"  Win Rate: {rank['win_rate']:.1f}%",
            f"  Sharpe: {rank['sharpe_ratio']:.2f}",
            f"  Max DD: {rank['max_drawdown']:.2f}%",
            f"  Trades: {rank['total_trades']}",
            f"  Ranking Score: {rank['ranking_score']:.3f}",
            ""
        ])

    return "\n".join(lines)