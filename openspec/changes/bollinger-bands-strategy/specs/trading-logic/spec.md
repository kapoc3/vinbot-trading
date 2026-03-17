## ADDED Requirements

### Requirement: Bollinger Bands Strategy Initialization
The system SHALL support instantiating and executing a `BollingerBandsStrategy` that uses both RSI and Bollinger Bands indicators to generate buy and sell signals.

#### Scenario: Using Bollinger Bands Strategy
- **WHEN** the environment variable `TRADING_STRATEGY` is set to "BollingerBands" at startup
- **THEN** the main trading loop evaluates price crosses below the lower band and RSI oversold levels before triggering market orders.

## MODIFIED Requirements

### Requirement: Autonomous Strategy Switching
- The bot MUST support a `TRADING_STRATEGY` value of `"Auto"`.
- When in `"Auto"` mode, the bot MUST select the most appropriate strategy based on the current `MarketRegime`.
- The strategy selection MUST be locked if a position is currently open for the symbol.

#### Scenario: Autonomous switch to Trending strategy
- **GIVEN** the bot is in `"Auto"` mode
- **AND** no position is open for `BTCUSDT`
- **WHEN** the `MarketRegime` for `BTCUSDT` changes to `Trending` (ADX > 25)
- **THEN** the bot MUST switch to the `RsiWithDivergence` strategy for `BTCUSDT`.

#### Scenario: Autonomous switch to Bollinger Bands strategy
- **GIVEN** the bot is in `"Auto"` mode
- **AND** no position is open for `BTCUSDT`
- **WHEN** the `MarketRegime` for `BTCUSDT` changes to `Ranging` (ADX < 20)
- **THEN** the bot MUST switch to the `BollingerBandsStrategy` for `BTCUSDT`.
