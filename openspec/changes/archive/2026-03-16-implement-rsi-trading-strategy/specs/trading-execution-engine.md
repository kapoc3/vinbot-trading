## MODIFIED Requirements

### Requirement: Place Market Order
The system SHALL support placing Market Buy/Sell orders autonomously based on programmatic signals from a defined trading strategy, rather than purely manual intervention.

#### Scenario: Successful Market Buy
- **WHEN** the RSI strategy engine triggers a buy signal
- **THEN** a `POST /api/v3/order` request is automatically sent with `type=MARKET` and the order details are logged, confirming the strategy execution.
