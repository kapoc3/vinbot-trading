## ADDED Requirements

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
