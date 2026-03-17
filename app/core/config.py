from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "VinBot Trading Core"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "secret"
    
    # Risk Management
    STOP_LOSS_PCT: float = 2.0
    TAKE_PROFIT_PCT: float = 5.0
    MAX_DAILY_LOSS_PCT: float = 5.0
    ENABLE_TRAILING_STOP: bool = True
    ATR_TRAILING_MULTIPLIER: float = 3.0
    
    # Notifications
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    # Binance Credentials
    BINANCE_API_KEY: str = ""
    BINANCE_SECRET_KEY: str = ""
    
    # Bot Config
    USE_TESTNET: bool = True
    TRADING_SYMBOLS: str = "BTCUSDT,ETHUSDT"
    LOG_LEVEL: str = "INFO"
    TRADING_STRATEGY: str = "RsiOnly" # RsiOnly | RsiWithDivergence | Auto | BollingerBands | MacdMaCross | Breakout
    BREAKOUT_VOLUME_MULTIPLIER: float = 1.5
    ENABLE_VOLUME_CONFIRMATION: bool = False
    VWAP_PERIOD: int = 50
    
    # Partial Take Profit Config
    # Format: "pnl_pct1:sell_pct1,pnl_pct2:sell_pct2"
    # Example: "5.0:50,10.0:25" -> At 5% gain sell 50% of the ORIGINAL size, at 10% gain sell 25% more.
    PARTIAL_TP_LEVELS: str = "5.0:50,10.0:25"
    MOVE_SL_TO_BE_ON_TP1: bool = True
    
    # BTC Directional Filter
    ENABLE_BTC_DIRECTIONAL_FILTER: bool = True
    BTC_DIRECTION_EMA: int = 200
    
    # Dynamic Position Sizing
    ENABLE_DYNAMIC_SIZING: bool = True
    ALLOCATED_CAPITAL: float = 1000.0
    RISK_PER_TRADE_PCT: float = 1.0
    
    # Relative Strength Filter
    ENABLE_RELATIVE_STRENGTH_FILTER: bool = True
    RS_LOOKBACK_PERIOD: int = 14
    
    # Persistence
    DATABASE_PATH: str = "data/vinbot.db"

    # Observability
    OTLP_ENDPOINT: str = "http://tempo:4317"
    PROMETHEUS_METRICS_PATH: str = "/metrics"

    @property
    def BINANCE_BASE_URL(self) -> str:
        return "https://testnet.binance.vision/api" if self.USE_TESTNET else "https://api.binance.com"

    @property
    def BINANCE_WS_URL(self) -> str:
        return "wss://stream.testnet.binance.vision/ws" if self.USE_TESTNET else "wss://stream.binance.com:9443/ws"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache()
def get_settings() -> Settings:
    return Settings()
