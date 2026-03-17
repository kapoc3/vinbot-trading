# Proposal: Scaled Take Profits (Toma de Ganancias Escalonada)

## The Problem
Currently, VinBot enters a position with 100% of its designated size and exits 100% at once. The exit is primarily triggered by either a hard stop loss, a strategy reversal signal, or the ATR Trailing Stop. This "all or nothing" approach has a significant drawback: if a coin pumps 15% and then rapidly crashes back to the entry price before the trailing stop catches up, the bot loses all those unrealized gains.

## The Solution
Implement **Partial Take Profits (Scaled Exits)**. By taking a percentage of the position off the table at predefined profit levels, we "lock in" gains early and let the rest of the position ride the trend free of risk.

For example:
- Take 50% off the table at +5% profit.
- Take 25% off the table at +10% profit.
- Let the remaining 25% ride the ATR trailing stop (or a runner).

Additionally, once the first Take Profit (TP1) is hit, we can automatically adjust the Stop Loss to the *Entry Price* (Break-Even), ensuring the trade is risk-free.

## High-Level Approach
1. **Define TP Levels:** Add configuration for a list of TP targets (e.g., `[(0.05, 0.5), (0.10, 0.25)]` -> 5% profit sell 50%, 10% profit sell 25%).
2. **State Management:** `app/services/risk_manager.py` (or a dedicated position tracker) must track how many of the TP levels have been triggered for an open position to avoid selling the same tier twice.
3. **Execution:** Update `main.py` (or the websocket listener) to check the current price against the active position's entry price. If a TP level is reached, the bot fires a `SELL` order for the specified percentage of the remaining/initial quantity.

## Impact
- Significantly smoother equity curve.
- Higher win rate (many trades hitting TP1 and reversing will now close in profit instead of a loss or break-even).
- Requires updating the `RiskManager` and trade execution flows to handle fractional selling instead of boolean `in_position` states.
