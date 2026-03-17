import logging
from typing import Dict, Any, List
from app.services.binance_client import binance_client

logger = logging.getLogger(__name__)

class TradingEngine:
    def __init__(self):
        self.order_history = []
        self.is_running = False

    async def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """Place a market order (Task 4.1)."""
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": quantity
        }
        try:
            logger.info(f"Placing {side} MARKET order for {quantity} {symbol}")
            order = await binance_client.request("POST", "/v3/order", params=params, signed=True)
            self.order_history.append(order)
            return order
        except Exception as e:
            logger.error(f"Failed to place market order: {e}")
            raise e

    async def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an active order (Task 4.2)."""
        params = {
            "symbol": symbol,
            "orderId": order_id
        }
        try:
            logger.info(f"Cancelling order {order_id} for {symbol}")
            return await binance_client.request("DELETE", "/v3/order", params=params, signed=True)
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            raise e

    async def check_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Check status of an order (Requirement: Order Status Monitoring)."""
        params = {
            "symbol": symbol,
            "orderId": order_id
        }
        try:
            return await binance_client.request("GET", "/v3/order", params=params, signed=True)
        except Exception as e:
            logger.error(f"Failed to check order status: {e}")
            raise e

    def get_order_history(self) -> List[Dict[str, Any]]:
        """Return logical order history (Task 4.3)."""
        return self.order_history

trading_engine = TradingEngine()
