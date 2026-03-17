## ADDED Requirements

### Requirement: ADX Trend Classification
The system SHALL implement the ADX (Average Directional Index) indicator to determine the current trend strength of a given market symbol.

#### Scenario: Market in Strong Trend
- **WHEN** the 14-period ADX value rises above 25
- **THEN** the system marks the regime as "Trending" or "Strong Trend".

#### Scenario: Market in Ranging State
- **WHEN** the 14-period ADX value is below 20
- **THEN** the system marks the regime as "Ranging" or "Sideways".

### Requirement: ATR Volatility Filtering
The system SHALL use ATR (Average True Range) to filter entries if volatility exceeds a predefined "Safety Threshold".

#### Scenario: High Volatility Protection
- **WHEN** the current ATR is double the 24-hour average ATR
- **THEN** the system SHALL pause new entries to prevent "Death Whipsaws".
