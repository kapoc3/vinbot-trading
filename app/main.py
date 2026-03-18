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
            # 1.1 Calculate Realized Units for PnL (Estimated)
            # PnL = (ClosePrice - EntryPrice) * Quantity
            entry_p = risk_manager.entry_prices.get(symbol, 0)
            realized_pnl_units = (close_price - entry_p) * qty_to_sell
            
            # Notify risk BEFORE liquidation
            quote_asset = "USDC" if "USDC" in symbol else "USDT"
            bal_info = await binance_client.get_asset_balance(quote_asset)
            current_bal = float(bal_info.get("free", 0.0))
            await notification_service.notify_risk(risk_signal, symbol, close_price, pnl, balance=current_bal, quote_asset=quote_asset)
            
            # 1.2 Format for Binance LOT_SIZE before selling
            lot_info = await binance_client.get_exchange_info(symbol)
            step_size = float(lot_info.get("stepSize", 0.000001))
            quantity = binance_client.round_step(qty_to_sell, step_size)
            
            # Record Realized PnL summary
            await risk_manager.update_daily_pnl(realized_pnl_units)
            
            # Place the SELL order
            order = await trading_engine.place_market_order(symbol, "SELL", quantity=quantity, rsi=None)
            
            if risk_signal == "PARTIAL_TP":
                # Update partial state, move SL if needed
                await risk_manager.update_partial_execution(symbol, qty_to_sell)
                logger.info(f"RISK | Partial TP Order Successful: {order.get('orderId')}")
            else:
                # Final exit (SL or Final TP)
                await rsi_strategy.update_position(symbol, False)
                await risk_manager.clear_entry_price(symbol)
                logger.info(f"RISK | Exit Order Successful: {order.get('orderId')}")
            
            # Record Realized PnL summary
            await risk_manager.update_daily_pnl(realized_pnl_units)
                
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
                    if settings.ENABLE_DYNAMIC_SIZING:
                        # Calculate SL price to determine risk distance
                        sl_price = close_price * (1 - settings.STOP_LOSS_PCT / 100.0)
                        raw_qty = risk_manager.calculate_position_size(symbol, close_price, sl_price)
                        
                        # Format for Binance LOT_SIZE
                        lot_info = await binance_client.get_exchange_info(symbol)
                        step_size = float(lot_info.get("stepSize", 0.000001))
                        quantity = binance_client.round_step(raw_qty, step_size)
                        
                        logger.info(f"SIZING | Calculated Dynamic Qty for {symbol}: {quantity} (Risk: {settings.RISK_PER_TRADE_PCT}%)")
                    else:
                        # Fixed order value approach (e.g. $10 USD)
                        raw_qty = settings.FIXED_ORDER_VALUE_USDT / close_price
                        
                        # Format for Binance LOT_SIZE
                        lot_info = await binance_client.get_exchange_info(symbol)
                        step_size = float(lot_info.get("stepSize", 0.000001))
                        quantity = binance_client.round_step(raw_qty, step_size)
                        
                        logger.info(f"SIZING | Fixed Order Value for {symbol} at {close_price}: {quantity} (Target: ${settings.FIXED_ORDER_VALUE_USDT}, Step: {step_size})")
                else:
                    # For SELL, we must only sell what we actually have left in risk_manager
                    pos_meta = risk_manager.position_data.get(symbol)
                    if pos_meta:
                        raw_qty = pos_meta["current_qty"]
                        lot_info = await binance_client.get_exchange_info(symbol)
                        step_size = float(lot_info.get("stepSize", 0.000001))
                        quantity = binance_client.round_step(raw_qty, step_size)
                    else:
                        logger.warning(f"EXECUTION | SELL Signal but NO position tracked in RiskManager for {symbol}. Resetting state.")
                        # Auto-sync strategy state to avoid ghost signals
                        await rsi_strategy.update_position(symbol, False)
                        return

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

async def background_report_task():
    """Periodic status report every 5 minutes."""
    while True:
        try:
            await asyncio.sleep(300) # 5 minutes
            pnl = risk_manager.daily_pnl
            quote = "USDC" if any("USDC" in s for s in settings.TRADING_SYMBOLS.split(",")) else "USDT"
            benchmark = f"BTC{quote}"
            btc_rsi = get_symbol_data(benchmark).get_rsi()
            status = "UP" if trading_engine.is_running else "IDLE"
            
            msg = f"📊 *VinBot Status Report*\n"
            msg += f"PnL Daily: `{pnl:.2f} {quote}`\n"
            if btc_rsi is not None:
                msg += f"{benchmark} RSI: `{btc_rsi:.2f}`\n"
            else:
                msg += f"{benchmark} RSI: `N/A`\n"
            msg += f"Status: `{status}`"
            
            if settings.ENABLE_PERIODIC_REPORTS:
                await notification_service.send_message(msg)
                logger.info("Periodic report sent to Telegram.")
        except Exception as e:
            logger.error(f"Error in background_report_task: {e}")

async def background_metrics_task():
    """Periodic task to update live balance metrics for Grafana."""
    from app.core.metrics import binance_wallet_balance
    while True:
        try:
            await asyncio.sleep(60) # 60 seconds
            quote_asset = "USDC" if any("USDC" in s for s in settings.TRADING_SYMBOLS.split(",")) else "USDT"
            bal_info = await binance_client.get_asset_balance(quote_asset)
            current_bal = float(bal_info.get("free", 0.0))
            binance_wallet_balance.labels(asset=quote_asset).set(current_bal)
        except Exception as e:
            logger.error(f"Error updating wallet balance metric: {e}")

async def run_trading_bot():
    """Background task for the trading engine initialization and symbol loop."""
    logger.info("Starting Trading Bot background loop...")
    await binance_client.sync_time()
    
    symbols = settings.TRADING_SYMBOLS.split(",")
    # Initialize Benchmark Symbol (usually BTC pair) for filters
    benchmark_symbol = "BTCUSDT" # Default
    if any("USDC" in s for s in symbols):
        benchmark_symbol = "BTCUSDC"
        
    if settings.ENABLE_BTC_DIRECTIONAL_FILTER or settings.ENABLE_RELATIVE_STRENGTH_FILTER:
        if benchmark_symbol not in symbols:
            logger.info(f"Initializing {benchmark_symbol} for directional/relative strength filters...")
            symbols.append(benchmark_symbol)
    
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
    # await notification_service.notify_status("ONLINE and monitoring markets")
    
    bot_task = asyncio.create_task(run_trading_bot())
    report_task = asyncio.create_task(background_report_task())
    metrics_task = asyncio.create_task(background_metrics_task())
    yield
    # Shutdown
    logger.info("Application shutting down...")
    # await notification_service.notify_status("OFFLINE / shutting down")
    bot_task.cancel()
    report_task.cancel()
    metrics_task.cancel()
    await binance_client.close()
    await db.disconnect()

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# Setup Observability (Prometheus + OTLP)
setup_observability(app)

app.include_router(api_router, prefix=settings.API_V1_STR)
