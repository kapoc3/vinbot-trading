import logging
from typing import Dict, Any, Optional, List
from collections import defaultdict
from datetime import datetime, timezone
from app.core.database import db

logger = logging.getLogger(__name__)

class StatisticsService:
    """Comprehensive statistics and audit service for trading performance."""
    
    async def get_symbol_stats(self, symbol: str) -> Dict[str, Any]:
        """Get detailed statistics for a specific symbol."""
        try:
            query = """
                SELECT side, price, quantity, timestamp
                FROM orders
                WHERE symbol = :symbol
                ORDER BY timestamp ASC
            """
            result = await db.execute(query, {"symbol": symbol})
            orders = result.fetchall()
            
            if not orders:
                return {"symbol": symbol, "error": "No orders found"}
            
            trades = self._match_trades(orders)
            if not trades:
                return {"symbol": symbol, "error": "No completed trades"}
            
            wins = [t for t in trades if t["profit"] > 0]
            losses = [t for t in trades if t["profit"] <= 0]
            
            total_profit = sum(t["profit"] for t in trades)
            avg_profit = total_profit / len(trades) if trades else 0
            
            return {
                "symbol": symbol,
                "total_trades": len(trades),
                "winning_trades": len(wins),
                "losing_trades": len(losses),
                "win_rate": len(wins) / len(trades) if trades else 0,
                "total_profit": total_profit,
                "avg_profit": avg_profit,
                "avg_duration_minutes": self._avg_duration(trades),
                "best_trade": max(t["profit"] for t in trades) if trades else 0,
                "worst_trade": min(t["profit"] for t in trades) if trades else 0,
            }
        except Exception as e:
            logger.error(f"Error getting symbol stats: {e}")
            return {"error": str(e)}

    async def get_all_symbols_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics for all symbols."""
        try:
            query = "SELECT symbol, side, price, quantity, timestamp FROM orders ORDER BY timestamp ASC"
            result = await db.execute(query)
            orders = result.fetchall()
            
            if not orders:
                return {"error": "No orders found"}
            
            orders_by_symbol = defaultdict(list)
            for order in orders:
                orders_by_symbol[order[0]].append(order)
            
            all_trades = []
            symbol_stats = {}
            
            for symbol, sym_orders in orders_by_symbol.items():
                trades = self._match_trades(sym_orders)
                all_trades.extend(trades)
                
                if trades:
                    wins = [t for t in trades if t["profit"] > 0]
                    total_profit = sum(t["profit"] for t in trades)
                    symbol_stats[symbol] = {
                        "trades": len(trades),
                        "wins": len(wins),
                        "win_rate": len(wins) / len(trades) if trades else 0,
                        "total_profit": total_profit,
                    }
            
            if not all_trades:
                return {"error": "No completed trades"}
            
            wins = [t for t in all_trades if t["profit"] > 0]
            losses = [t for t in all_trades if t["profit"] <= 0]
            total_profit = sum(t["profit"] for t in all_trades)
            
            return {
                "total_trades": len(all_trades),
                "winning_trades": len(wins),
                "losing_trades": len(losses),
                "win_rate": len(wins) / len(all_trades) if all_trades else 0,
                "total_profit": total_profit,
                "avg_profit": total_profit / len(all_trades) if all_trades else 0,
                "drawdown": self._calculate_drawdown(all_trades),
                "avg_duration_minutes": self._avg_duration(all_trades),
                "commission_estimate": self._estimate_commissions(all_trades),
                "hourly_performance": self._hourly_performance(all_trades),
                "best_hour": self._best_hour(all_trades),
                "worst_hour": self._worst_hour(all_trades),
                "symbol_stats": symbol_stats,
            }
        except Exception as e:
            logger.error(f"Error getting all stats: {e}")
            return {"error": str(e)}

    def _match_trades(self, orders: List) -> List[Dict[str, Any]]:
        """Match BUY/SELL orders to create completed trades."""
        trades = []
        inventory = []
        
        for order in orders:
            side = order[1]
            price = order[2]
            qty = order[3]
            timestamp = order[4]
            
            if side == "BUY":
                inventory.append({"price": price, "quantity": qty, "timestamp": timestamp})
            elif side == "SELL" and inventory:
                sell_qty = qty
                sell_price = price
                trade_profit = 0
                trade_qty = 0
                
                while sell_qty > 0 and inventory:
                    buy = inventory[0]
                    if buy["quantity"] <= sell_qty:
                        trade_profit += (sell_price - buy["price"]) * buy["quantity"]
                        trade_qty += buy["quantity"]
                        sell_qty -= buy["quantity"]
                        inventory.pop(0)
                    else:
                        trade_profit += (sell_price - buy["price"]) * sell_qty
                        trade_qty += sell_qty
                        buy["quantity"] -= sell_qty
                        sell_qty = 0
                
                if trade_qty > 0:
                    duration = (timestamp - inventory[0]["timestamp"]).total_seconds() / 60 if inventory else 0
                    trades.append({
                        "profit": trade_profit,
                        "quantity": trade_qty,
                        "duration_minutes": duration if duration > 0 else 0,
                    })
        
        return trades

    def _avg_duration(self, trades: List[Dict]) -> float:
        """Calculate average trade duration in minutes."""
        if not trades:
            return 0
        return sum(t.get("duration_minutes", 0) for t in trades) / len(trades)

    def _calculate_drawdown(self, trades: List[Dict]) -> Dict[str, float]:
        """Calculate maximum drawdown from cumulative PnL."""
        cumulative = 0
        peak = 0
        max_dd = 0
        
        for trade in trades:
            cumulative += trade["profit"]
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd
        
        return {
            "max_drawdown": max_dd,
            "current_balance_approx": cumulative
        }

    def _estimate_commissions(self, trades: List[Dict], fee_pct: float = 0.1) -> Dict[str, float]:
        """Estimate total commissions paid (0.1% per trade Binance)."""
        total_volume = sum(t["quantity"] * (t.get("price", 0) or 0) for t in trades)
        estimated_fee = total_volume * (fee_pct / 100)
        
        return {
            "estimated_volume": total_volume,
            "estimated_commissions": estimated_fee,
            "fee_percentage": fee_pct
        }

    def _hourly_performance(self, trades: List[Dict]) -> Dict[int, Dict[str, Any]]:
        """Calculate performance by hour of day."""
        # Note: This is simplified - in production would need trade prices
        hourly = defaultdict(lambda: {"trades": 0, "profit": 0})
        # Placeholder - would need actual timestamps matched
        return dict(hourly)

    def _best_hour(self, trades: List[Dict]) -> Optional[int]:
        """Find the best performing hour."""
        return 14  # Placeholder - would calculate from real data

    def _worst_hour(self, trades: List[Dict]) -> Optional[int]:
        """Find the worst performing hour."""
        return 2  # Placeholder - would calculate from real data

    async def get_performance_report(self) -> str:
        """Generate a formatted performance report."""
        stats = await self.get_all_symbols_stats()
        
        if "error" in stats:
            return f"Error: {stats['error']}"
        
        lines = [
            "📊 *Performance Report*",
            "",
            f"Total Trades: `{stats['total_trades']}`",
            f"Win Rate: `{stats['win_rate']*100:.1f}%`",
            f"Total Profit: `${stats['total_profit']:.2f}`",
            f"Avg Profit/Trade: `${stats['avg_profit']:.2f}`",
            f"Avg Duration: `{stats['avg_duration_minutes']:.1f} min`",
            "",
            f"📉 Max Drawdown: `${stats['drawdown']['max_drawdown']:.2f}`",
            f"💰 Est. Commissions: `${stats['commission_estimate']['estimated_commissions']:.2f}`",
            "",
            "📈 *By Symbol:*",
        ]
        
        for symbol, sym_stats in stats.get("symbol_stats", {}).items():
            emoji = "🟢" if sym_stats["total_profit"] > 0 else "🔴"
            lines.append(f"{emoji} {symbol}: {sym_stats['trades']} trades, ${sym_stats['total_profit']:.2f}")
        
        return "\n".join(lines)

    async def save_trade_stats(self, symbol: str, regime: str, strategy: str, 
                                 entry_price: float, exit_price: float, quantity: float,
                                 profit: float, duration_minutes: int):
        """Save individual trade statistics for learning."""
        try:
            profit_pct = ((exit_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
            now = datetime.now(timezone.utc)
            hour = now.hour
            day = now.weekday()
            
            query = """
                INSERT INTO trade_stats 
                (symbol, regime, strategy, entry_price, exit_price, quantity, profit, profit_pct, duration_minutes, hour_of_day, day_of_week)
                VALUES (:symbol, :regime, :strategy, :entry_price, :exit_price, :quantity, :profit, :profit_pct, :duration, :hour, :day)
            """
            await db.execute(query, {
                "symbol": symbol,
                "regime": regime,
                "strategy": strategy,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "quantity": quantity,
                "profit": profit,
                "profit_pct": profit_pct,
                "duration": duration_minutes,
                "hour": hour,
                "day": day
            })
            logger.info(f"STATS | Saved trade stats for {symbol}: profit {profit:.2f}")
        except Exception as e:
            logger.error(f"Error saving trade stats: {e}")

    async def update_symbol_performance(self):
        """Update symbol performance cache from trade_stats."""
        try:
            query = """
                INSERT INTO symbol_performance (symbol, total_trades, winning_trades, win_rate, total_profit, avg_profit, avg_duration_minutes, last_updated)
                SELECT 
                    symbol,
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as winning_trades,
                    AVG(CASE WHEN profit > 0 THEN 1.0 ELSE 0.0 END) as win_rate,
                    SUM(profit) as total_profit,
                    AVG(profit) as avg_profit,
                    AVG(duration_minutes) as avg_duration,
                    NOW()
                FROM trade_stats
                GROUP BY symbol
                ON CONFLICT (symbol) DO UPDATE SET
                    total_trades = EXCLUDED.total_trades,
                    winning_trades = EXCLUDED.winning_trades,
                    win_rate = EXCLUDED.win_rate,
                    total_profit = EXCLUDED.total_profit,
                    avg_profit = EXCLUDED.avg_profit,
                    avg_duration_minutes = EXCLUDED.avg_duration_minutes,
                    last_updated = EXCLUDED.last_updated
            """
            await db.execute(query)
            logger.info("STATS | Updated symbol performance cache")
        except Exception as e:
            logger.error(f"Error updating symbol performance: {e}")

    async def update_hourly_performance(self):
        """Update hourly performance cache."""
        try:
            query = """
                INSERT INTO hourly_performance (hour, total_trades, avg_profit, win_rate, last_updated)
                SELECT 
                    hour_of_day,
                    COUNT(*) as total_trades,
                    AVG(profit) as avg_profit,
                    AVG(CASE WHEN profit > 0 THEN 1.0 ELSE 0.0 END) as win_rate,
                    NOW()
                FROM trade_stats
                GROUP BY hour_of_day
                ON CONFLICT (hour) DO UPDATE SET
                    total_trades = EXCLUDED.total_trades,
                    avg_profit = EXCLUDED.avg_profit,
                    win_rate = EXCLUDED.win_rate,
                    last_updated = EXCLUDED.last_updated
            """
            await db.execute(query)
            logger.info("STATS | Updated hourly performance cache")
        except Exception as e:
            logger.error(f"Error updating hourly performance: {e}")

    async def get_learned_veto_data(self) -> Dict[str, Any]:
        """Get learned data for smart veto decisions."""
        try:
            # Best hours
            result = await db.execute("SELECT hour, win_rate, avg_profit FROM hourly_performance ORDER BY win_rate DESC LIMIT 5")
            best_hours = [{"hour": r[0], "win_rate": r[1], "avg_profit": r[2]} for r in result.fetchall()]
            
            # Worst hours
            result = await db.execute("SELECT hour, win_rate, avg_profit FROM hourly_performance ORDER BY win_rate ASC LIMIT 5")
            worst_hours = [{"hour": r[0], "win_rate": r[1], "avg_profit": r[2]} for r in result.fetchall()]
            
            # Best symbols
            result = await db.execute("SELECT symbol, win_rate, total_profit, avg_profit FROM symbol_performance ORDER BY total_profit DESC LIMIT 5")
            best_symbols = [{"symbol": r[0], "win_rate": r[1], "total_profit": r[2], "avg_profit": r[3]} for r in result.fetchall()]
            
            # Worst symbols
            result = await db.execute("SELECT symbol, win_rate, total_profit, avg_profit FROM symbol_performance WHERE total_trades >= 5 ORDER BY win_rate ASC LIMIT 5")
            worst_symbols = [{"symbol": r[0], "win_rate": r[1], "total_profit": r[2], "avg_profit": r[3]} for r in result.fetchall()]
            
            return {
                "best_hours": best_hours,
                "worst_hours": worst_hours,
                "best_symbols": best_symbols,
                "worst_symbols": worst_symbols,
            }
        except Exception as e:
            logger.error(f"Error getting learned veto data: {e}")
            return {}
        
        return "\n".join(lines)

statistics_service = StatisticsService()