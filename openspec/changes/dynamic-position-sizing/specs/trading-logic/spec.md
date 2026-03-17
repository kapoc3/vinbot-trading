## ADDED Requirements

### Requirement: Risk-Based Sizing
Upon receiving a BUY signal, the execution flow MUST NOT use a hardcoded quantity.

#### Scenario: Normal Buy Flow
- **GIVEN** `ENABLE_DYNAMIC_SIZING` = True
- **AND** `ALLOCATED_CAPITAL` = `1000.0`
- **AND** `RISK_PER_TRADE_PCT` = `1.5`
- **AND** a `"BUY"` signal triggers for `ETHUSDT` at current price `$3000`.
- **AND** the calculated initial stop loss is `$2850` (5% distance).
- **WHEN** preparing the market order:
- **THEN** The total monetary risk allowed is `1000 * 0.015 = $15`.
- **AND** The risk per coin is `$3000 - $2850 = $150`.
- **AND** The unformatted targeted quantity MUST be calculated as `15 / 150 = 0.1 ETH`.

#### Scenario: Binance Precision Formatting
- **GIVEN** a calculated dynamic quantity of `1.1234567` for `SOLUSDT`.
- **AND** the cached Binance `exchangeInfo` indicates a `LOT_SIZE` stepSize of `0.01` for `SOLUSDT`.
- **WHEN** the final quantity is formulated for the API payload:
- **THEN** the quantity MUST be truncated precisely to `1.12`.
