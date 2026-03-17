## 1. Indicator Layer (Core Math)

- [x] 1.1 Implement a local extrema algorithm (`find_local_extrema`) in `app/services/indicators.py` capable of returning swing highs/lows for an arbitrary array given a lookback window.
- [x] 1.2 Implement a divergence detection utility (`check_divergence`) in `app/services/indicators.py` that compares recent price swings against recent RSI swings to identify Bullish or Bearish Regular Divergences.
- [x] 1.3 Update `SymbolData` in `indicators.py` to maintain a sufficient queue of data (at least 100 historical prices AND corresponding RSIs) to calculate swings accurately.

## 2. Strategy Engine Layer

- [x] 2.1 Refactor config settings (`app/core/config.py`) to add `.env` support for `TRADING_STRATEGY` (default: "RsiOnly").
- [x] 2.2 Create `RsiDivergenceStrategy` class with a `evaluate_signal` method that implements the dual RSI + Divergence conditions.
- [x] 2.3 Refactor the existing hardcoded RSI logic from `app/main.py` into a standardized `RSIStrategy` class, making them adhere to a common interface.

## 3. Trading Loop Integration

- [x] 3.1 Update `app/main.py` entrypoint and `trading_engine.py` (if applicable) to dynamically load the selected strategy based on `settings.TRADING_STRATEGY`.
- [x] 3.2 Add related logging traces to output when a divergence rule has specifically filtered out a trade or confirmed it.
