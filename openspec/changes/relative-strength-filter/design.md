# Design: Relative Strength Filter

## Overview
This feature introduces a global interceptor in the `StrategyFactory` that will evaluate the relative performance of any altcoin generating a `BUY` signal against Bitcoin before approving the trade.

## Technical Modifications

1.  **Configuration (`app/core/config.py`):**
    *   Add `ENABLE_RELATIVE_STRENGTH_FILTER: bool = True`.
    *   Add `RS_LOOKBACK_PERIOD: int = 14` (The number of candles to use for the Rate of Change comparison).

2.  **Relative Strength Calculation (`app/services/indicators.py`):**
    *   Add a method `get_roc(period)` to the `SymbolData` class to calculate the Rate of Change: `((Current_Close - Close_N_Periods_Ago) / Close_N_Periods_Ago) * 100`.

3.  **Veto Logic (`app/services/strategy_factory.py`):**
    *   In `DynamicStrategyProxy.analyze()`:
        *   If `signal == "BUY"` and the symbol is not `"BTCUSDT"` (or any stablecoin pair, though handled implicitly):
        *   Retrieve the altcoin's `SymbolData`.
        *   Retrieve `BTCUSDT`'s `SymbolData`.
        *   Calculate `altcoin_roc = altcoin_data.get_roc(RS_LOOKBACK_PERIOD)`.
        *   Calculate `btc_roc = btc_data.get_roc(RS_LOOKBACK_PERIOD)`.
        *   If `altcoin_roc < btc_roc`: Log a veto message and return `None`.

4.  **Dependencies & Edge Cases:**
    *   Since BTC is the benchmark, `BTCUSDT` data must always be actively collected. The previous `BTC Directional Filter` feature already ensured `BTCUSDT` is tracked if enabled. We must update `main.py` so that `BTCUSDT` is added to the ticker stream if *either* `ENABLE_BTC_DIRECTIONAL_FILTER` *or* `ENABLE_RELATIVE_STRENGTH_FILTER` is active.
    *   If there isn't enough historical data (e.g., `< RS_LOOKBACK_PERIOD` candles accumulated upon startup), the filter should bypass safely or veto locally until enough data buffers. Vetoing is safer.
