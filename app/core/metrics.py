from prometheus_client import Counter, Gauge, Histogram

# --- Business Metrics ---

# RSI Gauge per symbol
trading_rsi = Gauge(
    "vinbot_rsi",
    "Current RSI value",
    ["symbol"]
)

# Orders Counter
trading_orders_total = Counter(
    "vinbot_orders_total",
    "Total number of executed orders",
    ["symbol", "side"]
)

# Daily PnL Gauge
trading_pnl_daily = Gauge(
    "vinbot_pnl_daily",
    "Accumulated daily PnL in reference currency",
)

# Market Regime Gauge (0: Unknown, 1: Ranging, 2: Trending, 3: HighVol)
trading_market_regime = Gauge(
    "vinbot_market_regime",
    "Current market regime classification (1: Ranging, 2: Trending, 3: HighVol)",
    ["symbol"]
)

# --- Technical Metrics ---

# Binance API Latency
binance_api_latency = Histogram(
    "vinbot_binance_api_latency_seconds",
    "Latency of Binance API requests",
    ["endpoint", "method"]
)
