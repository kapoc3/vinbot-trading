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

#### Scenario: Autonomous switch to MacdMaCross strategy
- **GIVEN** the bot is in `"Auto"` mode
- **AND** the `MarketRegime` is `TRENDING`
- **AND** the ADX strength is very high (>40)
- **THEN** the bot SHALL switch to the `MacdMaCrossStrategy` for stronger trend confirmation.

#### Scenario: Using RsiWithDivergence
- **WHEN** the environment variable `TRADING_STRATEGY` is set to "RsiWithDivergence" at startup
- **THEN** the main trading loop evaluates RSI values *and* recent divergences before triggering market orders.

#### Scenario: Using Default RsiOnly
- **WHEN** the environment variable `TRADING_STRATEGY` is omitted or set to "RsiOnly"
- **THEN** the main trading loop continues evaluating raw RSI overbought/oversold levels.

### Requirement: MACD + MA Cross Strategy
The system SHALL support a `MacdMaCrossStrategy` that uses a 200-period EMA as a trend filter and MACD signals for entry and exit.

#### Scenario: Running MACD Strategy
- **WHEN** the `TRADING_STRATEGY` environment variable is set to "MacdMaCross"
- **THEN** the bot executes trades based on MACD crossovers confirmed by the EMA 200 filter.
