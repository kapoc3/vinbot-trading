"""
CLI commands for backtesting.
"""
import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.backtest import (
    HistoricalDataFetcher,
    BacktestEngine,
    calculate_metrics,
    compare_strategies,
    generate_report,
    save_report
)
from app.services.backtest.engine import TradeSide

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Simple strategy implementations for CLI
def rsi_strategy(symbol, klines, price, rsi, **kwargs):
    """RSI strategy: BUY when oversold, SELL when overbought."""
    if rsi and rsi < 30:
        return "BUY"
    elif rsi and rsi > 70:
        return "SELL"
    return None


def bollinger_strategy(symbol, klines, price, rsi, **kwargs):
    """Bollinger Bands strategy."""
    if len(klines) < 20:
        return None

    closes = [k.close for k in klines[-20:]]
    sma = sum(closes) / 20
    std = (sum((c - sma) ** 2 for c in closes) / 20) ** 0.5
    lower = sma - 2 * std

    if price < lower and rsi and rsi < 40:
        return "BUY"
    elif rsi and rsi > 70:
        return "SELL"
    return None


STRATEGIES = {
    "rsi": rsi_strategy,
    "bollinger": bollinger_strategy,
    "macd": lambda s, k, p, r, **kwa: None,  # Placeholder
    "breakout": lambda s, k, p, r, **kwa: None,  # Placeholder
}


def run_backtest(args):
    """Run a single backtest."""
    logger.info(f"Running backtest: {args.strategy} on {args.symbol}")

    # Fetch data
    fetcher = HistoricalDataFetcher()
    klines = fetcher.fetch_klines(
        args.symbol,
        args.interval,
        args.start_date,
        args.end_date
    )

    if not klines:
        logger.error("No data fetched")
        return

    logger.info(f"Fetched {len(klines)} klines")

    # Get strategy
    strategy_fn = STRATEGIES.get(args.strategy)
    if not strategy_fn:
        logger.error(f"Unknown strategy: {args.strategy}")
        return

    # Run backtest
    engine = BacktestEngine(
        initial_capital=args.initial_capital,
        slippage_majors=0.001,
        slippage_alts=0.002,
        commission=0.001
    )

    result = engine.run(
        strategy_fn=strategy_fn,
        klines=klines,
        symbol=args.symbol,
        strategy_name=args.strategy.upper(),
        timeframe=args.interval,
        start_date=args.start_date,
        end_date=args.end_date,
        stop_loss_pct=args.stop_loss,
        take_profit_pct=args.take_profit,
        risk_per_trade_pct=args.risk
    )

    # Print results
    metrics = calculate_metrics(result)

    print("\n" + "=" * 50)
    print(f"BACKTEST RESULTS: {args.strategy.upper()}")
    print("=" * 50)
    print(f"Symbol: {args.symbol} | Timeframe: {args.interval}")
    print(f"Period: {args.start_date} to {args.end_date}")
    print(f"Initial Capital: ${args.initial_capital:.2f}")
    print("-" * 50)
    print(f"Total PnL: ${metrics['total_pnl']:.2f} ({metrics['total_pnl_pct']:.2f}%)")
    print(f"Final Capital: ${metrics['final_capital']:.2f}")
    print(f"Win Rate: {metrics['win_rate']:.1f}%")
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Winners: {metrics['winning_trades']} | Losers: {metrics['losing_trades']}")
    print("=" * 50)

    # Save report if requested
    if args.output:
        save_report(result, args.output)
        print(f"\nReport saved to: {args.output}")


def compare_strategies_cli(args):
    """Compare multiple strategies."""
    logger.info(f"Comparing strategies: {args.strategies}")

    # Build strategy list
    strategies = []
    for name in args.strategies:
        fn = STRATEGIES.get(name)
        if fn:
            strategies.append({"name": name.upper(), "fn": fn})

    if not strategies:
        logger.error("No valid strategies")
        return

    # Run comparison
    comparison = compare_strategies(
        strategies=strategies,
        symbol=args.symbol,
        start_date=args.start_date,
        end_date=args.end_date,
        interval=args.interval,
        engine_config={"initial_capital": args.initial_capital}
    )

    # Print results
    print("\n" + "=" * 50)
    print("STRATEGY COMPARISON")
    print("=" * 50)
    print(f"Symbol: {args.symbol} | Period: {args.start_date} to {args.end_date}")
    print("-" * 50)

    for rank in comparison.rankings:
        print(f"\n#{comparison.rankings.index(rank) + 1} {rank['strategy_name']}")
        print(f"   PnL: ${rank['total_pnl']:.2f} ({rank['total_pnl_pct']:.2f}%)")
        print(f"   Win Rate: {rank['win_rate']:.1f}%")
        print(f"   Sharpe: {rank['sharpe_ratio']:.2f}")
        print(f"   Max DD: {rank['max_drawdown']:.2f}%")
        print(f"   Ranking Score: {rank['ranking_score']:.3f}")

    print("\n" + "=" * 50)
    print(f"🏆 BEST STRATEGY: {comparison.best_strategy}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="VinBot Backtesting CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Run backtest
    run_parser = subparsers.add_parser("run", help="Run backtest")
    run_parser.add_argument("--strategy", "-s", default="rsi", choices=list(STRATEGIES.keys()))
    run_parser.add_argument("--symbol", "-S", default="BTCUSDT")
    run_parser.add_argument("--interval", "-i", default="1h")
    run_parser.add_argument("--start-date", default="2024-01-01")
    run_parser.add_argument("--end-date", default="2024-12-31")
    run_parser.add_argument("--capital", "-c", type=float, default=1000.0)
    run_parser.add_argument("--stop-loss", type=float, default=2.0)
    run_parser.add_argument("--take-profit", type=float, default=5.0)
    run_parser.add_argument("--risk", type=float, default=1.0)
    run_parser.add_argument("--output", "-o", help="Output HTML report path")

    # Compare strategies
    compare_parser = subparsers.add_parser("compare", help="Compare strategies")
    compare_parser.add_argument("--strategies", nargs="+", default=["rsi", "bollinger"])
    compare_parser.add_argument("--symbol", "-S", default="BTCUSDT")
    compare_parser.add_argument("--interval", "-i", default="1h")
    compare_parser.add_argument("--start-date", default="2024-01-01")
    compare_parser.add_argument("--end-date", default="2024-12-31")
    compare_parser.add_argument("--capital", "-c", type=float, default=1000.0)

    args = parser.parse_args()

    if args.command == "run":
        run_backtest(args)
    elif args.command == "compare":
        compare_strategies_cli(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()