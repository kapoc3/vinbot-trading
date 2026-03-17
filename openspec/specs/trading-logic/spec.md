## ADDED Requirements

### Requirement: Strategy Injection Layer
The trading engine SHALL dynamically select and instantiate its trading strategy based on a configuration parameter (`TRADING_STRATEGY`), allowing switching between "RsiOnly", "RsiWithDivergence", or other future strategies.

#### Scenario: Using RsiWithDivergence
- **WHEN** the environment variable `TRADING_STRATEGY` is set to "RsiWithDivergence" at startup
- **THEN** the main trading loop evaluates RSI values *and* recent divergences before triggering market orders.

#### Scenario: Using Default RsiOnly
- **WHEN** the environment variable `TRADING_STRATEGY` is omitted or set to "RsiOnly"
- **THEN** the main trading loop continues evaluating raw RSI overbought/oversold levels.
