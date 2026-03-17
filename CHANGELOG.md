# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-03-17

### Added
- **Autonomous Market Regime Detection**: New `RegimeService` that classifies market states into `Trending`, `Ranging`, or `HighVolatility` using ADX and ATR indicators.
- **Dynamic Strategy Manager**: Implemented `StrategyManager` to orchestrate strategy switching at runtime without restarting the bot.
- **Bollinger Bands Strategy**: Added `BollingerBandsStrategy` specifically optimized for ranging markets, combining price band breaches with RSI confirmation.
- **MACD + MA Cross Strategy**: Added `MacdMaCrossStrategy` for heavy trending markets, featuring an EMA 200 trend filter and MACD signal crossovers.
- **Auto-Switching Mode**: Added `Auto` mode for `TRADING_STRATEGY` that automatically selects the best strategy based on the current market regime (MACD for ADX > 40, RSI Divergence for normal trends, Bollinger for ranges).
- **Strategy Safety Lock**: Implemented a locking mechanism that prevents strategy switching while a symbol has an open position to maintain trade consistency.
- **Regime Observability**: New Prometheus metric `trading_market_regime` to monitor current market classification in real-time.

### Changed
- Refactored `TechnicalIndicators` to include native Python implementations for ADX, ATR, and Bollinger Bands.
- Enhanced `SymbolData` to store multi-dimensional historical data (High, Low, Close, RSI).

## [1.1.0] - 2026-03-17

### Added
- Integrated complete LGTM (Loki, Grafana, Tempo, Prometheus) observability stack using Docker setup.
- OpenTelemetry instrumentation and custom Prometheus metrics.
- Dashboard provisioning in Grafana for VinBot RSI tracking and Daily PnL summary.

### Changed
- Migrated dependency management from `requirements.txt` to `Poetry` (`pyproject.toml`).

### Fixed
- Ignored `.env` file safely with `.gitignore`.
