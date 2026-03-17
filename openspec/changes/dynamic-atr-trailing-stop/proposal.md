# Proposal: Dynamic ATR Trailing Stop (Advanced Risk Management)

## The Problem
Currently, the trading strategies in the bot trigger entries and exits based on indicator conditions (e.g., MACD or RSI cross). While these entry signals are well-tuned, the exits can be inefficient. If a strategy captures a strong trend that suddenly reverses sharply before the exit indicator triggers, the bot may give back a significant portion of the unrealized profit. The basic `RiskManager` currently handles fixed max open positions or static check mechanisms but does not actively protect running profits.

## The Solution
Implement a **Trailing Stop Loss based on the Average True Range (ATR)**.
Instead of relying solely on fixed indicators to close a position, we track the highest price reached since the position was opened. We then maintain a dynamic stop-loss level at a distance of `N * ATR` below this highest price. If the current price triggers this stop, we exit the position to lock in profits or minimize losses. 
Because ATR represents the current market volatility, the trailing stop will automatically widen during highly volatile periods (preventing premature exits from noise) and tighten during calm periods.

## High-Level Approach
1.  **State Management:** the `DynamicStrategyProxy` or the individual strategies themselves (or the `RiskManager`) will need to track the `highest_price` since a position was opened.
2.  **Stop Level Calculation:** Calculate real-time stop-loss: `TrailingStop = highest_price - (ATR_multiplier * current_ATR)`.
3.  **Exit Condition Overhaul:** When evaluating a symbol, before checking strategy-specific exit signals (like MACD cross down), first check if the current price has dropped below the `TrailingStop`. If so, issue a forced SELL signal.
4.  **Integration:** Introduce this logic into the strategy cycle. It could either be an enhancement to the `RiskManager` or a wrapper around all strategies in `DynamicStrategyProxy`. For modularity, having the strategies query the risk manager, or having the proxy intercept, are valid approaches.

## Capabilities Changed / Added
*   **Risk Management:** Native support for volatility-adjusted trailing stops.
*   **Strategy Interface:** Standardized tracking of trade high watermarks.

## Impact
*   **app/services/strategy_factory.py** or **app/services/risk_manager.py**: Requires state tracking for active trades (entry price, highest recorded price).
*   **app/services/persistence.py**: Needs to store and recover tracking data so trailing stops persist across bot restarts.
*   **Testing**: Unit tests are required to ensure the stop level correctly follows the price up but never moves down, and reliably triggers a sell on a reversal.
