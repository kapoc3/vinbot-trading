## 1. Dynamic ATR Trailing Logic

- [x] 1.1 Add `highest_prices: Dict[str, float]` state tracker to `DynamicStrategyProxy` (or a dedicated component).
- [x] 1.2 Implement the ATR trailing stop calculation inside the `analyze` wrap of `DynamicStrategyProxy` (e.g., multiplier of 3.0 by default).
- [x] 1.3 Ensure forced "SELL" is returned if price falls below `highest_price - (ATR * multiplier)`.

## 2. Persistence Integration

- [x] 2.1 Update `update_position` in the proxy (or strategy) to reset or initialize the `highest_price` when entering/exiting a trade.
- [x] 2.2 Wire up `persistence.get_state` and `set_state` in the proxy to save and recover `f"{symbol}_highest_price"`.

## 3. Configuration & Tuning

- [x] 3.1 Expose the ATR multiplier as a configurable constant (e.g., `ATR_TRAILING_MULTIPLIER = 3.0`).
- [x] 3.2 Add a toggle to enable/disable Trailing Stop globally if needed via env (`ENABLE_TRAILING_STOP=True`).

## 4. Documentation & Verification

- [x] 4.1 Write a dedicated unit test (`/tmp/test_trailing_stop.py`) that fakes price action to climb up then drop rapidly, verifying the "SELL" signal triggers.
- [x] 4.2 Update `CHANGELOG.md` with the new Dynamic ATR Trailing Stop functionality.
