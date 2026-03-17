## ADDED Requirements

### Requirement: Relative Strength Calculation
The system MUST calculate the Rate of Change (ROC) for a given symbol over a specified period.
- **Formula:** `ROC = ((Current Period Close - Prior Period Close) / Prior Period Close) * 100`
- **Graceful Failure:** If the requested prior period is out of bounds (insufficient data history), the calculation MUST safely return `None`.

### Requirement: Relative Strength Veto
The Strategy Proxy MUST veto `BUY` signals for altcoins if they are underperforming Bitcoin over the configured lookback window.

#### Scenario: Altcoin Outperforming Bitcoin
- **GIVEN** `ENABLE_RELATIVE_STRENGTH_FILTER` = True
- **AND** `RS_LOOKBACK_PERIOD` = `14`
- **AND** `SOLUSDT` triggers a `BUY` signal.
- **AND** `SOLUSDT`'s 14-period ROC is `5.5%`.
- **AND** `BTCUSDT`'s 14-period ROC is `2.1%`.
- **WHEN** the proxy validates the signal.
- **THEN** The proxy MUST allow the `BUY` signal to pass through.

#### Scenario: Altcoin Underperforming Bitcoin
- **GIVEN** `ENABLE_RELATIVE_STRENGTH_FILTER` = True
- **AND** `RS_LOOKBACK_PERIOD` = `14`
- **AND** `XRPUSDT` triggers a `BUY` signal.
- **AND** `XRPUSDT`'s 14-period ROC is `-1.2%`.
- **AND** `BTCUSDT`'s 14-period ROC is `3.0%`.
- **WHEN** the proxy validates the signal.
- **THEN** The proxy MUST veto the signal and return `None`.
- **AND** The proxy MUST log the veto reason indicating the RS underperformance.
