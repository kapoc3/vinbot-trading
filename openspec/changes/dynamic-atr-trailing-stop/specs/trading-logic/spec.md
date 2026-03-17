## MODIFIED Requirements

### Requirement: Dynamic ATR Trailing Stop
The trading engine SHALL evaluate an active trailing stop-loss for every open position before delegating the analysis to individual strategies. 

#### Scenario: Advancing Trailing Stop
- **GIVEN** an open position for `ETHUSDT`
- **WHEN** a new kline arrives, and the `close` price is greater than the recorded `highest_price` for that position
- **THEN** the system MUST update `highest_price` to the new `close` price and calculate the new trailing stop level as `highest_price - (ATR * Stop_Multiplier)`.

#### Scenario: Triggering Trailing Stop
- **GIVEN** an open position with an established `highest_price` and a current trailing stop level
- **WHEN** the `close` price drops below the calculated trailing stop level
- **THEN** the proxy MUST forcefully return a "SELL" signal regardless of what the underlying strategy (MACD, RSI, etc.) evaluates.

#### Scenario: State Persistence
- **WHEN** the bot restarts or reloads state
- **THEN** it MUST recover the `highest_price` for each active position to resume trailing stop evaluations correctly without resetting the high watermark to the current price.
