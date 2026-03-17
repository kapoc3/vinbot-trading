import logging
from typing import Dict, Any, List, Optional
from app.core.config import get_settings
from app.services.binance_client import binance_client
from app.services.persistence import persistence
from app.services.risk_manager import risk_manager
from app.services.notifications import notification_service
from app.core.metrics import trading_orders_total

logger = logging.getLogger(__name__)

class TradingEngine:
    def __init__(self):
        self.order_history = []
        self.is_running = False

    async def place_market_order(self, symbol: str, side: str, quantity: float, rsi: Optional[float] = None) -> Dict[str, Any]:
        """Place a MARKET order on Binance and persist the result."""
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": str(quantity)
        }
        try:
            logger.info(f"Placing {side} MARKET order for {quantity} {symbol}")
            order = await binance_client.request("POST", "/v3/order", params=params, signed=True)
            self.order_history.append(order)
            
            # Task 3.3: Save to persistent database
            await persistence.save_order(order, rsi=rsi)
            
            # Task 2.1: Notify via Telegram
            exec_price = float(order.get("price", 0) or order.get("fills", [{}])[0].get("price", 0))
            exec_qty = float(order.get("executedQty", quantity))
            await notification_service.notify_order(symbol, side, exec_price, exec_qty, rsi=rsi)
            
            # Prometheus Counter
            trading_orders_total.labels(symbol=symbol, side=side).inc()
            
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
