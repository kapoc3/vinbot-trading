## ADDED Requirements

### Requirement: Key-Value State Storage
The system SHALL provide a mechanism to store and retrieve arbitrary state keys (e.g., `btcusdt_in_position`) in a persistent database.

#### Scenario: Save and Recover Position State
- **WHEN** the strategy updates `in_position` to True for BTCUSDT
- **THEN** it SHALL be written to the database. Upon restart, the system SHALL read this value and initialize the strategy state with True.

### Requirement: Persistent Order Logging
The system SHALL record every successfully executed order from Binance into a persistent database table.

#### Scenario: Order Data Persistence
- **WHEN** a market order is filled on Binance
- **THEN** the system SHALL store the `orderId`, `symbol`, `side`, `price`, and `executedQty` in the local database.
