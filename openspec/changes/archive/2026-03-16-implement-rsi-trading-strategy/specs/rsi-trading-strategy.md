## ADDED Requirements

### Requirement: Trigger Buy Signal
The system SHALL emit a BUY signal when the RSI drops below the oversold threshold (default 30) and the bot is not currently holding a purchased position (`in_position` = False).

#### Scenario: RSI Oversold
- **WHEN** RSI hits 25 and `in_position` is False
- **THEN** the strategy records `in_position=True` and places a BUY market order.

### Requirement: Trigger Sell Signal
The system SHALL emit a SELL signal when the RSI rises above the overbought threshold (default 70) and the bot is currently holding a purchased position (`in_position` = True).

#### Scenario: RSI Overbought
- **WHEN** RSI hits 75 and `in_position` is True
- **THEN** the strategy records `in_position=False` and places a SELL market order.
