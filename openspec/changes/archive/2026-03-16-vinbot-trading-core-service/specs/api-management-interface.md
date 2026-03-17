## ADDED Requirements

### Requirement: Bot Control Endpoints
The FastAPI application SHALL expose endpoints to start, stop, and status-check the trading bot.

#### Scenario: Stop Bot Request
- **WHEN** `POST /bot/stop` is called
- **THEN** the background task for the trading engine is safely cancelled after closing open connections.

### Requirement: Health and Configuration Endpoint
The system SHALL provide an endpoint to verify connectivity and current configuration (without exposing secrets).

#### Scenario: Health Check
- **WHEN** `GET /health` is called
- **THEN** it returns the server time offset, balance summary, and bot status.
