## ADDED Requirements

### Requirement: Fractional Execution logic
The trading engine MUST be capable of executing sell orders for less than the total position size while maintaining an "open position" state until the quantity reaches zero.

#### Scenario: Retaining Open Session
- **GIVEN** the `risk_manager` returns `("PARTIAL_SELL", 1.5)` from an initial position of 3 BTC.
- **WHEN** placing a market order on Binance for the partial quantity (1.5 BTC)
- **THEN** the local position tracking must reflect `current_quantity = 1.5`, keeping the position logically open.

#### Scenario: Final Strategy Sell
- **GIVEN** an open position with an initial quantity of 3.0, and a current quantity of 1.5 (due to TP1).
- **WHEN** the active Strategy signals a `SELL` or trailing stop triggers
- **THEN** a market order is placed strictly for the remaining `current_quantity` (1.5 BTC) exactly to close out the trade entirely.
