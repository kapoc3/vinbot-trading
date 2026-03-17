# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-03-17

### Added
- **Autonomous Market Regime Detection**: New `RegimeService` that classifies market states into `Trending`, `Ranging`, or `HighVolatility` using ADX and ATR indicators.
- **Dynamic Strategy Manager**: Implemented `StrategyManager` to orchestrate strategy switching at runtime without restarting the bot.
- **Bollinger Bands Strategy**: Added `BollingerBandsStrategy` specifically optimized for ranging markets, combining price band breaches with RSI confirmation.
- **MACD + MA Cross Strategy**: Added `MacdMaCrossStrategy` for heavy trending markets, featuring an EMA 200 trend filter and MACD signal crossovers.
- **Partial Take Profit (Scaled Exits)**: Added support for selling portions of a position at multiple profit targets (e.g., sell 50% at +5%, 25% at +10%).
- **Dynamic Position Sizing (Risk-Based)**: Algorithmic quantity calculation based on account risk (e.g., risk 1% of equity per trade), ensuring uniform portfolio impact across different assets.
- **BTC Directional Filter**: Global "Market Regime" veto that blocks long positions if Bitcoin is below its 200-period EMA, protecting against systemic crashes.
- **Break-Even Stop Loss**: Automatically moves the hard stop-loss to the entry price once the first profit target is hit, ensuring risk-free trades.
- **Volume Confirmation Filter**: Implemented a global veto layer using VWAP and OBV trend to filter out "fake" buy signals in low-liquidity environments.
- **Volatility Breakout Strategy**: Added `BreakoutStrategy` using Donchian Channels and volume confirmation to capture explosive moves at the start of new trends.
- **Dynamic ATR Trailing Stop**: New volatility-adjusted trailing stop mechanism that protects profits by following the price up at a distance of `3 * ATR` and forcing a sell on sharp reversals.
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
