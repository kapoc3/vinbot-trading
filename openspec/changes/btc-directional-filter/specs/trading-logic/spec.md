## ADDED Requirements

### Requirement: BTC Macro Veto Check
The strategy manager proxy MUST intercept and filter BUY signals using Bitcoin's trend as a global market indicator.

#### Scenario: Altcoin BUY signal during BTC downtrend
- **GIVEN** `ENABLE_BTC_DIRECTIONAL_FILTER` is set to `True`
- **AND** `BTC_DIRECTION_EMA` is set to `200`
- **AND** the current close price of `BTCUSDT` is *below* its 200-period EMA.
- **WHEN** any underlying strategy (e.g., RSI, Breakout) emits a `"BUY"` signal for *any* symbol (e.g., `ETHUSDT` or `SOLUSDT`)
- **THEN** the `DynamicStrategyProxy` MUST veto the signal and return `None`.
- **AND** log a message indicating the global BTC directional veto.

#### Scenario: Global BTC tracking
- **GIVEN** the user configures `TRADING_SYMBOLS="ETHUSDT,XRPUSDT"`
- **AND** `ENABLE_BTC_DIRECTIONAL_FILTER` is `True`
- **WHEN** the application starts up
- **THEN** `BTCUSDT` MUST be automatically added to the internal tracking list for historical warmup and websocket streaming, ensuring its indicator data is always fresh and available for the proxy to use.
