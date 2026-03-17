# VinBot Trading

VinBot is an algorithmic trading bot built with FastAPI and Python. It is designed to connect to the Binance API, retrieve market data over WebSockets, apply trading strategies (like RSI), execute orders, and provide real-time metrics back to a localized observability stack.

## Architecture & Features
- **FastAPI Core**: Lightweight and fast framework for the backend structure.
- **Binance Integration**: Sync server time, capture WebSocket streams, place market orders.
- **Risk Management**: Keep track of entries, daily PnL, circuit breakers, and Stop Loss / Take profit boundaries.
- **Observability Stack**: Full LGTM stack configuration out of the box using `docker-compose.yml`.
- **Telegram Notifications**: Event-driven alert system on trades and system thresholds.

## Requirements
- Docker & Docker Compose
- `.env` file containing (use `.env.example` as reference if applicable):
```
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key
BINANCE_BASE_URL=https://testnet.binance.vision
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
LOG_LEVEL=INFO
PROJECT_NAME=VinBot
DATABASE_URL=sqlite+aiosqlite:///data/vinbot.db
STOP_LOSS_PCT=1.5
TAKE_PROFIT_PCT=3.0
MAX_DAILY_LOSS_PCT=5.0
RSI_PERIOD=14
RSI_OVERSOLD=30
RSI_OVERBOUGHT=70
OTLP_ENDPOINT=http://tempo:4317
PROMETHEUS_METRICS_PATH=/metrics
```

## Running the Bot

Run the whole stack via `docker compose`:

```bash
docker compose up -d
```

### Checking Status
- **Grafana**: [http://localhost:3001](http://localhost:3001) - Includes automatically provisioned Dashboards for VinBot.
- **Prometheus**: [http://localhost:9090](http://localhost:9090)
- **Loki**: Running on `3101` (Internal default is `3100`)

## Changelog

### v1.1.0 - 2026-03-17
* **Added**: Integrated complete LGTM (Loki, Grafana, Tempo, Prometheus) observability stack using Docker setup.
* **Added**: OpenTelemetry instrumentation and custom Prometheus metrics within the FastAPI application (`app/core/metrics.py`, `app/core/observability.py`).
* **Added**: Dashboard provisioning in Grafana for VinBot RSI tracking and Daily PnL summary.
* **Changed**: Migrated dependency management from `requirements.txt` to `Poetry` (`pyproject.toml`).
* **Fixed**: Ignored `.env` file safely with `.gitignore`.
