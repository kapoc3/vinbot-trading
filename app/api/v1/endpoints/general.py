from fastapi import APIRouter, Depends
from app.services.binance_client import binance_client
from app.services.account_manager import account_manager
from app.services.trading_engine import trading_engine
from typing import Dict, Any

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
async def get_bot_orders() -> Dict[str, Any]:
    """Task 6.1: Bot order history endpoint."""
    return {"orders": trading_engine.get_order_history()}
