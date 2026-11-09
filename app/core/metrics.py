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

# Wallet Balance Gauge
binance_wallet_balance = Gauge(
    "vinbot_wallet_balance",
    "Real-time wallet balance from Binance",
    ["asset"]
)

# --- ML & Quantitative Metrics ---

# ML Prediction Confidence Gauge
trading_ml_confidence = Gauge(
    "vinbot_ml_confidence",
    "Latest ML prediction confidence score (0.0 to 1.0)",
    ["symbol"]
)

# ML Predictions Counter
trading_ml_predictions_total = Counter(
    "vinbot_ml_predictions_total",
    "Total number of ML predictions emitted by class",
    ["symbol", "signal"]
)

# Position Multiplier Gauge (Ensemble + Multi-TF Confluence)
trading_position_multiplier = Gauge(
    "vinbot_position_multiplier",
    "Active position sizing multiplier from ML Ensemble and Multi-TF Confluence",
    ["symbol"]
)

# Smart Proxy Routing & Failover Metrics
binance_active_proxy_index = Gauge(
    "vinbot_binance_active_proxy_index",
    "Index of the currently active static proxy for signed Binance requests (-1 if direct)"
)

binance_proxy_failovers_total = Counter(
    "vinbot_binance_proxy_failovers_total",
    "Total number of automatic static proxy failover rotations"
)
