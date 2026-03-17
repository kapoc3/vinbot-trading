import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from app.core.config import get_settings
from app.services.persistence import persistence
from app.services.notifications import notification_service
from app.core.metrics import trading_pnl_daily

settings = get_settings()
logger = logging.getLogger(__name__)

class RiskManager:
    """Centralize risk control logic (SL/TP/Daily Loss) with Partial Take Profit support."""
    
    def __init__(self):
        # entry_prices stores the average entry price for each symbol
        self.entry_prices: Dict[str, float] = {}
        # position_data stores quantity and TP level state
        # {symbol: {"initial_qty": float, "current_qty": float, "tp_hits": int, "sl_price": float}}
        self.position_data: Dict[str, Dict[str, Any]] = {}
        # daily_loss_reached is a circuit breaker flag
        self.daily_loss_reached: bool = False
        # daily_pnl stores cumulative profit/loss for the current day
        self.daily_pnl: float = 0.0
        self.last_reset_date: str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    async def load_initial_state(self, symbols: List[str]):
        """Load entry prices and daily loss status from persistence."""
        for symbol in symbols:
            key_p = f"{symbol.lower()}_entry_price"
            price = await persistence.get_state(key_p, 0.0)
            if price > 0:
                self.entry_prices[symbol] = float(price)
                
                # Recover position metadata
                key_meta = f"{symbol.lower()}_pos_meta"
                meta = await persistence.get_state(key_meta, {})
                if meta:
                    self.position_data[symbol] = meta
                else:
                    # Fallback for old states
                    self.position_data[symbol] = {
                        "initial_qty": 0.0,
                        "current_qty": 0.0,
                        "tp_hits": 0,
                        "sl_price": price * (1 - settings.STOP_LOSS_PCT / 100.0)
                    }
                logger.info(f"RISK | {symbol} recovered position: Price {price}, Meta {self.position_data[symbol]}")
        
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

    async def set_entry_price(self, symbol: str, price: float, quantity: float = 0.0):
        """Update and persist the entry price and initial quantity for a symbol."""
        self.entry_prices[symbol] = float(price)
        self.position_data[symbol] = {
            "initial_qty": float(quantity),
            "current_qty": float(quantity),
            "tp_hits": 0,
            "sl_price": float(price * (1 - settings.STOP_LOSS_PCT / 100.0))
        }
        await persistence.set_state(f"{symbol.lower()}_entry_price", price)
        await persistence.set_state(f"{symbol.lower()}_pos_meta", self.position_data[symbol])

    async def clear_entry_price(self, symbol: str):
        """Remove entry price and metadata after closing a position."""
        self.entry_prices.pop(symbol, None)
        self.position_data.pop(symbol, None)
        await persistence.set_state(f"{symbol.lower()}_entry_price", 0.0)
        await persistence.set_state(f"{symbol.lower()}_pos_meta", {})

    async def update_partial_execution(self, symbol: str, executed_qty: float):
        """Update state after a partial sell."""
        if symbol in self.position_data:
            data = self.position_data[symbol]
            data["current_qty"] = float(data["current_qty"]) - float(executed_qty)
            data["tp_hits"] = int(data["tp_hits"]) + 1
            
            # Requirement: Move SL to Break-Even on first TP
            if data["tp_hits"] == 1 and settings.MOVE_SL_TO_BE_ON_TP1:
                data["sl_price"] = float(self.entry_prices[symbol])
                logger.info(f"RISK | TP1 hit for {symbol}. Moving SL to BE: {data['sl_price']:.2f}")
            
            await persistence.set_state(f"{symbol.lower()}_pos_meta", data)

    def _get_tp_targets(self) -> List[tuple[float, float]]:
        """Parse PARTIAL_TP_LEVELS string into list of (pnl_pct, sell_pct_of_original)."""
        try:
            levels = []
            for part in settings.PARTIAL_TP_LEVELS.split(","):
                pnl, sell = part.split(":")
                levels.append((float(pnl), float(sell) / 100.0))
            return sorted(levels) # Ensure ascending order
        except Exception as e:
            logger.error(f"RISK | Error parsing PARTIAL_TP_LEVELS: {e}")
            return []

    def check_sl_tp(self, symbol: str, current_price: float) -> Optional[Dict[str, Any]]:
        """Check if Stop Loss, Partial Take Profit, or Final Take Profit is hit."""
        entry_price = self.entry_prices.get(symbol)
        pos_meta = self.position_data.get(symbol)
        
        if entry_price is None or pos_meta is None:
            return None

        pnl_pct = ((current_price - entry_price) / entry_price) * 100.0
        
        # 1. Check Hard Stop Loss (dynamic price)
        if current_price <= pos_meta["sl_price"]:
            logger.warning(f"RISK | STOP LOSS triggered for {symbol} at {current_price} (Price <= {pos_meta['sl_price']:.2f})")
            return {"signal": "STOP_LOSS", "pnl": pnl_pct, "quantity": pos_meta["current_qty"]}

        # 2. Check Partial Take Profits
        tp_levels = self._get_tp_targets()
        hit_count = pos_meta["tp_hits"]
        
        if hit_count < len(tp_levels):
            target_pnl, sell_fraction = tp_levels[hit_count]
            if pnl_pct >= target_pnl:
                sell_qty = pos_meta["initial_qty"] * sell_fraction
                # Ensure we don't try to sell more than we have (safety)
                sell_qty = min(sell_qty, pos_meta["current_qty"])
                
                logger.info(f"RISK | PARTIAL TP {hit_count+1} triggered for {symbol} at {current_price} (+{pnl_pct:.2f}%)")
                return {
                    "signal": "PARTIAL_TP", 
                    "pnl": pnl_pct, 
                    "quantity": sell_qty,
                    "is_final": False
                }
            
        # 3. Check Final Take Profit (Legacy/Global fallback if defined higher than levels)
        if pnl_pct >= settings.TAKE_PROFIT_PCT:
            logger.info(f"RISK | FINAL TAKE PROFIT reached for {symbol} at {current_price} (PnL: {pnl_pct:.2f}%)")
            return {"signal": "TAKE_PROFIT", "pnl": pnl_pct, "quantity": pos_meta["current_qty"], "is_final": True}
            
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
        """Check if new trades are allowed based on daily risk."""
        return not self.daily_loss_reached

# Global instance
risk_manager = RiskManager()
