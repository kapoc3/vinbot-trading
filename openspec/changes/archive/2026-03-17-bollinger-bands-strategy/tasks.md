## 1. Indicator Enhancements

- [x] 1.1 Implement Bollinger Bands calculation (SMA 20, StdDev 2) in `app/services/indicators.py` within the `TechnicalIndicators` class.
- [x] 1.2 Update `SymbolData` class to maintain history state and expose a helper method `get_bollinger_bands()` to easily retrieve the Upper Band, Middle Band (SMA), and Lower Band.

## 2. Strategy Implementation

- [x] 2.1 Create a new strategy file `app/services/bollinger_strategy.py`.
- [x] 2.2 Implement the `BollingerBandsStrategy` class, adhering to the base structure (inheriting common methods or reusing existing patterns).
- [x] 2.3 Implement the entry logic in `BollingerBandsStrategy.analyze()` to trigger a Buy signal when `price < lower_band` AND `rsi < 30`.
- [x] 2.4 Implement basic exit logic (e.g., exiting when `price > middle_band` or `price > upper_band`).

## 3. Auto Mode Orchestration

- [x] 3.1 Refactor `StrategyManager.re_evaluate_regime` in `app/services/strategy_factory.py`.
- [x] 3.2 Ensure that when `MarketRegime` is `RANGING`, the `BollingerBandsStrategy` is selected instead of `RSIStrategy`.
- [x] 3.3 Ensure the `StrategyManager` instantiates and caches the `BollingerBandsStrategy` properly.

## 4. Configuration and Observability (Optional)

- [x] 4.1 Update `.env.example` and `app/core/config.py` to document the new `BollingerBands` available strategy.
- [x] 4.2 Validate that metrics (like PnL and order counters) automatically work with the newly deployed strategy.
