## 1. Indicator Layer (Trend math)

- [x] 1.1 Implement True Range and ATR calculation in `app/services/indicators.py`.
- [x] 1.2 Implement core ADX (Average Directional Index) logic within `TechnicalIndicators` to detect trend intensity.
- [x] 1.3 Update `SymbolData` to store the historical indicators required (TR, +DM, -DM) to maintain steady ADX calculation.

## 2. Advanced Market Service

- [x] 2.1 Create `app/services/regime_service.py` to classify symbols into predefined regimes: `Ranging`, `Trending`, `HighVolatility`.
- [x] 2.2 Define the threshold logic for regime switching (ADX > 25, ATR relative spike detection).
- [x] 2.3 Implement logging in the regime service to notify of market "state changes".

## 3. Dynamic Strategy Orchestration

- [x] 3.1 Refactor `app/services/strategy_factory.py` to include an "Auto" mode that polls the `RegimeService`.
- [x] 3.2 Implement a "lock" mechanism ensuring strategies don't switch while a position is currently open for a symbol.
- [x] 3.3 Update `app/main.py` trade callback to call `strategy_manager.re-evaluate_regime()` on each closed kline.

## 4. Observability & Config

- [x] 4.1 Update `app/core/config.py` to support `TRADING_STRATEGY=Auto`.
- [x] 4.2 Expose current market regime via a new Prometheus Gauge for Grafana visualization.
