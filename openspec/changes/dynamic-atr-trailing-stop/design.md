# Design: Dynamic ATR Trailing Stop

## The Problem (Why)
Our current strategies (`RSIStrategy`, `RsiDivergenceStrategy`, `BollingerBandsStrategy`, `MacdMaCrossStrategy`) open positions based on strong signals but primarily exit based on reversal signals from those same indicators. A major limitation of this approach is that trending indicators (like MACD) often lag. A price can surge 15%, but before the MACD signal line crosses down to trigger an exit, the price may have already dropped 10%. We need a mechanism to lock in profits dynamically without stifling the trend.

## Goals
1.  **Protect Profits:** Implement a trailing stop that moves up as the price moves up.
2.  **Volatility Adaptation:** The trailing stop distance should not be a fixed percentage but rather a multiple of the Average True Range (ATR), allowing the stop to widen during high volatility and tighten during low volatility.
3.  **Global Application:** The trailing stop mechanism should act as a safety net across *all* active strategies, intercepting trading logic to force a exit if triggered.

## Non-Goals
*   A static stop loss percentage (e.g., fixed -3%).
*   Modifying the core math of the existing opening strategy signals.
*   Adding support for Take Profit (limit) orders directly; this is strictly a dynamic stop loss evaluated on tick/kline.

## Solution Outline
The ideal place to inject this logic is the interface between the `StrategyManager` / `DynamicStrategyProxy` and the underlying strategies, or as a centralized component within the `RiskManager`. However, because it requires state persistence specific to a trade (the maximum price reached since opening the position), the strategy proxy is a natural fit.

**Proposed Implementation:**
1.  **State Tracking:** When a "BUY" signal is executed successfully, the system records the current price as `highest_price` for that symbol.
2.  **Ongoing Evaluation:**
    *   On each new kline update, if a position is open:
        *   If the new `close` (or `high`) > `highest_price`, update `highest_price = new close`.
        *   Calculate the trailing stop: `StopPrice = highest_price - (ATR * Stop_Multiplier)`. (e.g., a multiplier of 3.0 or 2.5 is typical).
        *   If current `close` < `StopPrice`, generate a forced "SELL" signal (overriding the underlying strategy's normal analyze phase).
    *   If no position is open: just pass through to normal strategy analysis.

### Persistence Strategy
Since this bot can restart, the `highest_price` must be stored persistently.
*   `persistence.set_state(f"{symbol}_highest_price", price)`
*   `persistence.set_state(f"{symbol}_atr_trailing_active", True/False)`

## Alternatives Considered
- **Updating each strategy individually**: Too much code duplication. Instead, wrapping the strategy interface with a `RiskManager.check_trailing_stop` function, or having the `StrategyManager` handle it globally is much cleaner.
- **Using percentage trailing**: Much more fragile. 5% trailing on BTC is huge, 5% on SHIB might just be market noise. ATR is strictly superior because it scales with the asset.

## Trade-offs & Risks
- **Whipsaws:** Even with ATR, extreme wicks could trigger the stop and push us out of a position just before it continues to trend upward. This is the inherent tradeoff of trailing stops.
- **Data Latency:** Since we evaluate on kline close (or occasionally on ticks), there might be a minor delay in stop execution vs placing a hard stop order on the exchange. However, calculating trailing stops locally (soft stops) avoids API rate limits and gives us more control over the logic.
