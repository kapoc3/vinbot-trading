## Why

The autonomous regime switching engine currently relies on the default `RSIStrategy` when it detects a ranging/lateral market. While the RSI indicator is useful for identifying overbought and oversold conditions, it only considers absolute momentum levels. In ranging markets, price tends to oscillate within dynamic boundaries. Introducing Bollinger Bands (which calculate standard deviations away from a moving average) will provide a more precise and adaptable measure of support and resistance during these lateral phases, improving entry precision and win rates.

## What Changes

- **Indicator Expansion**: Implementing the mathematical logic for Bollinger Bands (Simple Moving Average and Upper/Lower Bands based on standard deviations) within our indicator layer.
- **Strategy Implementation**: Creating a specific `BollingerBandsStrategy` that triggers buy signals when the price touches or crosses below the lower band while the RSI is oversold, and looks to exit near the middle/upper band.
- **Auto Mode Integration**: Updating the dynamic strategy orchestrator so that it prioritizes the `BollingerBandsStrategy` over the basic `RSIStrategy` when a ranging regime is detected by the `RegimeService`.

## Capabilities

### New Capabilities
- None. (We are expanding existing capabilities rather than creating entirely new autonomous domains).

### Modified Capabilities
- `technical-indicators`: Must now support the calculation and storage of Bollinger Bands (SMA 20, StdDev 2) points.
- `trading-logic`: Must include the new strategy in the `StrategyFactory` and use it as the preferred strategy for ranging regimes in `Auto` mode.

## Impact

- **Code Affected**: 
  - `app/services/indicators.py` (Bollinger calculations and `SymbolData` updates).
  - `app/services/strategy_factory.py` (New strategy integration).
  - A new file `app/services/bollinger_strategy.py` will be created.
- **Execution Engine**: No major changes required, as the Strategy interface will be honored.
- **Performance**: Negligible impact on calculation load.
