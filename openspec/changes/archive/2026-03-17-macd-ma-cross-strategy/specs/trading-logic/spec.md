## ADDED Requirements

### Requirement: MACD + MA Cross Strategy
The system SHALL support a `MacdMaCrossStrategy` that uses a 200-period EMA as a trend filter and MACD signals for entry and exit.

#### Scenario: Running MACD Strategy
- **WHEN** the `TRADING_STRATEGY` environment variable is set to "MacdMaCross"
- **THEN** the bot executes trades based on MACD crossovers confirmed by the EMA 200 filter.

## MODIFIED Requirements

### Requirement: Autonomous Strategy Switching
- The bot MUST support a `TRADING_STRATEGY` value of `"Auto"`.
- When in `"Auto"` mode, the bot MUST select the most appropriate strategy based on the current `MarketRegime`.
- The strategy selection MUST be locked if a position is currently open for the symbol.

#### Scenario: Autonomous switch to MacdMaCross strategy
- **GIVEN** the bot is in `"Auto"` mode
- **AND** the `MarketRegime` is `TRENDING`
- **AND** the ADX strength is very high (>40)
- **THEN** the bot SHALL switch to the `MacdMaCrossStrategy` for stronger trend confirmation.
