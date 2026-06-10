"""
Backtest API endpoints.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.backtest import (
    HistoricalDataFetcher,
    BacktestEngine,
    calculate_metrics,
    compare_strategies,
    generate_report,
    save_report
)

logger = logging.getLogger(__name__)
router = APIRouter()


class BacktestRequest(BaseModel):
    """Request model for backtest endpoint."""
    symbol: str = "BTCUSDT"
    strategy: str = "rsi"  # rsi, bollinger, macd, breakout
    start_date: str = "2024-01-01"
    end_date: str = "2024-12-31"
    interval: str = "1h"
    initial_capital: float = 1000.0
    stop_loss_pct: float = 2.0
    take_profit_pct: float = 5.0
    risk_per_trade_pct: float = 1.0
    output_file: Optional[str] = None


class CompareRequest(BaseModel):
    """Request model for comparison endpoint."""
    symbol: str = "BTCUSDT"
    strategies: list[str] = ["rsi", "bollinger", "macd"]
    start_date: str = "2024-01-01"
    end_date: str = "2024-12-31"
    interval: str = "1h"
    initial_capital: float = 1000.0


# Strategy functions
STRATEGIES = {
    "rsi": lambda symbol, klines, price, rsi: (
        "BUY" if rsi and rsi < 30 else ("SELL" if rsi and rsi > 70 else None)
    ),
    "bollinger": lambda symbol, klines, price, rsi: _bollinger_strategy,
    "macd": lambda symbol, klines, price, rsi: _macd_strategy,
    "breakout": lambda symbol, klines, price, rsi: _breakout_strategy,
}


def _bollinger_strategy(symbol, klines, price, rsi):
    """Bollinger Bands strategy."""
    if len(klines) < 20:
        return None

    closes = [k.close for k in klines[-20:]]
    sma = sum(closes) / 20
    std = (sum((c - sma) ** 2 for c in closes) / 20) ** 0.5
    lower = sma - 2 * std
    upper = sma + 2 * std

    if price < lower and rsi and rsi < 40:
        return "BUY"
    elif price > upper and rsi and rsi > 60:
        return "SELL"
    return None


def _macd_strategy(symbol, klines, price, rsi):
    """Simple MACD-like strategy."""
    if len(klines) < 26:
        return None

    ema12 = _ema([k.close for k in klines], 12)
    ema26 = _ema([k.close for k in klines], 26)

    if ema12 and ema26:
        if ema12 > ema26 * 1.01:  # Bullish cross
            return "BUY"
        elif ema12 < ema26 * 0.99:  # Bearish cross
            return "SELL"
    return None


def _breakout_strategy(symbol, klines, price, rsi):
    """Volatility breakout strategy."""
    if len(klines) < 20:
        return None

    highs = [k.high for k in klines[-20:]]
    max_high = max(highs)

    if price > max_high * 1.02:  # New high breakout
        return "BUY"
    elif price < min([k.low for k in klines[-20:]]) * 0.98:  # New low
        return "SELL"
    return None


def _ema(values: list, period: int) -> Optional[float]:
    """Calculate EMA."""
    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)
    ema = values[0]

    for value in values[1:]:
        ema = (value * multiplier) + (ema * (1 - multiplier))

    return ema


@router.post("/run")
async def run_backtest(request: BacktestRequest):
    """Run a backtest."""
    try:
        # Get strategy function
        strategy_fn = STRATEGIES.get(request.strategy)
        if not strategy_fn:
            raise HTTPException(f"Unknown strategy: {request.strategy}")

        # Fetch historical data
        fetcher = HistoricalDataFetcher()
        klines = fetcher.fetch_klines(
            request.symbol,
            request.interval,
            request.start_date,
            request.end_date
        )

        if not klines:
            raise HTTPException("No data fetched")

        # Run backtest
        engine = BacktestEngine(initial_capital=request.initial_capital)
        result = engine.run(
            strategy_fn=strategy_fn,
            klines=klines,
            symbol=request.symbol,
            strategy_name=request.strategy.upper(),
            timeframe=request.interval,
            start_date=request.start_date,
            end_date=request.end_date,
            stop_loss_pct=request.stop_loss_pct,
            take_profit_pct=request.take_profit_pct,
            risk_per_trade_pct=request.risk_per_trade_pct
        )

        # Calculate metrics
        metrics = calculate_metrics(result)

        # Generate report if requested
        report_html = None
        if request.output_file:
            save_report(result, request.output_file)
            report_html = generate_report(result)

        return {
            "status": "success",
            "result": {
                "strategy": result.strategy_name,
                "symbol": result.symbol,
                "start_date": result.start_date,
                "end_date": result.end_date,
                "trades": len(result.trades),
                "metrics": metrics,
                "output_file": request.output_file
            }
        }

    except Exception as e:
        logger.error(f"Backtest error: {e}")
        raise HTTPException(f"Backtest failed: {str(e)}")


@router.post("/compare")
async def compare(request: CompareRequest):
    """Compare multiple strategies."""
    try:
        # Build strategy list
        strategies = []
        for name in request.strategies:
            fn = STRATEGIES.get(name)
            if fn:
                strategies.append({"name": name.upper(), "fn": fn})

        if not strategies:
            raise HTTPException("No valid strategies provided")

        # Run comparison
        comparison = compare_strategies(
            strategies=strategies,
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            interval=request.interval,
            engine_config={"initial_capital": request.initial_capital}
        )

        return {
            "status": "success",
            "best_strategy": comparison.best_strategy,
            "rankings": comparison.rankings
        }

    except Exception as e:
        logger.error(f"Comparison error: {e}")
        raise HTTPException(f"Comparison failed: {str(e)}")


@router.get("/strategies")
async def list_strategies():
    """List available strategies."""
    return {
        "strategies": list(STRATEGIES.keys())
    }