## ADDED Requirements

### Requirement: Strategy Injection Layer
The trading engine SHALL dynamically select and instantiate its trading strategy based on a configuration parameter (`TRADING_STRATEGY`), allowing switching between "RsiOnly", "RsiWithDivergence", or other future strategies.

### Requirement: Autonomous Strategy Switching
- The bot MUST support a `TRADING_STRATEGY` value of `"Auto"`.
- When in `"Auto"` mode, the bot MUST select the most appropriate strategy based on the current `MarketRegime`.
- The strategy selection MUST be locked if a position is currently open for the symbol.

#### Scenario: Autonomous switch to Trending strategy
- **GIVEN** the bot is in `"Auto"` mode
- **AND** no position is open for `BTCUSDT`
- **WHEN** the `MarketRegime` for `BTCUSDT` changes to `Trending` (ADX > 25)
- **THEN** the bot MUST switch to the `RsiWithDivergence` strategy for `BTCUSDT`.

#### Scenario: Using RsiWithDivergence
- **WHEN** the environment variable `TRADING_STRATEGY` is set to "RsiWithDivergence" at startup
- **THEN** the main trading loop evaluates RSI values *and* recent divergences before triggering market orders.

#### Scenario: Using Default RsiOnly
- **WHEN** the environment variable `TRADING_STRATEGY` is omitted or set to "RsiOnly"
- **THEN** the main trading loop continues evaluating raw RSI overbought/oversold levels.
