## 1. Configuration & Initialization
- [x] 1.1 Add `ENABLE_BTC_DIRECTIONAL_FILTER: bool = True` and `BTC_DIRECTION_EMA: int = 200` to `app/core/config.py`.
- [x] 1.2 In `app/main.py`, modify the initialization loop to automatically append `"BTCUSDT"` to the internal symbols list if `ENABLE_BTC_DIRECTIONAL_FILTER` is True, ensuring data collection for BTC is always active.

## 2. Global Veto Logic
- [x] 2.1 Ensure `SymbolData.get_ema(period)` is fully functional in `app/services/indicators.py` to allow passing any arbitrary EMA period.
- [x] 2.2 In `app/services/strategy_factory.py` (`DynamicStrategyProxy`), add a global verification block triggered on any `"BUY"` signal.
- [x] 2.3 The verification block must fetch `"BTCUSDT"` data. If its current price is `<` its EMA, veto the signal and return `None`.

## 3. Testing & Documentation
- [x] 3.1 Create `/tmp/test_btc_filter.py` to mock `BTCUSDT` data and verify that an altcoin BUY signal is correctly blocked or permitted depending on BTC's trend.
- [x] 3.2 Update `CHANGELOG.md` reflecting the new Macro Market Context filter.
