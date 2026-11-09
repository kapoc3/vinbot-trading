import time
import logging
import hashlib
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Request, Response, HTTPException, status
from pydantic import BaseModel

from app.services.trading_engine import trading_engine
from app.services.risk_manager import risk_manager
from app.services.statistics import statistics_service
from app.services.regime_service import regime_service, MarketRegime
from app.services.strategy_factory import strategy_manager, current_strategy
from app.services.notifications import notification_service
from app.core.database import db
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()

# Input Validation Model
class LoginRequest(BaseModel):
    username: str
    password: str

# Simple in-memory cache
_cache = {
    "data": None,
    "timestamp": 0.0
}
CACHE_DURATION_SECS = 5.0

# Helpers for Session Authentication
def get_expected_signature(username: str) -> str:
    return hashlib.sha256(f"{username}:{settings.SECRET_KEY}".encode()).hexdigest()

def verify_session(request: Request) -> str:
    token = request.cookies.get("session_token")
    if not token or ":" not in token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    try:
        username, sig = token.split(":", 1)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session format"
        )
    if username != settings.DASHBOARD_USERNAME or sig != get_expected_signature(username):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token"
        )
    return username

# --- Authentication Endpoints ---

@router.post("/login")
async def login(login_data: LoginRequest, response: Response):
    """Log in and set a signed session cookie."""
    if login_data.username != settings.DASHBOARD_USERNAME or login_data.password != settings.DASHBOARD_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos"
        )
    
    sig = get_expected_signature(login_data.username)
    token = f"{login_data.username}:{sig}"
    
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400, # 1 day
        path="/"
    )
    logger.info(f"DASHBOARD | User '{login_data.username}' logged in successfully.")
    return {"status": "success", "message": "Autenticado con éxito"}

@router.post("/logout")
async def logout(response: Response, username: str = Depends(verify_session)):
    """Log out and delete the session cookie."""
    response.delete_cookie(key="session_token", path="/")
    logger.info(f"DASHBOARD | User '{username}' logged out.")
    return {"status": "success", "message": "Sesión cerrada"}

# --- Data & Control Endpoints ---

