# Design: Partial Take Profit

## Goals
1. Allow the user to configure multiple Take Profit targets based on percentage gain from the entry price.
2. Execute fractional sell orders when these targets are hit.
3. Automatically move the Stop Loss to Break-Even (Entry Price) once Target 1 is hit.
4. Integrate smoothly with the existing strategy architecture without rewriting individual strategies.

## Non-Goals
* Implementing a complex grid trading system. This is strictly for exiting existing positions.
* Complex quantity calculations based on precise exchange balances at this stage. We will operate on a logical percentage of the initial entry unit size.

## Solution Outline
1. **Configuration Update (`config.py`):**
   * Add `PARTIAL_TP_LEVELS: str = "0.05:0.5,0.10:0.25"` (String format to parse into tuples or dicts: at 5% profit sell 50%, at 10% profit sell 25% of the original size).
   * Add `MOVE_SL_TO_BE_ON_TP1: bool = True`.

2. **Risk Manager Update (`risk_manager.py`):**
   * Upgrade `Position` state to store:
     * `entry_price`: float
     * `initial_quantity`: float
     * `current_quantity`: float
     * `tp_levels_hit`: int (counts how many levels have been executed)
   * The `check_risk_limits()` method will now also evaluate if the current price exceeds `entry_price * (1 + partial_tp_percentage)`.
   * Return a specific tuple or dict: `("PARTIAL_SELL", sell_quantity)` if a TP is hit.

3. **Trading Loop Integration (`main.py` / `strategy_factory.py`):**
   * When `risk_manager` reports a `"PARTIAL_SELL"`, instruct the `TradingEngine` to sell that specific quantity.
   * Do not flag `in_position` as `False` until the `current_quantity` reaches 0 (or a strategy/trailing stop triggers the final full sell).
   * If a strategy signals `"SELL"` or the trailing stop hits, sell the *remaining* `current_quantity`.

4. **Persistence:**
   * Update `persistence.py` to save and load the `tp_levels_hit` count and the `current_quantity` to survive restarts gracefully.
