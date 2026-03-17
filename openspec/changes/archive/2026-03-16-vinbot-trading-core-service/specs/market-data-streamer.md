## ADDED Requirements

### Requirement: Real-time Klines Stream
The system SHALL connect to Binance WebSockets to receive live candlestick (klines) data for configured symbols.

#### Scenario: Kline Update Received
- **WHEN** a new kline event is received via WebSocket
- **THEN** it is parsed and made available to the strategy engine.

### Requirement: Order Book Depth Tracking
The system SHALL maintain a local representation of the order book (L2 depth) for high-frequency decision making.

#### Scenario: Depth Snapshot Update
- **WHEN** a depth update event is received
- **THEN** the local order book state is updated accordingly.
