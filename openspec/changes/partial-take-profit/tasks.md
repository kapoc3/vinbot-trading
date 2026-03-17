## 1. Config Updates
- [x] 1.1 Add `PARTIAL_TP_LEVELS: str` to `app/core/config.py` with parsing logic (e.g. `5.0:50,10.0:25`).
- [x] 1.2 Add `MOVE_SL_TO_BE_ON_TP1: bool = True` to config.

## 2. Risk Manager Core Enhancements
- [x] 2.1 Update `RiskManager` to track `initial_quantity`, `current_quantity`, and `tp_levels_hit` per symbol.
- [x] 2.2 In `check_risk_limits`, implement logic to iterate over un-hit TP levels.
- [x] 2.3 Add Break-Even SL update logic when TP1 triggers.
- [x] 2.4 Return the tuple `("PARTIAL_SELL", qty)` when applicable instead of just "SELL".

## 3. Position Logic & Trading Engine
- [x] 3.1 Update `main.py` (or websocket callback) to handle `("PARTIAL_SELL", qty)` signals explicitly.
- [x] 3.2 Add the logic for full "SELL" (strategy or trailing stop) to only sell the remaining `current_quantity`, not the initial batch.
- [x] 3.3 Ensure `strategy_factory.py` (via `DynamicStrategyProxy`) retains position locks correctly until `current_quantity` zeroes out.

## 4. Testing & Validation
- [x] 4.1 Write `/tmp/test_partial_tp.py` to simulate a simulated sequence of Partial TP and final Strategy exit to guarantee mathematics are sound.
- [x] 4.2 Update `CHANGELOG.md`.
