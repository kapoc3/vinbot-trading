## 1. Indicator Mathematics

- [x] 1.1 Implement `calculate_ema(prices, period)` in `TechnicalIndicators`.
- [x] 1.2 Implement `calculate_macd(prices, ...)` in `TechnicalIndicators`.
- [x] 1.3 Add `get_macd()` and `get_ema()` helpers to `SymbolData`.

## 2. Strategy Development

- [x] 2.1 Create `app/services/macd_strategy.py`.
- [x] 2.2 Implement `MacdMaCrossStrategy` with EMA 200 filter logic.
- [x] 2.3 Implement entry/exit signal conditions (MACD Signal Line Cross).

## 3. Orchestration & Tuning

- [x] 3.1 Register `MacdMaCrossStrategy` in `StrategyManager`.
- [x] 3.2 Update `re_evaluate_regime` to utilize MACD in high-strength trends.
- [x] 3.3 (Verification) Increase default `maxlen` for `SymbolData` to 500 to support EMA 200 stability.

## 4. Documentation & Testing

- [x] 4.1 Create test script `/tmp/test_macd.py`.
- [x] 4.2 Update `CHANGELOG.md` with the new strategy capability.
