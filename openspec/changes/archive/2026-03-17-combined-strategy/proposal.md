## Why

The current trading strategy relies solely on the Relative Strength Index (RSI). While effective for basic overbought/oversold conditions, relying on a single indicator often leads to false signals in strong trending markets. Implementing a combined strategy that looks for RSI Divergences (when the price makes a new low but the RSI makes a higher low, or vice versa) significantly increases the probability of a successful trade by filtering out "noise" and confirming trend reversals with higher accuracy.

## What Changes

1.  **Divergence Detection Engine**: Develop a new mathematical module within `app/services/indicators.py` capable of identifying recent swing highs and swing lows in both price (klines) and RSI data.
2.  **RSI + Divergence Strategy**: Create a new strategy module (`app/services/divergence_strategy.py` or integrate into a strategy manager) that triggers buy/sell signals *only* when an RSI overbought/oversold condition is accompanied by a confirmed bullish/bearish divergence.
3.  **Strategy Configuration**: Update the configuration layer so the user can seamlessly switch between "RsiOnly" and "RsiWithDivergence" strategies.

## Capabilities

### New Capabilities
- `combined-strategies`: The ability to evaluate multiple technical indicators concurrently (specifically RSI value and Price/RSI Divergence) to generate a unified, high-confidence trading signal.

### Modified Capabilities
- `trading-logic`: The existing trading loop will be modified to support plugging in different strategy classes or evaluating the new divergence checks before placing an order.

## Impact

-   **Indicators Service**: `app/services/indicators.py` will require new methods to analyze historical data structures (swing highs/lows) rather than just the latest closing price.
-   **Main Loop**: `app/main.py` and `trading_engine.py` might need minor refactoring to support strategy injection or enhanced configuration.
-   **Data Storage**: `SymbolData` needs to store a few recent swing points or calculate them on the fly from the deque of klines.
