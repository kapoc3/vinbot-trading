## ADDED Requirements

### Requirement: RSI Divergence Strategy Module
The system SHALL evaluate dual conditions consisting of RSI overbought/oversold levels combined with regular bullish/bearish price-to-RSI divergences to generate entry signals.

#### Scenario: Regular Bullish Divergence Detection
- **WHEN** the RSI falls below the oversold threshold, and the most recent price swing low is lower than the previous swing low, AND the corresponding RSI swing low is higher than the previous RSI swing low
- **THEN** the system issues a BUY signal.

#### Scenario: Regular Bearish Divergence Detection
- **WHEN** the RSI rises above the overbought threshold, and the most recent price swing high is higher than the previous swing high, AND the corresponding RSI swing high is lower than the previous RSI swing high
- **THEN** the system issues a SELL signal.

### Requirement: Swing Extrema Algorithm
The system SHALL provide a mathematical utility to identify local swing highs and swing lows within a given series (price arrays or RSI arrays) using a configurable lookback/lookforward pivot window.

#### Scenario: Swing High Detection
- **WHEN** a data point is higher than all `n` previous points and all `n` subsequent points within its window
- **THEN** the index and value are marked as a local swing high.

#### Scenario: Swing Low Detection
- **WHEN** a data point is lower than all `n` previous points and all `n` subsequent points within its window
- **THEN** the index and value are marked as a local swing low.
