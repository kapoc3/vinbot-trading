## 1. Indicator Maths Expansion
- [ ] 1.1 Implement `calculate_donchian_channel` in `app/services/indicators.py`.
- [ ] 1.2 Expose a `get_donchian_channel` and `get_volume_sma` helper method on the `SymbolData` class.

## 2. Breakout Strategy Implementation
- [ ] 2.1 Create `app/services/breakout_strategy.py` with the `BreakoutStrategy` logic (Buy on upper break + high volume, Sell on middle return).
- [ ] 2.2 Wire up states and position management inside the new strategy class.

## 3. Factory Integration
- [ ] 3.1 Import and register `BreakoutStrategy` within `StrategyManager` (`app/services/strategy_factory.py`).
- [ ] 3.2 Add to `DynamicStrategyProxy` methods for state synchronization.
- [ ] 3.3 (Optional) Integrate into `Auto` regime selection logic.

## 4. Testing & Docs
- [ ] 4.1 Write `/tmp/test_breakout.py` to verify the Donchian math and the Breakout/Volume logic.
- [ ] 4.2 Update `CHANGELOG.md` reflecting the new strategy capabilities.
