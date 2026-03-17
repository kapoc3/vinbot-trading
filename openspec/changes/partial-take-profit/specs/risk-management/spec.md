## ADDED Requirements

### Requirement: Multiple TP Trigger Evaluation
The risk manager MUST evaluate open positions to see if the current price crosses predetermined Take Profit percentage levels in relation to the initial entry price.

#### Scenario: First Take Profit Hit
- **GIVEN** a configuration `PARTIAL_TP_LEVELS="0.05:0.5"` (5% profit, sell 50% of the position)
- **WHEN** an open position reaches 5% above its original `entry_price`
- **AND** the `tp_levels_hit` for this position is currently `0`
- **THEN** the system returns a partial sell signal with the quantity calculated as `initial_quantity * 0.5`.
- **AND** increments the `tp_levels_hit` counter to `1`.

#### Scenario: Break-Even Stop Loss upon TP1
- **GIVEN** the `MOVE_SL_TO_BE_ON_TP1` flag is set to `True`
- **WHEN** the first Take Profit level is hit (`tp_levels_hit` goes from 0 to 1)
- **THEN** the hard stop-loss level for the remaining position is immediately moved to `entry_price`.
