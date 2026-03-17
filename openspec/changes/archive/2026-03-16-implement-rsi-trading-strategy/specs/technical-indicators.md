## ADDED Requirements

### Requirement: RSI Calculation
The system SHALL calculate the Relative Strength Index (RSI) using a configurable period (default 14) based on a provided moving window of closing prices.

#### Scenario: Valid RSI Calculation
- **WHEN** the indicator module receives a list of closing prices of size >= period
- **THEN** it returns a float value between 0 and 100 representing the RSI score.

### Requirement: Historical Price Warm-up
The system SHALL fetch historical closing prices to pre-fill the mathematical indicator arrays before applying WebSocket streams.

#### Scenario: Warm-up Initialized
- **WHEN** the trading strategy starts up for a specific symbol
- **THEN** it retrieves the last N klines via the REST API before it starts processing live events.
