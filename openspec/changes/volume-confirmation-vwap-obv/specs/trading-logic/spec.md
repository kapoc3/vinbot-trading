## ADDED Requirements

### Requirement: Global Volume Confirmation Veto
The proxy engine SHALL optionally intercept strategy "BUY" signals and veto them if volume confirms lack of bullish interest.

#### Scenario: Vetoing a BUY without VWAP Support
- **GIVEN** the `ENABLE_VOLUME_CONFIRMATION` setting is `True`
- **AND** a strategy returns a "BUY" signal
- **WHEN** the current price is strictly less than the calculated VWAP
- **THEN** the proxy MUST change the signal to `None` (Veto).

#### Scenario: Vetoing a BUY with Declining OBV
- **GIVEN** the `ENABLE_VOLUME_CONFIRMATION` setting is `True`
- **AND** a strategy returns a "BUY" signal
- **WHEN** the current OBV is less than its own 20-period Moving Average (indicating declining trend)
- **THEN** the proxy MUST change the signal to `None` (Veto).

#### Scenario: Allowing a Confirmed BUY
- **GIVEN** the `ENABLE_VOLUME_CONFIRMATION` setting is `True`
- **AND** a strategy returns a "BUY" signal
- **WHEN** the current price >= VWAP
- **AND** the current OBV >= OBV_SMA(20)
- **THEN** the proxy MUST allow the "BUY" signal to pass through unchanged.
