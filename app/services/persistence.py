import json
import logging
from typing import Any, Optional, Dict
from app.core.database import db

logger = logging.getLogger(__name__)

class PersistenceService:
    """Task 2.1 & 2.2: Repository for state and order persistence."""
    
    async def set_state(self, key: str, value: Any):
        """Save a key-value state to bot_state table."""
        # Serialize to JSON string to handle arbitrary types
        json_val = json.dumps(value)
        await db.connection.execute(
            "INSERT OR REPLACE INTO bot_state (key, value) VALUES (?, ?)",
            (key, json_val)
        )
        await db.connection.commit()

    async def get_state(self, key: str, default: Any = None) -> Any:
        """Retrieve a key-value state from bot_state table."""
        async with db.connection.execute(
            "SELECT value FROM bot_state WHERE key = ?", (key,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return json.loads(row["value"])
        return default

    async def save_order(self, order_data: Dict[str, Any], rsi: Optional[float] = None):
        """Save executed order details to orders table."""
        try:
            await db.connection.execute(
                """
                INSERT INTO orders (order_id, symbol, side, price, quantity, rsi)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    order_data.get("orderId"),
                    order_data.get("symbol"),
                    order_data.get("side"),
                    float(order_data.get("price", 0) or order_data.get("fills", [{}])[0].get("price", 0)),
                    float(order_data.get("executedQty", 0) or order_data.get("origQty", 0)),
                    rsi
                )
            )
            await db.connection.commit()
            logger.info(f"Persistent storage: Order {order_data.get('orderId')} saved.")
        except Exception as e:
            logger.error(f"Failed to save order to persistence: {e}")

# Global instance
persistence = PersistenceService()
