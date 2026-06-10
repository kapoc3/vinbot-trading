import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
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
        # {symbol: {"initial_qty": float, "current_qty": float, "tp_hits": int, "sl_price": float, "entry_time": datetime}}
        self.position_data: Dict[str, Dict[str, Any]] = {}
        # daily_loss_reached is a circuit breaker flag
        self.daily_loss_reached: bool = False
        # daily_pnl stores cumulative profit/loss for the current day
        self.daily_pnl: float = 0.0
        self.last_reset_date: str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        # Trailing TP state: {symbol: {"highest_price": float, "trailing_level": float, "is_active": bool, "activation_price": float}}
        self.trailing_tp_state: Dict[str, Dict[str, Any]] = {}
        # Time exit cooldown: {symbol: datetime}
        self.time_exit_cooldowns: Dict[str, datetime] = {}

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
            "sl_price": float(price * (1 - settings.STOP_LOSS_PCT / 100.0)),
            "entry_time": datetime.now(timezone.utc)
        }
        # Initialize trailing TP state for this symbol
        self.trailing_tp_state[symbol] = {
            "highest_price": 0.0,
            "trailing_level": 0.0,
            "is_active": False,
            "activation_price": 0.0
        }
        await persistence.set_state(f"{symbol.lower()}_entry_price", price)
        await persistence.set_state(f"{symbol.lower()}_pos_meta", self.position_data[symbol])
        await persistence.set_state(f"{symbol.lower()}_trailing_tp", self.trailing_tp_state[symbol])

    async def clear_entry_price(self, symbol: str):
        """Remove entry price and metadata after closing a position."""
        self.entry_prices.pop(symbol, None)
        self.position_data.pop(symbol, None)
        self.trailing_tp_state.pop(symbol, None)
        self.time_exit_cooldowns.pop(symbol, None)
        await persistence.set_state(f"{symbol.lower()}_entry_price", 0.0)
        await persistence.set_state(f"{symbol.lower()}_pos_meta", {})
        await persistence.set_state(f"{symbol.lower()}_trailing_tp", {})

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

    def check_sl_tp(self, symbol: str, current_price: float, atr: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Check if Stop Loss, Partial Take Profit, or Final Take Profit is hit."""
        entry_price = self.entry_prices.get(symbol)
        pos_meta = self.position_data.get(symbol)

        if entry_price is None or pos_meta is None or entry_price <= 0:
            return None

        pnl_pct = float(((current_price - entry_price) / entry_price) * 100.0)

        # 0. Update current price in position data for time exit calculation
        if symbol in self.position_data:
            self.position_data[symbol]["current_price"] = current_price

        # 1. Check Hard Stop Loss (dynamic price)
        sl_price = float(pos_meta.get("sl_price", 0.0))
        if current_price <= sl_price:
            logger.warning(f"RISK | STOP LOSS triggered for {symbol} at {current_price} (Price <= {sl_price:.2f})")
            return {"signal": "STOP_LOSS", "pnl": pnl_pct, "quantity": float(pos_meta.get("current_qty", 0.0))}

        # 1.5 Check Trailing Take Profit (if enabled)
        trailing_result = self.check_trailing_tp(symbol, current_price)
        if trailing_result:
            return trailing_result

        # 1.7 Check Time-Based Exit (if enabled)
        time_exit_result = self.check_time_exit(symbol)
        if time_exit_result:
            return time_exit_result

        # 1.8 Check RSI Divergence Exit (if enabled)
        divergence_exit_result = self.check_divergence_exit(symbol)
        if divergence_exit_result:
            return divergence_exit_result

        # 2. Check Partial Take Profits
        tp_levels = self._get_tp_targets()
        hit_count = int(pos_meta.get("tp_hits", 0))
        
        if hit_count < len(tp_levels):
            target_pnl, sell_fraction = tp_levels[hit_count]
            if pnl_pct >= target_pnl:
                sell_qty = float(pos_meta.get("initial_qty", 0.0)) * sell_fraction
                # Ensure we don't try to sell more than we have (safety)
                current_qty = float(pos_meta.get("current_qty", 0.0))
                sell_qty = min(sell_qty, current_qty)
                
                logger.info(f"RISK | PARTIAL TP {hit_count+1} triggered for {symbol} at {current_price} (+{pnl_pct:.2f}%)")
                return {
                    "signal": "PARTIAL_TP", 
                    "pnl": pnl_pct, 
                    "quantity": sell_qty,
                    "is_final": False
                }
            
        # 3. Check Final Take Profit (Legacy/Global fallback if defined higher than levels)
        if pnl_pct >= float(settings.TAKE_PROFIT_PCT):
            logger.info(f"RISK | FINAL TAKE PROFIT reached for {symbol} at {current_price} (PnL: {pnl_pct:.2f}%)")
            return {"signal": "TAKE_PROFIT", "pnl": pnl_pct, "quantity": float(pos_meta.get("current_qty", 0.0)), "is_final": True}
            
        return None

    async def update_daily_pnl(self, realized_pnl: float):
        """Track daily performance and trigger circuit breaker if needed."""
        self.daily_pnl += realized_pnl
        trading_pnl_daily.set(self.daily_pnl) # Update Prometheus Gauge
        await persistence.set_state("daily_pnl", self.daily_pnl)
        
        max_loss_limit = settings.ALLOCATED_CAPITAL * (settings.MAX_DAILY_LOSS_PCT / 100.0)
        if self.daily_pnl <= -max_loss_limit:
            self.daily_loss_reached = True
            await persistence.set_state("daily_loss_reached", True)
            logger.error(f"RISK | CIRCUIT BREAKER! Daily loss limit reached: {self.daily_pnl:.2f}")
            await notification_service.notify_status(f"CIRCUIT BREAKER reached! Daily Loss: {self.daily_pnl:.2f}")

    def is_trading_allowed(self) -> bool:
        """Check if new trades are allowed based on daily risk."""
        return not self.daily_loss_reached

    def calculate_position_size(self, symbol: str, entry_price: float, sl_price: float) -> float:
        """
        Calculate the quantity to purchase based on risk-per-trade.
        Formula: (Allocated Capital * Risk %) / (Entry Price - Stop Loss Price)
        """
        try:
            risk_pct = settings.RISK_PER_TRADE_PCT / 100.0
            capital_at_risk = settings.ALLOCATED_CAPITAL * risk_pct
            
            price_risk_per_unit = abs(entry_price - sl_price)
            
            if price_risk_per_unit <= 0:
                logger.error(f"RISK | Sizing failed for {symbol}: SL price {sl_price} is >= Entry {entry_price}")
                return 0.0
            
            raw_qty = capital_at_risk / price_risk_per_unit
            return float(raw_qty)
        except Exception as e:
            logger.error(f"RISK | Error calculating position size for {symbol}: {e}")
            return 0.0

    # ==================== TRAILING TAKE PROFIT ====================

    def should_check_trailing_tp(self, symbol: str) -> bool:
        """Check if trailing TP is enabled."""
        return settings.ENABLE_TRAILING_TP and symbol in self.entry_prices

    def activate_trailing_tp(self, symbol: str, current_price: float, atr: Optional[float] = None):
        """Activate trailing TP when profit threshold is reached."""
        if not settings.ENABLE_TRAILING_TP:
            return

        entry_price = self.entry_prices.get(symbol)
        if not entry_price:
            return

        pnl_pct = ((current_price - entry_price) / entry_price) * 100

        if pnl_pct >= settings.TRAILING_TP_ACTIVATION_PCT:
            atr_distance = (atr or (current_price * 0.01)) * settings.TRAILING_TP_ATR_MULTIPLIER
            trailing_level = current_price - atr_distance

            self.trailing_tp_state[symbol] = {
                "highest_price": current_price,
                "trailing_level": trailing_level,
                "is_active": True,
                "activation_price": current_price
            }
            logger.info(f"RISK | Trailing TP activated for {symbol} at {current_price:.2f} (pnl: {pnl_pct:.2f}%, trailing_level: {trailing_level:.2f})")

    def update_trailing_tp(self, symbol: str, current_price: float, atr: Optional[float] = None):
        """Update trailing TP level when price makes new high."""
        if symbol not in self.trailing_tp_state:
            return

        state = self.trailing_tp_state[symbol]
        if not state.get("is_active"):
            return

        if current_price > state["highest_price"]:
            atr_distance = (atr or (current_price * 0.01)) * settings.TRAILING_TP_ATR_MULTIPLIER
            new_trailing_level = current_price - atr_distance

            self.trailing_tp_state[symbol]["highest_price"] = current_price
            self.trailing_tp_state[symbol]["trailing_level"] = new_trailing_level
            logger.info(f"RISK | Trailing TP updated for {symbol}: new_high={current_price:.2f}, trailing_level={new_trailing_level:.2f}")

    def check_trailing_tp(self, symbol: str, current_price: float) -> Optional[Dict[str, Any]]:
        """Check if trailing TP is triggered."""
        if symbol not in self.trailing_tp_state:
            return None

        state = self.trailing_tp_state[symbol]
        if not state.get("is_active"):
            return None

        trailing_level = state.get("trailing_level", 0)

        if current_price <= trailing_level:
            entry_price = self.entry_prices.get(symbol, 0)
            pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
            qty = self.position_data.get(symbol, {}).get("current_qty", 0)

            logger.warning(f"RISK | TRAILING TP triggered for {symbol} at {current_price:.2f} (level: {trailing_level:.2f}, pnl: {pnl_pct:.2f}%)")

            # Deactivate trailing TP after trigger
            self.trailing_tp_state[symbol]["is_active"] = False

            return {"signal": "TRAILING_TP", "pnl": pnl_pct, "quantity": qty, "is_final": True}

        return None

    def clear_trailing_tp(self, symbol: str):
        """Clear trailing TP state when position is closed."""
        if symbol in self.trailing_tp_state:
            self.trailing_tp_state.pop(symbol, None)

    # ==================== TIME-BASED EXIT ====================

    def should_check_time_exit(self, symbol: str) -> bool:
        """Check if time-based exit is enabled and position exists."""
        return settings.ENABLE_TIME_EXIT and symbol in self.position_data

    def check_time_exit(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Check if position has exceeded max hold time."""
        if not settings.ENABLE_TIME_EXIT:
            return None

        pos_data = self.position_data.get(symbol)
        if not pos_data:
            return None

        entry_time = pos_data.get("entry_time")
        if not entry_time:
            return None

        # Check cooldown
        cooldown = self.time_exit_cooldowns.get(symbol)
        if cooldown and datetime.now(timezone.utc) < cooldown:
            return None

        now = datetime.now(timezone.utc)
        hours_held = (now - entry_time).total_seconds() / 3600

        if hours_held > settings.MAX_HOLD_HOURS:
            entry_price = self.entry_prices.get(symbol, 0)
            current_price = pos_data.get("current_price", entry_price)
            pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
            qty = pos_data.get("current_qty", 0)

            logger.warning(f"RISK | TIME EXIT triggered for {symbol} after {hours_held:.2f} hours (max: {settings.MAX_HOLD_HOURS})")

            # Set cooldown
            self.time_exit_cooldowns[symbol] = datetime.now(timezone.utc) + timedelta(minutes=settings.TIME_EXIT_COOLDOWN_MINUTES)

            return {"signal": "TIME_EXIT", "pnl": pnl_pct, "quantity": qty, "is_final": True}

        return None

    def is_in_cooldown(self, symbol: str) -> bool:
        """Check if symbol is in time exit cooldown."""
        cooldown = self.time_exit_cooldowns.get(symbol)
        if cooldown and datetime.now(timezone.utc) < cooldown:
            return True
        return False

    # ==================== SIGNAL STRENGTH EXIT ====================

    def classify_signal_strength(self, indicator_value: float, threshold: float, direction: str = "buy") -> str:
        """
        Classify signal strength based on distance from threshold.
        direction: 'buy' (oversold threshold) or 'sell' (overbought threshold)
        """
        if direction == "buy":
            distance = threshold - indicator_value  # How far below oversold
            if distance >= 10:  # RSI <= oversold - 10
                return "STRONG"
            elif distance >= 5:  # RSI <= oversold - 5
                return "MODERATE"
            else:  # RSI <= oversold but close
                return "WEAK"
        else:  # sell - distance above overbought
            distance = indicator_value - threshold
            if distance >= 10:
                return "STRONG"
            elif distance >= 5:
                return "MODERATE"
            else:
                return "WEAK"

    def get_adjusted_exit_threshold(self, symbol: str, base_threshold: float, direction: str = "sell") -> float:
        """Get exit threshold adjusted by signal strength."""
        pos_data = self.position_data.get(symbol, {})
        signal_strength = pos_data.get("signal_strength", "MODERATE")

        if direction == "sell":
            if signal_strength == "STRONG":
                return base_threshold  # Let it ride
            elif signal_strength == "MODERATE":
                return base_threshold - 5  # Exit earlier
            else:  # WEAK
                return base_threshold - 10  # Exit much earlier

        return base_threshold

    async def update_signal_strength(self, symbol: str, indicator_value: float, threshold: float, direction: str = "buy"):
        """Update signal strength classification for a position."""
        strength = self.classify_signal_strength(indicator_value, threshold, direction)
        if symbol in self.position_data:
            self.position_data[symbol]["signal_strength"] = strength
            await persistence.set_state(f"{symbol.lower()}_pos_meta", self.position_data[symbol])
            logger.info(f"RISK | Signal strength for {symbol}: {strength} (value: {indicator_value:.2f}, threshold: {threshold})")

    # ==================== RSI DIVERGENCE EXIT ====================

    def check_divergence_exit(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Check if bearish divergence signals exit."""
        if not settings.ENABLE_SIGNAL_STRENGTH_EXIT:
            return None

        if symbol not in self.position_data or symbol not in self.entry_prices:
            return None

        from app.services.indicators import get_symbol_data
        symbol_data = get_symbol_data(symbol)

        divergence = symbol_data.get_divergence(pivot_length=5)
        if divergence != "bearish_divergence":
            return None

        entry_price = self.entry_prices.get(symbol, 0)
        current_price = symbol_data.closes[-1] if symbol_data.closes else 0
        pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
        qty = self.position_data.get(symbol, {}).get("current_qty", 0)

        logger.warning(f"RISK | DIVERGENCE EXIT triggered for {symbol} (bearish divergence detected)")

        return {"signal": "DIVERGENCE_EXIT", "pnl": pnl_pct, "quantity": qty, "is_final": True}

    # ==================== DYNAMIC PARTIAL TP ====================

    def get_dynamic_tp_levels(self, symbol: str, entry_price: float, atr_pct: float) -> List[tuple[float, float]]:
        """Calculate dynamic TP levels based on volatility."""
        if not settings.ENABLE_DYNAMIC_PARTIAL_TP:
            return self._get_tp_targets()

        base_levels = self._get_tp_targets()
        if not base_levels:
            return []

        volatility_multiplier = 1.0

        if atr_pct > 2.0:
            volatility_multiplier = 1 + (atr_pct - 2) * 0.3
        elif atr_pct <= 1.0:
            volatility_multiplier = 0.8

        adjusted_levels = []
        for pnl_pct, sell_fraction in base_levels:
            adjusted_pnl = pnl_pct * volatility_multiplier
            adjusted_levels.append((adjusted_pnl, sell_fraction))

        logger.info(f"RISK | Dynamic TP Levels for {symbol}: Base {base_levels} -> Adjusted {adjusted_levels} (ATR%: {atr_pct:.2f}%)")

        return adjusted_levels

# Global instance
risk_manager = RiskManager()
