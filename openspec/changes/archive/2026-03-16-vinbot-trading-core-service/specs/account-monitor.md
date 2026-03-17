## ADDED Requirements

### Requirement: Balance Tracking
The system SHALL maintain a real-time view of available balances for the base and quote assets (e.g., BTC and USDT).

#### Scenario: Balance Changed after Trade
- **WHEN** a trade is executed
- **THEN** it calls `GET /api/v3/account` to refresh the current balances.

### Requirement: Dry Run / Testnet Support
The system SHALL allow operating in a "paper trading" mode using the Binance Testnet.

#### Scenario: Testnet Mode Enabled
- **WHEN** the `USE_TESTNET` environment variable is true
- **THEN** all requests are routed to `testnet.binance.vision`.
