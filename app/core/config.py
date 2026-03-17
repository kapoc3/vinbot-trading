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
    
    # Notifications
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    # Binance Credentials
    BINANCE_API_KEY: str = ""
    BINANCE_SECRET_KEY: str = ""
    
    # Bot Config
    USE_TESTNET: bool = True
    TRADING_SYMBOLS: str = "BTCUSDT"
    LOG_LEVEL: str = "INFO"
    
    # Persistence
    DATABASE_PATH: str = "data/vinbot.db"

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
