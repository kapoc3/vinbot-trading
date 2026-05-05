import logging
import asyncio
from typing import Dict, Any, List, Optional
from app.core.config import get_settings
from app.services.binance_client import binance_client
from app.services.notifications import notification_service

settings = get_settings()
logger = logging.getLogger(__name__)


class GridBot:
    def __init__(self):
        self.symbol = ""
        self.grid_levels = []
        self.grid_spacing_pct = 1.0
        self.grid_count = 10
        self.total_capital = 0.0
        self.qty_per_grid = 0.0
        self.is_running = False
        self.active_orders = {}
        self.profit_per_trade = {}
        self.commission_pct = 0.001  # 0.1% Binance commission
        
    def initialize(self, symbol: str, lower_price: float, upper_price: float, grid_count: int, current_price: float = None):
        self.symbol = symbol
        self.grid_count = grid_count
        
        if current_price and current_price < upper_price:
            center_price = current_price
            range_pct = 0.15
            lower_price = current_price * (1 - range_pct)
            upper_price = current_price * (1 + range_pct)
            logger.info(f"GRID | Auto-adjusted grid to current price {current_price}: {lower_price:.2f} - {upper_price:.2f}")
        
        self.grid_spacing_pct = (upper_price - lower_price) / lower_price / grid_count
        
        self.grid_levels = []
        price_range = upper_price - lower_price
        step = price_range / grid_count
        
        for i in range(grid_count):
            self.grid_levels.append({
                "price": lower_price + (step * i),
                "buy_order_id": None,
                "sell_order_id": None,
                "filled": False
            })
        
        self.is_running = True
        logger.info(f"GRID | Initialized {grid_count} levels for {symbol} between {lower_price:.2f} and {upper_price:.2f}")

    async def calculate_position_size(self) -> float:
        try:
            quote_asset = "USDC" if "USDC" in self.symbol else "USDT"
            balance_info = await binance_client.get_asset_balance(quote_asset)
            available_balance = float(balance_info.get("free", 0.0))
            logger.info(f"GRID | Available {quote_asset} balance: {available_balance}")
            
            if available_balance < 10:
                logger.warning(f"GRID | Insufficient {quote_asset} balance: {available_balance}")
                return 0.0
            
            # Get min notional from exchange info
            min_notional = 5.0
            try:
                info = await binance_client.request("GET", "/api/v3/exchangeInfo", params={"symbol": self.symbol})
                symbol_data = next((s for s in info["symbols"] if s["symbol"] == self.symbol), None)
                if symbol_data:
                    notional_filter = next((f for f in symbol_data.get("filters", []) if f.get("filterType") == "NOTIONAL"), None)
                    if notional_filter:
                        min_notional = float(notional_filter.get("minNotional", 5.0))
                        logger.info(f"GRID | Min notional: {min_notional}")
            except Exception as e:
                logger.warning(f"GRID | Could not get min notional: {e}")
            
            self.total_capital = min(available_balance * 0.5, 100.0)
            
            if not self.grid_levels or self.grid_levels[0]["price"] <= 0:
                logger.error(f"GRID | Invalid grid levels or price")
                return 0.0
            
            # Calculate qty to meet min notional
            qty = self.total_capital / self.grid_count / self.grid_levels[0]["price"]
            qty = max(qty, min_notional / self.grid_levels[0]["price"])
            
            self.qty_per_grid = qty
            logger.info(f"GRID | Qty per grid: {self.qty_per_grid}, Capital: {self.total_capital}, Grid levels: {len(self.grid_levels)}")
            return self.qty_per_grid
        except Exception as e:
            logger.error(f"GRID | Error calculating position size: {e}")
            return 0.0

    async def place_grid_orders(self):
        if not self.grid_levels:
            return
            
        await self.calculate_position_size()
        lot_info = await binance_client.get_exchange_info(self.symbol)
        step_size = float(lot_info.get("stepSize", 0.000001))
        
        # Get price precision from exchange info
        try:
            info = await binance_client.request("GET", "/api/v3/exchangeInfo", params={"symbol": self.symbol})
            symbol_data = next((s for s in info["symbols"] if s["symbol"] == self.symbol), None)
            price_precision = symbol_data.get("pricePrecision", 2) if symbol_data else 2
            price_filter = next((f for f in symbol_data.get("filters", []) if f.get("filterType") == "PRICE_FILTER"), {})
            tick_size = float(price_filter.get("tickSize", "0.01"))
        except Exception as e:
            logger.warning(f"GRID | Could not get price precision: {e}")
            price_precision = 2
            tick_size = 0.01
        
        for i, level in enumerate(self.grid_levels):
            if level["filled"]:
                continue
            
            qty = binance_client.round_step(self.qty_per_grid, step_size)
            
            # Round price to correct precision
            price = round(level["price"] / tick_size) * tick_size
            price = round(price, price_precision)
            
            try:
                buy_params = {
                    "symbol": self.symbol,
                    "side": "BUY",
                    "type": "LIMIT",
                    "price": str(price),
                    "quantity": str(qty),
                    "timeInForce": "GTC"
                }
                
                order = await binance_client.request("POST", "/v3/order", params=buy_params, signed=True)
                level["buy_order_id"] = int(order["orderId"])
                self.active_orders[order["orderId"]] = {"level": i, "side": "BUY", "qty": qty, "price": level["price"]}
                
                logger.info(f"GRID | Placed BUY order at level {i}: {level['price']} for {qty}")
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"GRID | Failed to place buy order at level {i}: {e}")

    async def check_order_fills(self, current_price: float):
        to_remove = []
        
        for order_id, order_info in self.active_orders.items():
            try:
                params = {"symbol": self.symbol, "orderId": order_id}
                order_status = await binance_client.request("GET", "/v3/order", params=params, signed=True)
                
                if order_status["status"] == "FILLED":
                    level_idx = order_info["level"]
                    qty = float(order_info["qty"])
                    buy_price = float(order_info["price"])
                    
                    # Calculate sell price accounting for commission (0.1% buy + 0.1% sell)
                    gross_profit_pct = self.grid_spacing_pct * 2
                    net_profit_pct = gross_profit_pct - (self.commission_pct * 2)
                    sell_price = buy_price * (1 + net_profit_pct)
                    
                    # Round sell price to correct precision
                    try:
                        info = await binance_client.request("GET", "/api/v3/exchangeInfo", params={"symbol": self.symbol})
                        symbol_data = next((s for s in info["symbols"] if s["symbol"] == self.symbol), None)
                        price_precision = symbol_data.get("pricePrecision", 2) if symbol_data else 2
                        price_filter = next((f for f in symbol_data.get("filters", []) if f.get("filterType") == "PRICE_FILTER"), {})
                        tick_size = float(price_filter.get("tickSize", "0.01"))
                        sell_price = round(sell_price / tick_size) * tick_size
                        sell_price = round(sell_price, price_precision)
                    except Exception:
                        sell_price = round(sell_price, 2)
                    
                    # Ensure minimum profit after fees
                    if net_profit_pct <= 0:
                        logger.warning(f"GRID | Not enough spread to cover fees. Skipping sell.")
                        continue
                    
                    lot_info = await binance_client.get_exchange_info(self.symbol)
                    step_size = float(lot_info.get("stepSize", 0.000001))
                    sell_qty = binance_client.round_step(qty, step_size)
                    
                    sell_params = {
                        "symbol": self.symbol,
                        "side": "SELL",
                        "type": "LIMIT",
                        "price": str(sell_price),
                        "quantity": str(sell_qty),
                        "timeInForce": "GTC"
                    }
                    
                    sell_order = await binance_client.request("POST", "/v3/order", params=sell_params, signed=True)
                    self.active_orders[order_id]["sell_order_id"] = int(sell_order["orderId"])
                    self.active_orders[order_id]["status"] = "waiting_sell"
                    
                    profit = (sell_price - buy_price) * qty
                    self.profit_per_trade[order_id] = profit
                    
                    logger.info(f"GRID | BUY filled at {buy_price}. Placed SELL at {sell_price}. Est profit: {profit:.4f}")
                    
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"GRID | Error checking order {order_id}: {e}")

    async def check_sell_fills(self):
        to_remove = []
        
        for order_id, order_info in list(self.active_orders.items()):
            if order_info.get("status") != "waiting_sell" or not order_info.get("sell_order_id"):
                continue
                
            try:
                params = {"symbol": self.symbol, "orderId": order_info["sell_order_id"]}
                order_status = await binance_client.request("GET", "/v3/order", params=params, signed=True)
                
                if order_status["status"] == "FILLED":
                    profit = self.profit_per_trade.get(order_id, 0)
                    
                    base_asset = self.symbol.replace("USDT", "").replace("USDC", "")
                    await notification_service.send_message(
                        f"🟢 *Grid Trade Closed*\n"
                        f"Symbol: `{self.symbol}`\n"
                        f"Profit: `${profit:.4f}`\n"
                        f"Status: SELL filled"
                    )
                    
                    to_remove.append(order_id)
                    logger.info(f"GRID | SELL filled. Profit: ${profit:.4f}")
                    
            except Exception as e:
                logger.error(f"GRID | Error checking sell order: {e}")
        
        for order_id in to_remove:
            self.active_orders.pop(order_id, None)
            self.profit_per_trade.pop(order_id, None)

    async def cancel_all_orders(self):
        try:
            params = {"symbol": self.symbol}
            open_orders = await binance_client.request("GET", "/v3/openOrders", params=params, signed=True)
            
            for order in open_orders:
                await binance_client.request("DELETE", "/v3/order", params={"symbol": self.symbol, "orderId": order["orderId"]}, signed=True)
                logger.info(f"GRID | Cancelled order {order['orderId']}")
            
            self.active_orders.clear()
            
        except Exception as e:
            logger.error(f"GRID | Error cancelling orders: {e}")

    def get_status(self) -> Dict[str, Any]:
        total_profit = sum(self.profit_per_trade.values())
        return {
            "symbol": self.symbol,
            "is_running": self.is_running,
            "active_orders": len(self.active_orders),
            "total_profit": total_profit,
            "grid_count": self.grid_count
        }


grid_bot = GridBot()