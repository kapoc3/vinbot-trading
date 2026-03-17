import asyncio
import logging
import os
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
from app.services.trading_engine import trading_engine
from app.services.indicators import get_symbol_data
from app.services.strategy_factory import current_strategy as rsi_strategy, strategy_manager

settings = get_settings()

# Setup logging to both console and file
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

async def dummy_strategy_callback(data: Dict[str, Any]):
    """Main trading loop logic for processing incoming market data."""
    symbol = data.get("s", "")
    kline = data.get("k", {})
    close_price = float(kline.get("c", 0))
    is_closed = kline.get("x", False)
    
    if not trading_engine.is_running:
        return

    # 1. Real-time SL/TP/Partial check on every pricing tick
    risk_res = risk_manager.check_sl_tp(symbol, close_price)
    if risk_res:
        risk_signal = risk_res["signal"]
        pnl = risk_res["pnl"]
        qty_to_sell = risk_res["quantity"]
        is_final = risk_res.get("is_final", True) if risk_signal != "PARTIAL_TP" else False
        
        logger.warning(f"RISK | Action {risk_signal} triggered for {symbol}")
        try:
            # Notify risk BEFORE liquidation
            await notification_service.notify_risk(risk_signal, symbol, close_price, pnl)
            
            # Place the SELL order
            order = await trading_engine.place_market_order(symbol, "SELL", quantity=qty_to_sell, rsi=None)
            
            if risk_signal == "PARTIAL_TP":
                # Update partial state, move SL if needed
                await risk_manager.update_partial_execution(symbol, qty_to_sell)
                logger.info(f"RISK | Partial TP Order Successful: {order.get('orderId')}")
            else:
                # Final exit (SL or Final TP)
                await rsi_strategy.update_position(symbol, False)
                await risk_manager.clear_entry_price(symbol)
                logger.info(f"RISK | Exit Order Successful: {order.get('orderId')}")
                
        except Exception as e:
            logger.error(f"RISK | Failed to execute risk exit for {symbol}: {e}")

    # 2. Sequential Logic on Kline Close
    if is_closed:
        symbol_data = get_symbol_data(symbol)
        symbol_data.add_kline(kline)
        
        # Strategy management
        strategy_manager.re_evaluate_regime(symbol)
        rsi = symbol_data.get_rsi()
        
        if rsi:
            trading_rsi.labels(symbol=symbol).set(rsi)
            logger.info(f"Kline Closed | {symbol} RSI: {rsi:.2f}")
            
            # Analyze strategy signal
            # Note: signal handles trailing stop and volume confirmation internally via proxy
            signal = rsi_strategy.analyze(symbol)
            
            if signal:
                side = "BUY" if signal == "BUY" else "SELL"
                
                # Determine Quantity
                if side == "BUY":
                    # For BUY, we use a fixed safety quantity for now
                    quantity = 0.01 if "BTC" in symbol else 0.1
                else:
                    # For SELL, we must only sell what we actually have left in risk_manager
                    pos_meta = risk_manager.position_data.get(symbol)
                    if pos_meta:
                        quantity = pos_meta["current_qty"]
                    else:
                        # Fallback for unexpected states
                        quantity = 0.01 if "BTC" in symbol else 0.1

                try:
                    logger.info(f"EXECUTION | Placing {side} order for {symbol} at {close_price} (Qty: {quantity})")
                    order = await trading_engine.place_market_order(symbol, side, quantity, rsi=rsi)
                    
                    # Update local states
                    if side == "BUY":
                        # Binance filled price
                        entry_p = float(order.get("price", 0) or order.get("fills", [{}])[0].get("price", 0))
                        exec_qty = float(order.get("executedQty", quantity))
                        await risk_manager.set_entry_price(symbol, entry_p, exec_qty)
                        await rsi_strategy.update_position(symbol, True)
                    else:
                        await rsi_strategy.update_position(symbol, False)
                        await risk_manager.clear_entry_price(symbol)
                        
                    logger.info(f"EXECUTION | Order Success: {order.get('orderId')}")
                except Exception as e:
                    logger.error(f"EXECUTION | Order Failed for {symbol}: {e}")
        else:
            logger.info(f"Kline Closed | {symbol} (Waiting for more data...)")

async def run_trading_bot():
    """Background task for the trading engine initialization and symbol loop."""
    logger.info("Starting Trading Bot background loop...")
    await binance_client.sync_time()
    
    symbols = settings.TRADING_SYMBOLS.split(",")
    if settings.ENABLE_BTC_DIRECTIONAL_FILTER:
        if "BTCUSDT" not in symbols:
            logger.info("Initializing BTCUSDT for directional filter...")
            symbols.append("BTCUSDT")
    
    # Load initial states for recovery
    await rsi_strategy.load_initial_state(symbols)
    await risk_manager.load_initial_state(symbols)
    
    # Warm-up historical data
    for symbol in symbols:
        logger.info(f"Warming up {symbol}...")
        historical_klines = await market_service.get_historical_klines(symbol, "1m", limit=100)
        symbol_data = get_symbol_data(symbol)
        for k in historical_klines:
            # Kline arrays in Binance are [open_time, o, h, l, c, v, ...]
            symbol_data.add_kline({
                "c": k[4], "h": k[2], "l": k[3], "v": k[5]
            })
        logger.info(f"Warm-up complete for {symbol}. RSI: {symbol_data.get_rsi()}")

    tasks = []
    for symbol in symbols:
        tasks.append(market_service.stream_klines(symbol, "1m", dummy_strategy_callback))
    
    await asyncio.gather(*tasks)

@asynccontextmanager
async def lifespan(app: FastAPI):
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

# Setup Observability (Prometheus + OTLP)
setup_observability(app)

app.include_router(api_router, prefix=settings.API_V1_STR)
