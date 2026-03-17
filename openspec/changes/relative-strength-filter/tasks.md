## 1. Indicator Support
- [x] 1.1 In `app/services/indicators.py`, add `get_roc(self, period: int) -> Optional[float]` to the `SymbolData` class. Use standard ROC calculation. Return `None` if `len(self.closes) <= period`.

## 2. Configuration & Orchestration
- [x] 2.1 In `app/core/config.py`, add `ENABLE_RELATIVE_STRENGTH_FILTER: bool = True` and `RS_LOOKBACK_PERIOD: int = 14`.
- [x] 2.2 In `app/main.py`, update the initialization block for symbols. Ensure `"BTCUSDT"` is appended to the stream list if *either* `ENABLE_BTC_DIRECTIONAL_FILTER` or `ENABLE_RELATIVE_STRENGTH_FILTER` is enabled.

## 3. Proxy Veto Implementation
- [x] 3.1 In `app/services/strategy_factory.py`, update `DynamicStrategyProxy.analyze()`.
- [x] 3.2 Add a check: if `signal == "BUY" and symbol != "BTCUSDT" and settings.ENABLE_RELATIVE_STRENGTH_FILTER`.
- [x] 3.3 Within the block, calculate ROC for the target symbol and `BTCUSDT` using `settings.RS_LOOKBACK_PERIOD`. Log a veto and return `None` if the symbol's ROC is `<` BTC's ROC. Bypass gracefully (return `None` or allow, preferably explicitly log and allow as fallback, though strict veto is safer) if ROC cannot be calculated. For strict safety, abort the trade if `None`.

## 4. Testing & Documentation
- [x] 4.1 Create `/tmp/test_relative_strength.py` to seed a hypothetical SymbolData history for an altcoin and BTC, testing both outperformance and underperformance scenarios.
- [x] 4.2 Update `CHANGELOG.md` to reflect the new feature.
