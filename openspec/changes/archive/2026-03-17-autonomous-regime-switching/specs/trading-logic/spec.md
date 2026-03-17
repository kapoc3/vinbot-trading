## MODIFIED Requirements

### Requirement: Strategy Injection Layer
The trading engine SHALL dynamically select and instantiate its trading strategy based on a configuration parameter (`TRADING_STRATEGY`), allowing switching between "RsiOnly", "RsiWithDivergence", or **"Auto"** for autonomous regime-based switching.

#### Scenario: Autonomous Regime Switching
- **WHEN** `TRADING_STRATEGY` is set to "Auto"
- **THEN** the engine re-evaluates the market regime every candle and swaps between "RsiOnly" and "RsiWithDivergence" as appropriate.

#### Scenario: Using RsiWithDivergence
- **WHEN** the environment variable `TRADING_STRATEGY` is set to "RsiWithDivergence" at startup
- **THEN** the main trading loop evaluates RSI values *and* recent divergences before triggering market orders.

#### Scenario: Using Default RsiOnly
- **WHEN** the environment variable `TRADING_STRATEGY` is omitted or set to "RsiOnly"
- **THEN** the main trading loop continues evaluating raw RSI overbought/oversold levels.
