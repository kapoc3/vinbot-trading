from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "VinBot Trading Core"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "secret"
    
    # Dashboard Authentication
    DASHBOARD_USERNAME: str = "admin"
    DASHBOARD_PASSWORD: str = "admin"
    
    # Risk Management
    STOP_LOSS_PCT: float = 2.0
    TAKE_PROFIT_PCT: float = 5.0
    MAX_DAILY_LOSS_PCT: float = 5.0
    ENABLE_TRAILING_STOP: bool = True
    ATR_TRAILING_MULTIPLIER: float = 3.0
    TRAILING_STOP_PCT: float = 0.5  # 0.5% from peak (reasonable for crypto)
    
    # Notifications
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    # Binance Credentials
    BINANCE_API_KEY: str = ""
    BINANCE_SECRET_KEY: str = ""
    
    # Bot Config
    BINANCE_ENV: str = "prod" # prod | testnet | mock
    TRADING_SYMBOLS: str = "BTCUSDT,ETHUSDT"
    LOG_LEVEL: str = "INFO"
    TRADING_STRATEGY: str = "RsiOnly" # RsiOnly | RsiWithDivergence | Auto | BollingerBands | MacdMaCross | Breakout
    BREAKOUT_VOLUME_MULTIPLIER: float = 1.5
    ENABLE_VOLUME_CONFIRMATION: bool = False
    VWAP_PERIOD: int = 50
    
    # Partial Take Profit Config
    # Format: "pnl_pct1:sell_pct1,pnl_pct2:sell_pct2"
    # Example: "1.0:30,2.0:30,3.0:40" -> At 1% gain sell 30%, at 2% sell 30%, at 3% sell remaining 40%
    PARTIAL_TP_LEVELS: str = "1.0:30,2.0:30,3.0:40"
    MOVE_SL_TO_BE_ON_TP1: bool = True
    MIN_PROFIT_USD: float = 1.0  # Minimum profit in dollars to execute any sell
    
    # BTC Directional Filter
    ENABLE_BTC_DIRECTIONAL_FILTER: bool = True
    BTC_DIRECTION_EMA: int = 200
    
    # Dynamic Position Sizing
    ENABLE_DYNAMIC_SIZING: bool = True
    FIXED_ORDER_VALUE_USDT: float = 10.0
    ALLOCATED_CAPITAL: float = 1000.0
    RISK_PER_TRADE_PCT: float = 1.0
    
    # Technical Indicators
    RSI_PERIOD: int = 14
    RSI_OVERBOUGHT: float = 70.0
    RSI_OVERSOLD: float = 30.0
    
    # Relative Strength Filter
    ENABLE_RELATIVE_STRENGTH_FILTER: bool = True
    RS_LOOKBACK_PERIOD: int = 14
    
    # Advanced Exit Strategies
    # Trailing Take Profit
    ENABLE_TRAILING_TP: bool = True
    TRAILING_TP_ATR_MULTIPLIER: float = 2.0
    TRAILING_TP_ACTIVATION_PCT: float = 1.5

    # Time-Based Exit
    ENABLE_TIME_EXIT: bool = True
    MAX_HOLD_HOURS: int = 4
    TIME_EXIT_COOLDOWN_MINUTES: int = 15

    # Signal Strength Exit
    ENABLE_SIGNAL_STRENGTH_EXIT: bool = True

    # Dynamic Partial TP
    ENABLE_DYNAMIC_PARTIAL_TP: bool = True

    # Grid Trading Bot
    ENABLE_GRID_BOT: bool = False

    # Backtesting
    BACKTEST_CACHE_DIR: str = "data/backtest_cache"
    BACKTEST_INITIAL_CAPITAL: float = 1000.0
    BACKTEST_SLIPPAGE_MAJORS: float = 0.001  # 0.1%
    BACKTEST_SLIPPAGE_ALTS: float = 0.002   # 0.2%
    BACKTEST_COMMISSION: float = 0.001      # 0.1%
    BACKTEST_DEFAULT_DAYS: int = 365

    # Multi-Timeframe Analysis
    MULTI_TF_ENABLED: bool = True
    ACTIVE_TIMEFRAMES: str = "1m,15m,1h"  # Timeframes a monitorear
    MAX_CANDLES_PER_TF: int = 500
    MIN_CONFLUENCE_LEVEL: str = "MEDIA"   # ALTA, MEDIA, BAJA
    ALLOW_LOW_CONFLUENCE_TRADES: bool = False

    # ML Signals
    ML_ENABLED: bool = False
    ML_MODEL_PATH: str = "data/ml_models"
    ML_CONFIDENCE_THRESHOLD: float = 0.5
    ML_TRAIN_THRESHOLD_PCT: float = 2.0  # % movement to label as BUY/SELL
    ML_TRAIN_HORIZON: int = 10  # candles forward to check

    # Paper Trading
    PAPER_TRADING_ENABLED: bool = False
    PAPER_INITIAL_BALANCE: float = 10000.0
    PAPER_SLIPPAGE: float = 0.001  # 0.1% slippage simulation
    PAPER_COMMISSION: float = 0.001  # 0.1% commission simulation

    # Portfolio Rebalancing
    PORTFOLIO_REBALANCING_ENABLED: bool = False
    ALLOCATION_METHOD: str = "equal"  # equal, inverse_volatility, risk_weighted
    REBALANCE_THRESHOLD_PCT: float = 20.0  # Rebalance when position deviates 20%
    MAX_POSITION_PCT: float = 30.0  # Max 30% of portfolio per symbol
    MIN_POSITION_PCT: float = 5.0  # Min 5% of portfolio per symbol
    CORRELATION_THRESHOLD: float = 0.8  # Exclude if correlation > 0.8

    # Risk Analytics
    VAR_WINDOW: int = 30  # Days for VaR calculation
    VAR_CONFIDENCE: float = 0.95  # VaR confidence level
    MAX_DRAWDOWN_THRESHOLD: float = 0.20  # Alert if drawdown exceeds 20%
    ANALYTICS_ENABLED: bool = True

    GRID_SYMBOL: str = "SOLUSDT"
    GRID_LOWER_PRICE: float = 100.0
    GRID_UPPER_PRICE: float = 150.0
    GRID_GRID_COUNT: int = 10
    GRID_SPACING_PCT: float = 1.0
    
    # Persistence
    DATABASE_PATH: str = "data/vinbot.db"
    DB_HOST: str = "localhost"
    DB_USER: str = "vinbot"
    DB_PASSWORD: str = "vinbotpass"
    DB_PORT: int = 5432
    DB_NAME: str = "vinbot_db"

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        # For Docker, DB_HOST should be 'db'
        host = "db" if Path("/.dockerenv").exists() or Path("/run/.containerenv").exists() else self.DB_HOST
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{host}:{self.DB_PORT}/{self.DB_NAME}"
 
    # Observability
    OTLP_ENDPOINT: str = "http://tempo:4317"
    PROMETHEUS_METRICS_PATH: str = "/metrics"
    
    # Notification Toggles
    ENABLE_PERIODIC_REPORTS: bool = True
    REPORT_INTERVAL_SECONDS: int = 21600 # 6 hours
 
    # Binance URLs
    PROD_BASE_URL: str = "https://api.binance.com"
    PROD_WS_URL: str = "wss://stream.binance.com:9443/ws"
    TESTNET_BASE_URL: str = "https://testnet.binance.vision"
    TESTNET_WS_URL: str = "wss://stream.testnet.binance.vision/ws"
 
    @property
    def BINANCE_BASE_URL(self) -> str:
        return self.TESTNET_BASE_URL if self.BINANCE_ENV == "testnet" else self.PROD_BASE_URL
 
    @property
    def BINANCE_WS_URL(self) -> str:
        return self.TESTNET_WS_URL if self.BINANCE_ENV == "testnet" else self.PROD_WS_URL

    @property
    def USE_TESTNET(self) -> bool:
        """Alias for backward compatibility."""
        return self.BINANCE_ENV == "testnet"

    @property
    def USE_MOCK_BINANCE(self) -> bool:
        """Alias for backward compatibility."""
        return self.BINANCE_ENV == "mock"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache()
def get_settings() -> Settings:
    return Settings()
