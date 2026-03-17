## MODIFIED Requirements

### Requirement: Trigger Buy Signal
The system SHALL emit a BUY signal when the RSI drops below the oversold threshold AND the persistent state database confirms `in_position` is False for the specific symbol.

#### Scenario: Recovery from Restart
- **WHEN** the bot restarts and RSI is oversold
- **THEN** the strategy SHALL check the persistent database; if it shows the bot is already `in_position`, it SHALL NOT emit a new signal.
