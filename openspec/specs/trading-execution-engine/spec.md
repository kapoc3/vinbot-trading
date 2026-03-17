## ADDED Requirements

### Requirement: Place Market Order
The system SHALL support placing Market Buy/Sell orders as the primary execution method for high priority trades.

#### Scenario: Successful Market Buy
- **WHEN** the strategy engine triggers a buy signal
- **THEN** a `POST /api/v3/order` request is sent with `type=MARKET` and the order details are logged.

### Requirement: Order Status Monitoring
The system SHALL poll or use user data streams to track the fill status of placed orders.

#### Scenario: Order Filled Notification
- **WHEN** an order status changes to `FILLED`
- **THEN** the system updates the local trade history and notifies the account monitor.
