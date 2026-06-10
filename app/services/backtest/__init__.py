"""
Backtesting module for VinBot Trading.
"""
from app.services.backtest.data_fetcher import HistoricalDataFetcher
from app.services.backtest.engine import BacktestEngine, BacktestResult
from app.services.backtest.metrics import calculate_metrics
from app.services.backtest.comparison import compare_strategies
from app.services.backtest.reporter import generate_report, save_report

__all__ = [
    "HistoricalDataFetcher",
    "BacktestEngine",
    "BacktestResult",
    "calculate_metrics",
    "compare_strategies",
    "generate_report",
    "save_report"
]