@router.get("")
async def get_dashboard_data(username: str = Depends(verify_session)) -> Dict[str, Any]:
    """Get consolidated dashboard data including performance, regime, and recent trades."""
    current_time = time.time()
    if _cache["data"] is not None and (current_time - _cache["timestamp"]) < CACHE_DURATION_SECS:
        logger.debug("DASHBOARD | Returning cached dashboard data.")
        return _cache["data"]

    # 1. Bot status and quick risk manager metrics
    bot_running = trading_engine.is_running
    daily_pnl = risk_manager.daily_pnl
    allowed_to_trade = risk_manager.is_trading_allowed()

    # 2. Accumulated performance stats from statistics service
    accumulated_pnl = 0.0
    performance_stats = {
        "total_trades": 0,
        "winning_trades": 0,
        "losing_trades": 0,
        "win_rate": 0.0,
        "total_profit": 0.0,
        "avg_profit": 0.0,
        "max_drawdown": 0.0
    }
    try:
        stats = await statistics_service.get_all_symbols_stats()
        if "error" not in stats:
            performance_stats = {
                "total_trades": stats.get("total_trades", 0),
                "winning_trades": stats.get("winning_trades", 0),
                "losing_trades": stats.get("losing_trades", 0),
                "win_rate": round(stats.get("win_rate", 0.0) * 100, 2),
                "total_profit": round(stats.get("total_profit", 0.0), 4),
                "avg_profit": round(stats.get("avg_profit", 0.0), 4),
                "max_drawdown": round(stats.get("drawdown", {}).get("max_drawdown", 0.0), 4)
            }
            accumulated_pnl = stats.get("total_profit", 0.0)
    except Exception as e:
        logger.error(f"DASHBOARD | Error fetching accumulated PnL: {e}")

    # 3. Compile regimes and active strategies for all trading symbols
    symbols = [s.strip() for s in settings.TRADING_SYMBOLS.split(",") if s.strip()]
    
    symbol_regimes = {}
    symbol_strategies = {}
    
    for symbol in symbols:
        # Regime classification
        regime = regime_service.current_regimes.get(symbol, MarketRegime.UNKNOWN)
        symbol_regimes[symbol] = regime.value
        
        # Strategy name
        try:
            strategy = strategy_manager.get_strategy(symbol)
            symbol_strategies[symbol] = strategy.__class__.__name__
        except Exception as e:
            logger.debug(f"DASHBOARD | Could not get strategy for {symbol}: {e}")
            symbol_strategies[symbol] = settings.TRADING_STRATEGY

    # 4. SQLite query to get the last 10 orders
    recent_trades: List[Dict[str, Any]] = []
    try:
        cursor = await db.execute(
            "SELECT order_id, symbol, side, price, quantity, rsi, timestamp FROM orders ORDER BY timestamp DESC LIMIT 10"
        )
        rows = await cursor.fetchall()
        recent_trades = [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"DASHBOARD | Error fetching recent trades from database: {e}")

    # 5. Compile Local AI (Triple-Barrier Ensemble + OBI) telemetry across all active models
    ml_symbols_data: Dict[str, Any] = {}
    all_recent_decisions: List[Dict[str, Any]] = []
    try:
        import os
        import json
        import pickle

        model_dir = settings.ML_MODEL_PATH
        if os.path.isdir(model_dir):
            # Discover all symbols that have telemetry or trained models
            discovered_symbols = set(symbols)
            for fname in os.listdir(model_dir):
                if fname.endswith("_telemetry.json"):
                    discovered_symbols.add(fname.replace("_telemetry.json", ""))
                elif fname.endswith("_model.pkl"):
                    discovered_symbols.add(fname.replace("_model.pkl", ""))

            for sym in sorted(discovered_symbols):
                telemetry_path = os.path.join(model_dir, f"{sym}_telemetry.json")
                model_path = os.path.join(model_dir, f"{sym}_model.pkl")
                snap = None
                if os.path.exists(telemetry_path):
                    try:
                        with open(telemetry_path, "r", encoding="utf-8") as f:
                            snap = json.load(f)
                    except Exception:
                        snap = None
                if snap is None and os.path.exists(model_path):
                    try:
                        with open(model_path, "rb") as f:
                            mdata = pickle.load(f)
                        snap = {
                            "symbol": sym,
                            "model_type": mdata.get("model_type", "VotingEnsemble"),
                            "trained_at": mdata.get("trained_at", ""),
                            "n_samples": mdata.get("n_samples", 0),
                            "cv_accuracy": round(float(mdata.get("cv_mean", 0.0)) * 100.0, 1),
                            "cv_buy_winrate": round(float(mdata.get("cv_buy_precision", 0.0)) * 100.0, 1),
                            "live_evaluated": 0,
                            "live_correct": 0,
                            "live_accuracy": 0.0,
                            "vetoes_total": 0,
                            "vetoes_saved": 0,
                            "latest_signal": "HOLD",
                            "latest_confidence": 0.0,
                            "buy_prob": 0.0,
                            "hold_prob": 100.0,
                            "sell_prob": 0.0,
                            "obi": 0.0,
                            "recent_decisions": [],
                        }
                    except Exception:
                        pass
                if snap:
                    ml_symbols_data[sym] = snap
                    for dec in snap.get("recent_decisions", []):
                        all_recent_decisions.append(dec)
    except Exception as e:
        logger.error(f"DASHBOARD | Error compiling ML telemetry: {e}")

    all_recent_decisions.sort(key=lambda d: d.get("time", ""), reverse=True)
    cv_vals = [v.get("cv_accuracy", 0.0) for v in ml_symbols_data.values() if v.get("cv_accuracy", 0.0) > 0]
    live_eval_total = sum(v.get("live_evaluated", 0) for v in ml_symbols_data.values())
    live_corr_total = sum(v.get("live_correct", 0) for v in ml_symbols_data.values())
    vetoes_total = sum(v.get("vetoes_total", 0) for v in ml_symbols_data.values())
    vetoes_saved = sum(v.get("vetoes_saved", 0) for v in ml_symbols_data.values())

    ml_insights = {
        "enabled": settings.ML_ENABLED,
        "models_active": len(ml_symbols_data),
        "avg_cv_accuracy": round(sum(cv_vals) / len(cv_vals), 1) if cv_vals else 0.0,
        "live_evaluated_total": live_eval_total,
        "live_correct_total": live_corr_total,
        "live_accuracy_pct": round((live_corr_total / live_eval_total) * 100.0, 1) if live_eval_total > 0 else None,
        "vetoes_total": vetoes_total,
        "vetoes_saved": vetoes_saved,
        "symbols": ml_symbols_data,
        "recent_decisions": all_recent_decisions[:12],
    }

    data = {
        "bot_running": bot_running,
        "daily_pnl": round(daily_pnl, 4),
        "accumulated_pnl": round(accumulated_pnl, 4),
        "performance_stats": performance_stats,
        "allowed_to_trade": allowed_to_trade,
        "strategy_mode": settings.TRADING_STRATEGY,
        "symbol_regimes": symbol_regimes,
        "symbol_strategies": symbol_strategies,
        "recent_trades": recent_trades,
        "ml_insights": ml_insights,
        "timestamp": current_time
    }

    _cache["data"] = data
    _cache["timestamp"] = current_time
    logger.debug("DASHBOARD | Cache updated with fresh dashboard data.")
    
    return data

