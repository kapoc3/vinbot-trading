## ADDED Requirements

### Requirement: Bollinger Bands Calculation
The system SHALL calculate Bollinger Bands for a given symbol using a Simple Moving Average (SMA) period (default 20) and a standard deviation multiplier (default 2.0).

#### Scenario: Upper and Lower Band Generation
- **GIVEN** a sliding window of historical closing prices
- **WHEN** the `TechnicalIndicators` module is queried for Bollinger Bands
- **THEN** it returns the SMA, the Upper Band, and the Lower Band values correctly computed.
