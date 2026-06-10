## ADDED Requirements

### Requirement: Dashboard Visual Interface
The system SHALL provide a web user interface that visually displays the data provided by the Dashboard API in a consolidated view.

#### Scenario: Viewing the dashboard
- **WHEN** the user navigates to the dashboard URL
- **THEN** the UI displays the daily PnL, total PnL, current market regime, active strategy, and a table of recent trades.

### Requirement: Real-time Update Polling
The web UI SHALL update the displayed data periodically to provide near real-time insights without manual refresh.

#### Scenario: Auto-refresh
- **WHEN** the user keeps the dashboard open
- **THEN** the UI polls the Dashboard API every 10 seconds and updates the DOM elements with the fresh data.
