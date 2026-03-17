## Why

Current bot logic requires manual selection of strategies (via `.env`). However, market conditions are dynamic; a strategy that works well in a ranging market (like pure RSI) often fails during a strong trend, and a trend-following or divergence-based strategy might be too slow in a choppy lateral market. To achieve true autonomy, the bot must be able to classify the current "Market Regime" and automatically switch to the most appropriate strategy.

## What Changes

- **Regime Classification Engine**: Implementation of advanced indicators (ADX for trend strength, ATR for volatility) to establish market "states" (e.g., Trending, Choppy, Volatile).
- **Autonomous Strategy Orchestrator**: A new management layer that periodically re-evaluates the market regime and updates the active strategy instance in the main loop.
- **Dynamic Configuration**: Support for environment-based "auto-mode" settings, allowing the user to toggle between manual strategy selection and fully autonomous switching.

## Capabilities

### New Capabilities
- `market-regime-analyzer`: The system SHALL be able to identify the current market state (Strong Trend, Ranging, High Volatility) based on a combination of trailing indicators (ADX/ATR).
- `dynamic-strategy-orchestration`: The engine SHALL support switching the active trading strategy instance at runtime without requiring a service restart.

### Modified Capabilities
- `trading-logic`: Requirements for selecting a strategy will change from a startup-only static factory to a runtime-re-evaluated selection process.

## Impact

- **Indicators Service**: `app/services/indicators.py` will need mathematical implementations for ADX and ATR.
- **Strategy Factory**: `app/services/strategy_factory.py` will be expanded or superseded by a dynamic manager.
- **Main Loop**: The kline callback in `app.main` will need to account for potential strategy swaps between candles.
- **Observability**: New metrics to track the "current active regime" to visualize bot decisions in Grafana.
