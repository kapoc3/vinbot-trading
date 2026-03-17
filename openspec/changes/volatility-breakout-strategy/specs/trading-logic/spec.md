## ADDED Requirements

### Requirement: Breakout Strategy System
The trading engine SHALL support a `"Breakout"` strategy utilizing Donchian Channels and Volume confirmation.

#### Scenario: Valid Breakout Buy Signal
- **GIVEN** a price history with calculation of a 20-period Donchian Channel
- **AND** a 20-period average volume baseline
- **WHEN** the current candle's close breaks above the Donchian Upper Band
- **AND** the current candle's volume is significantly above the average volume (>1.2x)
- **THEN** the `BreakoutStrategy` returns a "BUY" signal.

#### Scenario: Return to Middle Band Exit
- **GIVEN** an open position initiated by the BreakoutStrategy
- **WHEN** the current candle's close drops below the Donchian Middle Band (average of upper and lower bands)
- **AND** the ATR Trailing Stop has not already triggered
- **THEN** the `BreakoutStrategy` returns a "SELL" signal.
