import asyncio
import logging
from typing import Dict, Any
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.api.v1.router import api_router
from app.services.binance_client import binance_client
from app.services.market_data import market_service
from app.core.database import db
from app.services.risk_manager import risk_manager
from app.services.notifications import notification_service
from app.core.observability import setup_observability
from app.core.metrics import trading_rsi

settings = get_settings()

# Setup logging to both console and file
import os
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/bot.log")
    ]
)
logger = logging.getLogger(__name__)

from app.services.trading_engine import trading_engine
from app.services.indicators import get_symbol_data

from app.services.strategy_factory import current_strategy as rsi_strategy

async def dummy_strategy_callback(data: Dict[str, Any]):
    """Example callback for the trading loop."""
    symbol = data.get("s", "")
    kline = data.get("k", {})
    close_price = float(kline.get("c", 0))
    is_closed = kline.get("x", False)
    
    # Task 2.2: Real-time SL/TP check on every pricing tick
    risk_res = risk_manager.check_sl_tp(symbol, close_price)
    if risk_res and trading_engine.is_running:
        risk_signal = risk_res["signal"]
        pnl = risk_res["pnl"]
        logger.warning(f"RISK | Action {risk_signal} triggered for {symbol}")
        try:
            # Task 2.2: Notify risk BEFORE liquidation to explain why
            await notification_service.notify_risk(risk_signal, symbol, close_price, pnl)
            
            # Liquidate position immediately
            order = await trading_engine.place_market_order(symbol, "SELL", quantity=0.01, rsi=None)
            await rsi_strategy.update_position(symbol, False)
            await risk_manager.clear_entry_price(symbol)
            logger.info(f"RISK | Exit Order Successful: {order.get('orderId')}")
        except Exception as e:
            logger.error(f"RISK | Failed to liquidate {symbol}: {e}")

    if is_closed:
        # Task 2.3: Update indicator history on kline close
        symbol_data = get_symbol_data(symbol)
        symbol_data.add_close(close_price)
        rsi = symbol_data.get_rsi()
        
        if rsi:
            # Update Prometheus Gauge
            trading_rsi.labels(symbol=symbol).set(rsi)
            
            logger.info(f"Kline Closed | {symbol} RSI: {rsi:.2f}")
            # Task 4.1 & 4.2: Analyze and trigger orders
            signal = rsi_strategy.analyze(symbol)
            
            if signal and trading_engine.is_running:
                side = "BUY" if signal == "BUY" else "SELL"
                # Using a small fixed quantity for safety in Testnet
                quantity = 0.01 if "BTC" in symbol else 0.1 
                
                try:
                    logger.info(f"EXECUTION | Placing {side} order for {symbol} at {close_price}")
                    order = await trading_engine.place_market_order(symbol, side, quantity, rsi=rsi)
                    logger.info(f"EXECUTION | Order Success: {order.get('orderId')}")
                    # Task 4.3: Update position status in strategy
                    await rsi_strategy.update_position(symbol, side == "BUY")
                except Exception as e:
                    logger.error(f"EXECUTION | Order Failed for {symbol}: {e}")
        else:
            logger.info(f"Kline Closed | {symbol} (Waiting for more data...)")

    if not trading_engine.is_running:
        return
        
    # Periodic update (not necessarily every 2s to avoid spamming logs)
    # logger.info(f"Market Update | {symbol}: {close_price}")

async def run_trading_bot():
    """Background task for the trading engine."""
    logger.info("Starting Trading Bot background loop...")
    await binance_client.sync_time()
    
    symbols = settings.TRADING_SYMBOLS.split(",")
    
    # Task 1.3 & 2.3 & 3.1: Load initial risk state
    await rsi_strategy.load_initial_state(symbols)
    await risk_manager.load_initial_state(symbols)
    
    # Task 2.1 & 2.2: Warm-up historical data
    for symbol in symbols:
        logger.info(f"Warming up {symbol}...")
        historical_klines = await market_service.get_historical_klines(symbol, "1m", limit=100)
        symbol_data = get_symbol_data(symbol)
        for k in historical_klines:
            symbol_data.add_close(float(k[4]))
        logger.info(f"Warm-up complete for {symbol}. RSI: {symbol_data.get_rsi()}")

    tasks = []
    for symbol in symbols:
        tasks.append(market_service.stream_klines(symbol, "1m", dummy_strategy_callback))
    
    await asyncio.gather(*tasks)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Task 4.1: Startup - Init DB
    logger.info("Application starting up...")
    await db.connect()
    await notification_service.notify_status("ONLINE and monitoring markets")
    
    bot_task = asyncio.create_task(run_trading_bot())
    yield
    # Shutdown
    logger.info("Application shutting down...")
    await notification_service.notify_status("OFFLINE / shutting down")
    bot_task.cancel()
    await binance_client.close()
    await db.disconnect()

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# Task 1.2: Setup Observability (Prometheus + OTLP)
setup_observability(app)

app.include_router(api_router, prefix=settings.API_V1_STR)
