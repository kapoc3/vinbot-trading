## Why

The bot currently uses the `RsiDivergenceStrategy` for trending markets. While effective, RSI-based trend following can be late or sensitive to small pullbacks. The MACD (Moving Average Convergence Divergence) combined with Exponential Moving Average (EMA) crossovers is a industry-standard trend-following system that better filters out short-term noise and manages longer-term momentum. Adding this capability will provide a more "traditional" and robust option for the `TRENDING` market regime.

## What Changes

- **Indicator Expansion**: Implementing EMA (Exponential Moving Average) and MACD (MACD line, Signal line, and Histogram) calculations in the `TechnicalIndicators` class.
- **Strategy Implementation**: Developing a `MacdMaCrossStrategy` that uses:
  - EMA 200 for long-term trend direction (filter).
  - MACD Signal line crossover for entry/exit timing.
- **Auto Mode Integration**: Updating the `StrategyManager` to support this new strategy and optionally allowing it to be the primary strategy for the `TRENDING` regime.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `technical-indicators`: Add support for EMA and MACD calculations.
- `trading-logic`: Integrate the new MACD-based strategy into the factory and auto-switching logic.

## Impact

- **Code Affected**: 
  - `app/services/indicators.py`: New math for EMA/MACD.
  - `app/services/strategy_factory.py`: Integration of the new strategy.
  - `app/services/macd_strategy.py`: New strategy file.
- **Performance**: High (requires calculation of EMAs which are recursive, but 150-200 points of history is manageable).
