import logging
from app.services.rsi_strategy import RSIStrategy
from app.services.divergence_strategy import RsiDivergenceStrategy
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

def create_strategy():
    strategy_type = settings.TRADING_STRATEGY
    logger.info(f"STRATEGY | Initializing strategy: {strategy_type}")
    
    if strategy_type == "RsiWithDivergence":
        return RsiDivergenceStrategy()
    
    # Default is RsiOnly
    return RSIStrategy()

# Singleton for the entire bot session
current_strategy = create_strategy()
