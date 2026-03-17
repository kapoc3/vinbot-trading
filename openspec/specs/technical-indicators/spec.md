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

### Requirement: Bollinger Bands Calculation
The system SHALL calculate Bollinger Bands for a given symbol using a Simple Moving Average (SMA) period (default 20) and a standard deviation multiplier (default 2.0).

#### Scenario: Upper and Lower Band Generation
- **GIVEN** a sliding window of historical closing prices
- **WHEN** the `TechnicalIndicators` module is queried for Bollinger Bands
- **THEN** it returns the SMA, the Upper Band, and the Lower Band values correctly computed.

### Requirement: EMA Calculation
The system SHALL calculate the Exponential Moving Average (EMA) for a given period N using the standard smoothing constant `2 / (N + 1)`.

#### Scenario: EMA Smoothing
- **GIVEN** a list of closing prices
- **WHEN** the `TechnicalIndicators` module is queried for EMA(9)
- **THEN** it returns the smoothed average correctly computed across the historical window.

### Requirement: MACD Calculation
The system SHALL calculate the MACD line, Signal line, and Histogram using the standard (12, 26, 9) parameters.

#### Scenario: MACD Signal Cross
- **GIVEN** a price history
- **WHEN** the MACD line moves above the Signal line
- **THEN** the system identifies this as a potential bullish momentum shift.
