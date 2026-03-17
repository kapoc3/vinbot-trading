## Requirements

### Requirement: Order Execution Notification
The system SHALL send a message to Telegram whenever a buy or sell order is successfully executed.

#### Format:
- `🚀 [SYMBOL] BUY | Price: [PRICE] | Qty: [QTY]`
- `💰 [SYMBOL] SELL | Price: [PRICE] | Qty: [QTY]`

### Requirement: Risk Management Alerts
The system SHALL send urgent alerts when risk protection mechanisms are triggered.

#### Scenarios:
- **Stop Loss**: `⚠️ STOP LOSS triggered for [SYMBOL] at [PRICE]`
- **Daily Limit**: `🛑 CIRCUIT BREAKER: Daily loss limit reached!`

### Requirement: System Status
The system SHALL notify upon startup and graceful shutdown.

#### Format:
- `🤖 VinBot is now ONLINE and monitoring markets.`
- `🔌 VinBot is shutting down.`
