## ADDED Requirements

### Requirement: Dashboard API Endpoint
The system SHALL expose a GET endpoint at `/api/v1/dashboard` that returns consolidated financial and operational metrics.

#### Scenario: Fetching dashboard data
- **WHEN** a valid GET request is made to `/api/v1/dashboard`
- **THEN** the system returns a JSON response containing the current PnL, active strategy name, current market regime, and a list of recent trades.

### Requirement: Dashboard API Caching
The system SHALL cache the dashboard data to prevent database overload from frequent UI polling.

#### Scenario: Cached data retrieval
- **WHEN** multiple requests hit `/api/v1/dashboard` within a 5-second window
- **THEN** the system returns cached data instead of executing new SQLite queries for the trade history.
