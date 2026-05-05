import logging
import asyncio
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy import text
from app.core.config import get_settings
from app.core.database import db

settings = get_settings()
logger = logging.getLogger(__name__)


class RegressionService:
    def __init__(self):
        self.lookback_days = 30
        self.min_data_points = 100
        self.last_analysis = {}
        self.update_interval = 300
        self.tracked_symbols = set()
        
    async def init_symbols(self, symbols: List[str]):
        """Initialize tracking for symbols."""
        self.tracked_symbols = set(symbols)
        
    async def record_price(self, symbol: str, price: float, volume: float = 0.0):
        """Record a price point for analysis."""
        try:
            query = """
                INSERT INTO price_history (symbol, price, volume)
                VALUES (:symbol, :price, :volume)
            """
            await db.execute(query, {"symbol": symbol, "price": price, "volume": volume})
        except Exception as e:
            logger.error(f"Error recording price for {symbol}: {e}")
            
    async def cleanup_old_data(self):
        """Remove data older than lookback_days."""
        try:
            cutoff = datetime.utcnow() - timedelta(days=self.lookback_days)
            query = "DELETE FROM price_history WHERE timestamp < :cutoff"
            await db.execute(query, {"cutoff": cutoff})
            
            await self.ensure_partitions()
            
            logger.info(f"REGRESSION | Cleanup completed. Data older than {self.lookback_days} days removed.")
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")

    async def ensure_partitions(self):
        """Ensure partitions exist for next 3 months."""
        try:
            from datetime import datetime
            current = datetime.utcnow()
            
            for i in range(3):
                target_month = (current.month + i - 1) % 12 + 1
                target_year = current.year + (current.month + i - 1) // 12
                partition_name = f"price_history_p{target_year}_{target_month:02d}"
                
                next_month = target_month + 1
                next_year = target_year if next_month <= 12 else target_year + 1
                next_month = next_month if next_month <= 12 else 1
                
                try:
                    await db.execute(text(f"""
                        CREATE TABLE IF NOT EXISTS {partition_name}
                        PARTITION OF price_history 
                        FOR VALUES FROM ('{target_year}-{target_month:02d}-01') TO ('{next_year}-{next_month:02d}-01')
                    """))
                except Exception:
                    pass
                    
        except Exception as e:
            logger.error(f"Error ensuring partitions: {e}")

    async def calculate_regression(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Calculate linear regression on price history."""
        try:
            since = datetime.utcnow() - timedelta(days=self.lookback_days)
            query = """
                SELECT EXTRACT(EPOCH FROM (timestamp - :since)) as x, price as y
                FROM price_history
                WHERE symbol = :symbol AND timestamp >= :since
                ORDER BY timestamp ASC
            """
            result = await db.execute(query, {"symbol": symbol, "since": since})
            rows = result.fetchall()
            
            if len(rows) < self.min_data_points:
                logger.debug(f"Insufficient data for {symbol}: {len(rows)} points")
                return None
                
            x = np.array([float(row[0]) for row in rows])
            y = np.array([float(row[1]) for row in rows])
            
            x_normalized = (x - x.min()) / (x.max() - x.min() + 1e-10)
            
            coeffs = np.polyfit(x_normalized, y, 1)
            slope, intercept = coeffs
            
            y_pred = slope * x_normalized + intercept
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / (ss_tot + 1e-10))
            
            current_price = y[-1] if len(y) > 0 else 0
            avg_price = np.mean(y)
            
            normalized_slope = slope / avg_price * 100
            
            if normalized_slope > 0.5:
                signal = "UPTREND"
            elif normalized_slope < -0.5:
                signal = "DOWNTREND"
            else:
                signal = "SIDEWAYS"
                
            return {
                "symbol": symbol,
                "slope": float(slope),
                "intercept": float(intercept),
                "r_squared": float(r_squared),
                "normalized_slope": float(normalized_slope),
                "signal": signal,
                "current_price": float(current_price),
                "avg_price": float(avg_price),
                "data_points": len(rows)
            }
            
        except Exception as e:
            logger.error(f"Error calculating regression for {symbol}: {e}")
            return None

    async def analyze_all_symbols(self):
        """Analyze all tracked symbols."""
        results = {}
        for symbol in self.tracked_symbols:
            analysis = await self.calculate_regression(symbol)
            if analysis:
                results[symbol] = analysis
                await self.save_analysis(analysis)
        self.last_analysis = results
        return results

    async def save_analysis(self, analysis: Dict[str, Any]):
        """Save analysis to database for quick access."""
        try:
            query = """
                INSERT INTO regression_analysis 
                (symbol, slope, intercept, r_squared, signal, avg_price, normalized_slope, data_points, last_updated)
                VALUES (:symbol, :slope, :intercept, :r_squared, :signal, :avg_price, :normalized_slope, :data_points, NOW())
                ON CONFLICT (symbol) DO UPDATE SET 
                    slope = EXCLUDED.slope,
                    intercept = EXCLUDED.intercept,
                    r_squared = EXCLUDED.r_squared,
                    signal = EXCLUDED.signal,
                    avg_price = EXCLUDED.avg_price,
                    normalized_slope = EXCLUDED.normalized_slope,
                    data_points = EXCLUDED.data_points,
                    last_updated = NOW()
            """
            await db.execute(query, {
                "symbol": analysis["symbol"],
                "slope": analysis["slope"],
                "intercept": analysis["intercept"],
                "r_squared": analysis["r_squared"],
                "signal": analysis["signal"],
                "avg_price": analysis.get("avg_price", 0),
                "normalized_slope": analysis.get("normalized_slope", 0),
                "data_points": analysis.get("data_points", 0)
            })
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")

    async def get_buy_opportunity(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Determine if current price is a good buy opportunity based on regression."""
        analysis = await self.calculate_regression(symbol)
        
        if not analysis:
            return None
            
        current_price = analysis["current_price"]
        avg_price = analysis["avg_price"]
        
        price_deviation = ((current_price - avg_price) / avg_price) * 100
        
        is_oversold = analysis["signal"] == "DOWNTREND" and price_deviation < -5
        is_undervalued = price_deviation < -10
        
        if is_oversold or is_undervalued:
            return {
                "symbol": symbol,
                "buy_signal": True,
                "confidence": min(abs(price_deviation) / 10, 1.0),
                "current_price": current_price,
                "avg_price": avg_price,
                "deviation_pct": price_deviation,
                "trend": analysis["signal"],
                "r_squared": analysis["r_squared"]
            }
        
        return None

    def get_latest_analysis(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis for a symbol."""
        return self.last_analysis.get(symbol)


regression_service = RegressionService()