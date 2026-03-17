## ADDED Requirements

### Requirement: Donchian Channel Calculation
The system SHALL compute Donchian Channels over a specified sliding window of periods.

#### Scenario: Getting Donchian Bands
- **GIVEN** a list of highs and a list of lows
- **WHEN** the `TechnicalIndicators` module is queried for Donchian(20)
- **THEN** it correctly identifies the highest high, lowest low, and the middle baseline of the last 20 periods.

### Requirement: Volume SMA Calculation
The system SHALL calculate the Simple Moving Average (SMA) of trading volume to define a volume baseline.

#### Scenario: Generating Volume SMA
- **GIVEN** a list of closing volumes for past klines
- **WHEN** calculating the 20-period SMA
- **THEN** it correctly provides the average volume for breakout comparison.