@router.get("/trades")
async def get_trades(date: Optional[str] = None, username: str = Depends(verify_session)) -> List[Dict[str, Any]]:
    """Get executed trades, optionally filtered by date (format: YYYY-MM-DD)."""
    query = "SELECT order_id, symbol, side, price, quantity, rsi, timestamp FROM orders"
    params = {}
    
    if date:
        # Validate date format
        try:
            time.strptime(date, "%Y-%m-%d")
            query += " WHERE DATE(timestamp) = :date"
            params["date"] = date
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de fecha inválido. Usar YYYY-MM-DD"
            )
            
    query += " ORDER BY timestamp DESC"
    
    try:
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"DASHBOARD | Error retrieving trades by date ({date}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al recuperar transacciones de la base de datos"
        )

@router.get("/historical")
async def get_historical_data(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    limit: int = 100,
    username: str = Depends(verify_session)
) -> List[Dict[str, Any]]:
    """Get historical klines for a symbol and interval, formatted for charts."""
    symbol_upper = symbol.upper()
    
    valid_intervals = {"1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"}
    if interval not in valid_intervals:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Intervalo inválido. Intervalos válidos: {sorted(list(valid_intervals))}"
        )
    
    if limit < 1 or limit > 500:
        limit = 100

    try:
        from app.services.market_data import market_service
        klines = await market_service.get_historical_klines(symbol_upper, interval, limit)
        if not klines:
            raise ValueError("No data returned from Binance")
            
        formatted_data = []
        for k in klines:
            formatted_data.append({
                "time": k[0],
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5])
            })
        return formatted_data
    except Exception as e:
        logger.error(f"DASHBOARD | Error fetching historical data for {symbol_upper} ({interval}): {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al obtener datos históricos para {symbol_upper} desde Binance. Verifique el símbolo."
        )

@router.post("/bot/start")
async def start_bot(username: str = Depends(verify_session)):
    """Start the trading bot execution loop."""
    trading_engine.is_running = True
    await notification_service.send_message("🤖 *VinBot Status Update*\nEl bot ha sido *INICIADO* manualmente desde el Dashboard\\.")
    logger.info(f"DASHBOARD | Bot started by user '{username}'.")
    return {"status": "success", "message": "Bot iniciado correctamente."}

@router.post("/bot/stop")
async def stop_bot(username: str = Depends(verify_session)):
    """Stop the trading bot execution loop."""
    trading_engine.is_running = False
    await notification_service.send_message("🤖 *VinBot Status Update*\nEl bot ha sido *DETENIDO* manualmente desde el Dashboard\\.")
    logger.info(f"DASHBOARD | Bot stopped by user '{username}'.")
    return {"status": "success", "message": "Bot detenido correctamente."}

@router.post("/reset-operations")
async def reset_operations(username: str = Depends(verify_session)):
    """Reset daily statistics, clear tracked entry prices, and open positions."""
    # 1. Reset daily stats & circuit breaker in risk manager
    await risk_manager.reset_daily_stats()
    
    # 2. Reset database & active status tracker per configured symbol
    symbols = [s.strip() for s in settings.TRADING_SYMBOLS.split(",") if s.strip()]
    for symbol in symbols:
        await risk_manager.clear_entry_price(symbol)
        await current_strategy.update_position(symbol, False)
        
    await notification_service.send_message("📊 *VinBot Operations Reset*\nLas operaciones, posiciones activas y PnL han sido *REINICIADOS* manualmente desde el Dashboard\\.")
    logger.info(f"DASHBOARD | Operations reset by user '{username}'.")
    return {"status": "success", "message": "Operaciones y PnL reiniciados con éxito."}
