## 1. VWAP and OBV Implementation
- [x] 1.1 Implement OBV (On-Balance Volume) running calculation in `app/services/indicators.py`.
- [x] 1.2 Implement rolling VWAP (`sum(typical * volume) / sum(volume)`) in `app/services/indicators.py`.
- [x] 1.3 Expose both via `SymbolData` methods (`get_obv`, `get_vwap`).

## 2. Proxy Confirmation Filter
- [x] 2.1 Add `ENABLE_VOLUME_CONFIRMATION`, `VWAP_PERIOD` to `app/core/config.py`.
- [x] 2.2 In `DynamicStrategyProxy.analyze` (`strategy_factory.py`), intercept "BUY" signals.
- [x] 2.3 Apply veto logic: return `None` instead of `"BUY"` if `current_price < vwap` or `obv_trend < 0`.

## 3. Testing and Validation
- [x] 3.1 Create `/tmp/test_vwap_obv.py` to ensure indicator math is sound and proxy vetoing works.
- [x] 3.2 Update `CHANGELOG.md` with new Volume Confirmation filter.
