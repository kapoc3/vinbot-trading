import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.core.config import get_settings
from app.services.persistence import persistence
from app.services.notifications import notification_service
from app.core.metrics import trading_pnl_daily

settings = get_settings()
logger = logging.getLogger(__name__)

class RiskManager:
    """Task 1.2: Centralize risk control logic (SL/TP/Daily Loss)."""
    
    def __init__(self):
        # entry_prices stores the average entry price for each symbol
        self.entry_prices: Dict[str, float] = {}
        # daily_loss_reached is a circuit breaker flag
        self.daily_loss_reached: bool = False
        # daily_pnl stores cumulative profit/loss for the current day
        self.daily_pnl: float = 0.0
        self.last_reset_date: str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    async def load_initial_state(self, symbols: list[str]):
        """Load entry prices and daily loss status from persistence."""
        for symbol in symbols:
            key = f"{symbol.lower()}_entry_price"
            price = await persistence.get_state(key, 0.0)
            if price > 0:
                self.entry_prices[symbol] = float(price)
                logger.info(f"RISK | {symbol} recovered entry price: {price}")
        
        # Check if daily loss limit was reached previously today
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if await persistence.get_state("last_reset_date") == today:
            self.daily_loss_reached = await persistence.get_state("daily_loss_reached", False)
            self.daily_pnl = await persistence.get_state("daily_pnl", 0.0)
        else:
            await self.reset_daily_stats()

    async def reset_daily_stats(self):
        """Reset daily PnL and circuit breaker at 00:00 UTC."""
        self.daily_pnl = 0.0
        trading_pnl_daily.set(0) # Reset Prometheus Gauge
        self.daily_loss_reached = False
        self.last_reset_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        await persistence.set_state("daily_loss_reached", False)
        await persistence.set_state("last_reset_date", self.last_reset_date)
        logger.info("RISK | Daily stats reset for new day.")
        await notification_service.notify_status("Daily stats reset for new day")

    async def set_entry_price(self, symbol: str, price: float):
        """Update and persist the entry price for a symbol."""
        self.entry_prices[symbol] = float(price)
        key = f"{symbol.lower()}_entry_price"
        await persistence.set_state(key, price)

    async def clear_entry_price(self, symbol: str):
        """Remove entry price after closing a position."""
        if symbol in self.entry_prices:
            del self.entry_prices[symbol]
        key = f"{symbol.lower()}_entry_price"
        await persistence.set_state(key, 0.0)

    def check_sl_tp(self, symbol: str, current_price: float) -> Optional[Dict[str, Any]]:
        """Task 2.2: Check if Stop Loss or Take Profit is hit."""
        entry_price = self.entry_prices.get(symbol)
        if not entry_price or entry_price == 0:
            return None

        pnl_pct = ((current_price - entry_price) / entry_price) * 100.0
        
        if pnl_pct <= -settings.STOP_LOSS_PCT:
            logger.warning(f"RISK | STOP LOSS triggered for {symbol} at {current_price} (PnL: {pnl_pct:.2f}%)")
            return {"signal": "STOP_LOSS", "pnl": pnl_pct}
            
        if pnl_pct >= settings.TAKE_PROFIT_PCT:
            logger.info(f"RISK | TAKE PROFIT reached for {symbol} at {current_price} (PnL: {pnl_pct:.2f}%)")
            return {"signal": "TAKE_PROFIT", "pnl": pnl_pct}
            
        return None

    async def update_daily_pnl(self, realized_pnl: float):
        """Track daily performance and trigger circuit breaker if needed."""
        self.daily_pnl += realized_pnl
        trading_pnl_daily.set(self.daily_pnl) # Update Prometheus Gauge
        await persistence.set_state("daily_pnl", self.daily_pnl)
        
        if self.daily_pnl < -settings.MAX_DAILY_LOSS_PCT * 100: # Simulating $100 units for now
            self.daily_loss_reached = True
            await persistence.set_state("daily_loss_reached", True)
            logger.error(f"RISK | CIRCUIT BREAKER! Daily loss limit reached: {self.daily_pnl:.2f}")
            await notification_service.notify_status(f"CIRCUIT BREAKER reached! Daily Loss: {self.daily_pnl:.2f}")

    def is_trading_allowed(self) -> bool:
        """Task 3.1: Check if new trades are allowed based on daily risk."""
        return not self.daily_loss_reached

# Global instance
risk_manager = RiskManager()
