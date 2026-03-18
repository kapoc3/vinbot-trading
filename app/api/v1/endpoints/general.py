from fastapi import APIRouter, Depends
from app.services.binance_client import binance_client
from app.services.account_manager import account_manager
from app.services.trading_engine import trading_engine
from app.core.database import db
from app.services.risk_manager import risk_manager
from app.services.notifications import notification_service
from typing import Dict, Any, List

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Task 6.3: Health check reporting status."""
    return {
        "status": "healthy",
        "binance_url": binance_client.base_url,
        "time_offset_ms": binance_client.time_offset,
        "testnet": binance_client.base_url.find("testnet") != -1,
        "bot_running": trading_engine.is_running
    }

@router.post("/bot/start")
async def start_bot() -> Dict[str, str]:
    """Start the trading bot."""
    trading_engine.is_running = True
    return {"message": "Bot started"}

@router.post("/bot/stop")
async def stop_bot() -> Dict[str, str]:
    """Stop the trading bot (Requirement: Bot Control Endpoints)."""
    trading_engine.is_running = False
    return {"message": "Bot stopped"}

@router.get("/account/balance")
async def get_balance() -> Dict[str, Any]:
    """Task 6.1: Account balance endpoint."""
    return await account_manager.get_account_info()

@router.get("/bot/orders")
async def get_order_history() -> List[Dict[str, Any]]:
    """Get order history from memory."""
    return trading_engine.get_order_history()

@router.get("/bot/history")
async def get_persistent_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Task 4.3: Get order history from persistent database."""
    async with db.connection.execute(
        "SELECT * FROM orders ORDER BY timestamp DESC LIMIT ?", (limit,)
    ) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

@router.get("/bot/risk-status")
async def get_risk_status() -> Dict[str, Any]:
    """Task 4.2: Get current risk status and daily performance."""
    return {
        "daily_pnl": risk_manager.daily_pnl,
        "daily_loss_reached": risk_manager.daily_loss_reached,
        "entry_prices": risk_manager.entry_prices,
        "allowed_to_trade": risk_manager.is_trading_allowed()
    }

@router.get("/bot/performance")
async def get_performance_metrics() -> Dict[str, Any]:
    """Calculate overall model effectiveness from order history."""
    async with db.connection.execute("SELECT * FROM orders ORDER BY timestamp ASC") as cursor:
        rows = await cursor.fetchall()
        trades = [dict(row) for row in rows]
    
    if not trades:
        return {"message": "No trades recorded yet", "win_rate": 0, "total_pnl": 0}

    # Group orders into completed trades (Buy -> Sell)
    # This is a simplified version: assuming Spot Buy then Sell for win/loss
    realized_trades = []
    symbol_positions = {} # symbol -> last_buy_order
    
    total_pnl = 0.0
    wins = 0
    losses = 0
    
    for order in trades:
        symbol = order["symbol"]
        side = order["side"]
        price = order["price"]
        qty = order["quantity"]
        
        if side == "BUY":
            symbol_positions[symbol] = order
        elif side == "SELL" and symbol in symbol_positions:
            buy_order = symbol_positions.pop(symbol)
            pnl_val = (price - buy_order["price"]) * qty
            total_pnl += pnl_val
            if pnl_val > 0:
                wins += 1
            else:
                losses += 1
            realized_trades.append({
                "symbol": symbol,
                "pnl": pnl_val,
                "profit_pct": (price - buy_order["price"]) / buy_order["price"] * 100 if buy_order["price"] > 0 else 0
            })

    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    
    return {
        "total_orders": len(trades),
        "completed_trades": len(realized_trades),
        "wins": wins,
        "losses": losses,
        "win_rate_pct": round(win_rate, 2),
        "accumulated_pnl": round(total_pnl, 4),
        "average_pnl_per_trade": round(total_pnl / len(realized_trades), 4) if realized_trades else 0,
        "last_trades": realized_trades[-5:] # last 5 realized trades
    }

@router.post("/bot/force-trade")
async def force_trade(symbol: str, side: str, quantity: float) -> Dict[str, Any]:
    """Force a manual market order for testing purposes."""
    try:
        side_upper = side.upper()
        order = await trading_engine.place_market_order(symbol, side_upper, quantity)
        
        # Consistent State Management
        if side_upper == "BUY":
            price = float(order.get("price", 0) or order.get("fills", [{}])[0].get("price", 0))
            if price <= 0 and "fills" in order and order["fills"]:
                price = sum(float(f["price"]) * float(f["qty"]) for f in order["fills"]) / sum(float(f["qty"]) for f in order["fills"])
            await risk_manager.set_entry_price(symbol, price, quantity)
        elif side_upper == "SELL":
            await risk_manager.clear_entry_price(symbol)
            
        return {"status": "success", "order": order}
    except Exception as e:
        return {"status": "error", "message": str(e)}
