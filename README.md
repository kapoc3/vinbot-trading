# VinBot Trading

VinBot is an algorithmic trading bot built with FastAPI and Python. It is designed to connect to the Binance API, retrieve market data over WebSockets, apply trading strategies (like RSI), execute orders, and provide real-time metrics back to a localized observability stack.

## Architecture & Features
- **FastAPI Core**: Lightweight and fast framework for the backend structure.
- **Binance Integration**: Sync server time, capture WebSocket streams, place market orders.
- **Autonomous Regime Detection**: Automatically classifies the market into `Trending`, `Ranging`, or `HighVolatility` using ADX and ATR.
- **Dynamic Strategy Orchestration**: Real-time strategy switching based on market conditions (RSI + Divergence for Trends, Bollinger Bands for Ranges).
- **Strategy Consistency Lock**: Safety mechanism to prevent strategy changes during active trades.
- **Observability Stack**: Full LGTM stack (Loki, Grafana, Tempo, Prometheus) for deep insights into bot performance.

## Requirements
- Docker & Docker Compose
- `.env` file containing (use `.env.example` as reference if applicable):
```
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key
# Strategy: RsiOnly, RsiWithDivergence, BollingerBands, or Auto
TRADING_STRATEGY=Auto
...
```

## Running the Bot

Run the whole stack via `docker compose`:

```bash
docker compose up -d
```

### Checking Status
- **Grafana**: [http://localhost:3001](http://localhost:3001) - Includes dashboards for PnL, Market Regime, and RSI.
- **Prometheus**: [http://localhost:9090](http://localhost:9090)

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for a full history of changes.
