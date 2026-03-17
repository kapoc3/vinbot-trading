## 1. Configuration Changes
- [ ] 1.1 Add `ENABLE_DYNAMIC_SIZING: bool`, `ALLOCATED_CAPITAL: float`, and `RISK_PER_TRADE_PCT: float` to `app/core/config.py`.

## 2. Binance Exchange Info & Precision
- [ ] 2.1 Update `app/services/binance_client.py` with a method `get_exchange_info(symbol)` to fetch `LOT_SIZE` metadata (specifically `stepSize`).
- [ ] 2.2 Create a caching mechanism for exchange info so it's only queried once on startup per active symbol.
- [ ] 2.3 Implement a helper function `format_quantity(raw_qty, step_size)` that mathematically truncates a float to a valid string or float respecting the Binance step.

## 3. Risk Sizing Logic
- [ ] 3.1 In `app/services/risk_manager.py`, implement `calculate_position_size(symbol, entry_price, sl_price)` using the Kelly/Risk formulation. Protect against division by zero if prices equal.

## 4. Execution Integration
- [ ] 4.1 In `app/main.py`, remove the `if "BTC" in symbol...` hardcoded size block.
- [ ] 4.2 Replace the quantity logic to invoke the new sizing and formatting pipeline to derive an exact, safe execution size prior to order placement.

## 5. Testing & Validation
- [ ] 5.1 Create `/tmp/test_dynamic_sizing.py` simulating exact risk parameters, stop-loss distances, and precision truncation mathematically.
- [ ] 5.2 Update `CHANGELOG.md`.
