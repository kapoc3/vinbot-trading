# Proposal: BTC Directional Filter (Market Context)

## The Problem
Currently, VinBot evaluates long (BUY) trading signals for altcoins based purely on their individual price action and indicators (RSI, Bollinger, MACD, Volume). However, the cryptocurrency market is highly correlated, and Bitcoin (BTC) dictates the overall market direction. 

Going long on altcoins when Bitcoin is in a strong downtrend is statistically unfavorable and often results in "catching falling knives," as heavy BTC sell-offs will drag down almost all other assets, regardless of how bullish their individual setups might appear.

## The Solution
Implement a **BTC Directional Filter** acting as a "Market Regime Conductor."
Before any strategy is allowed to execute a BUY order for any altcoin, the bot must first check Bitcoin's trend. If BTC is deemed "bearish" (e.g., trading below its moving average or VWAP), all BUY signals for altcoins are vetoed.

This serves as a macro-level risk management system, ensuring the bot only swims with the current of the overall market, significantly increasing the probability of successful trades and reducing massive drawdowns during market crashes.

## High-Level Approach
1.  **Configuration:** Introduce `ENABLE_BTC_DIRECTIONAL_FILTER: bool = True` and configure the trend indicator for BTC (e.g., `BTC_DIRECTION_EMA: int = 200` or a VWAP check).
2.  **Data Availability:** Ensure the engine always subscribes to and tracks `BTCUSDT` market data internally, even if the user hasn't explicitly added it to their `TRADING_SYMBOLS` config.
3.  **Veto Mechanism:** Extend the `DynamicStrategyProxy.analyze()` method. When evaluating a BUY signal for an altcoin, interrogate the `SymbolData` of `BTCUSDT`. If BTC is trading below its key moving average, veto the altcoin's BUY signal.

## Impact
- **Higher Win Rate:** Trades are only taken in favorable market conditions.
- **Lower Drawdowns:** The bot naturally stops taking long positions when the general market crashes.
- **Improved Risk-Adjusted Returns:** Less exposure to market-wide systemic risks.
