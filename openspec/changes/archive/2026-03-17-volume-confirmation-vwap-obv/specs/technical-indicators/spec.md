## ADDED Requirements

### Requirement: Rolling VWAP Calculation
The system SHALL compute a Volume Weighted Average Price (VWAP) over a rolling N-period window.

#### Scenario: Getting Rolling VWAP
- **GIVEN** a sliding window of typical prices `(high+low+close)/3` and volumes
- **WHEN** the `TechnicalIndicators` module is queried for VWAP(50)
- **THEN** it correctly computes `sum(Typical*Volume) / sum(Volume)` over the last 50 periods.

### Requirement: Continuous OBV Calculation
The system SHALL calculate continuous On-Balance Volume (OBV).

#### Scenario: Updating Current OBV
- **GIVEN** an ongoing OBV sum
- **WHEN** a new kline closes higher than the previous close
- **THEN** the total volume for that kline is added to the OBV sum.
- **WHEN** a new kline closes lower than the previous close
- **THEN** the total volume for that kline is subtracted from the OBV sum.
