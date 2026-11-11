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
from app.services.binance_client import binance_client
from app.services.persistence import persistence
from app.core.database import db
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()

# Input Validation Model
class LoginRequest(BaseModel):
    username: str
    password: str

class SellPositionRequest(BaseModel):
    symbol: str

class AIChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = None

# Simple in-memory cache
_cache = {
    "data": None,
    "timestamp": 0.0
}
CACHE_DURATION_SECS = 5.0

_wallet_cache = {
    "data": None,
    "timestamp": 0.0
}
WALLET_CACHE_DURATION_SECS = 15.0

STABLECOINS = {"USDC", "USDT", "FDUSD", "BUSD", "DAI", "TUSD"}


async def _fetch_wallet_portfolio() -> Dict[str, Any]:
    """Fetch real-time Spot wallet balances from Binance and compute USD valuations."""
    now = time.time()
    if _wallet_cache["data"] is not None and (now - _wallet_cache["timestamp"]) < WALLET_CACHE_DURATION_SECS:
        return _wallet_cache["data"]

    default_wallet = {
        "total_usd": 0.0,
        "free_stable_usd": 0.0,
        "locked_usd": 0.0,
        "invested_crypto_usd": 0.0,
        "goal_usd": 100.0,
        "goal_progress_pct": 0.0,
        "assets": [],
        "updated_at": now,
    }

    # If Alpaca broker is selected, fetch from Alpaca adapter
    if getattr(settings, "BROKER_BACKEND", "binance").lower() == "alpaca":
        try:
            from app.services.brokers import get_broker_adapter
            adapter = get_broker_adapter("alpaca")
            acc = await adapter.get_account()
            assets = await adapter.get_wallet_balances()
            tot_usd = acc.get("equity_usd", 0.0)
            cash_usd = acc.get("cash_usd", 0.0)
            invested = max(0.0, tot_usd - cash_usd)
            wallet_data = {
                "total_usd": tot_usd,
                "free_stable_usd": cash_usd,
                "locked_usd": 0.0,
                "invested_crypto_usd": round(invested, 2),
                "goal_usd": 100.0,
                "goal_progress_pct": round(min(100.0, (tot_usd / 100.0) * 100.0), 1) if tot_usd > 0 else 0.0,
                "assets": assets,
                "updated_at": now,
            }
            _wallet_cache["data"] = wallet_data
            _wallet_cache["timestamp"] = now
            return wallet_data
        except Exception as e:
            logger.error(f"DASHBOARD | Error fetching Alpaca wallet portfolio: {e}")
            return default_wallet

    # Skip network calls in mock mode or unit test mocks
    api_key = getattr(settings, "BINANCE_API_KEY", None)
    env_mode = getattr(settings, "BINANCE_ENV", "mock")
    if env_mode == "mock" or not isinstance(api_key, str) or not api_key or "mock" in api_key.lower():
        return default_wallet

    try:
        account = await binance_client.request("GET", "/api/v3/account", signed=True)
        tickers = await binance_client.request("GET", "/api/v3/ticker/price", signed=False)

        price_map: Dict[str, float] = {}
        if isinstance(tickers, list):
            for t in tickers:
                if "symbol" in t and "price" in t:
                    try:
                        price_map[t["symbol"]] = float(t["price"])
                    except (ValueError, TypeError):
                        pass

        raw_balances = account.get("balances", []) if isinstance(account, dict) else []
        assets_list: List[Dict[str, Any]] = []

        for b in raw_balances:
            asset = str(b.get("asset", "")).upper()
            if not asset:
                continue
            free = float(b.get("free", 0.0) or 0.0)
            locked = float(b.get("locked", 0.0) or 0.0)
            total = free + locked
            if total <= 0:
                continue

            is_stable = asset in STABLECOINS
            if is_stable:
                price_usd = 1.0
            else:
                price_usd = (
                    price_map.get(f"{asset}USDC")
                    or price_map.get(f"{asset}USDT")
                    or price_map.get(f"{asset}FDUSD")
                    or price_map.get(f"{asset}BUSD")
                    or 0.0
                )
                if price_usd == 0.0 and f"USDC{asset}" in price_map and price_map[f"USDC{asset}"] > 0:
                    price_usd = 1.0 / price_map[f"USDC{asset}"]

            usd_value = total * price_usd
            # Filter out sub-cent dust unless it's >= $0.005
            if usd_value < 0.005:
                continue

            # Check if bot tracks an open entry price for this asset (across both classic and scalper DBs)
            entry_price = 0.0
            unrealized_pnl_pct = None
            if not is_stable:
                try:
                    ep_usdc = await persistence.get_state(f"{asset.lower()}usdc_entry_price", 0.0)
                    ep_usdt = await persistence.get_state(f"{asset.lower()}usdt_entry_price", 0.0)
                    entry_price = float(ep_usdc or ep_usdt or risk_manager.entry_prices.get(f"{asset}USDC", 0.0) or 0.0)
                    if entry_price == 0.0:
                        import sqlite3
                        import os
                        import json as _json
                        for db_file in ("data/vinbot_scalper.db", "data/vinbot_classic.db"):
                            if os.path.exists(db_file):
                                with sqlite3.connect(db_file) as sconn:
                                    r = sconn.execute(
                                        "SELECT value FROM bot_state WHERE key IN (?, ?)",
                                        (f"{asset.lower()}usdc_entry_price", f"{asset.lower()}usdt_entry_price"),
                                    ).fetchone()
                                    if r and r[0]:
                                        val = float(_json.loads(r[0]))
                                        if val > 0:
                                            entry_price = val
                                            break
                    if entry_price > 0 and price_usd > 0:
                        unrealized_pnl_pct = round(((price_usd - entry_price) / entry_price) * 100.0, 2)
                except Exception:
                    pass

            assets_list.append({
                "asset": asset,
                "free": round(free, 8),
                "locked": round(locked, 8),
                "total": round(total, 8),
                "price_usd": round(price_usd, 6 if price_usd < 1.0 else 4),
                "usd_value": round(usd_value, 2),
                "is_stable": is_stable,
                "in_bot_position": entry_price > 0 and usd_value >= 5.0,
                "entry_price": round(entry_price, 4) if entry_price > 0 else None,
                "unrealized_pnl_pct": unrealized_pnl_pct,
            })

        assets_list.sort(key=lambda x: x["usd_value"], reverse=True)
        total_usd = round(sum(a["usd_value"] for a in assets_list), 2)
        free_stable_usd = round(sum(a["free"] * a["price_usd"] for a in assets_list if a["is_stable"]), 2)
        locked_usd = round(sum(a["locked"] * a["price_usd"] for a in assets_list), 2)
        invested_crypto_usd = round(sum(a["usd_value"] for a in assets_list if not a["is_stable"]), 2)

        for a in assets_list:
            a["allocation_pct"] = round((a["usd_value"] / total_usd) * 100.0, 1) if total_usd > 0 else 0.0

        goal_usd = 100.0
        wallet_snapshot = {
            "total_usd": total_usd,
            "free_stable_usd": free_stable_usd,
            "locked_usd": locked_usd,
            "invested_crypto_usd": invested_crypto_usd,
            "goal_usd": goal_usd,
            "goal_progress_pct": round(min(100.0, (total_usd / goal_usd) * 100.0), 1) if goal_usd > 0 else 0.0,
            "assets": assets_list,
            "updated_at": now,
        }
        _wallet_cache["data"] = wallet_snapshot
        _wallet_cache["timestamp"] = now
        return wallet_snapshot
    except Exception as e:
        logger.error(f"DASHBOARD | Error fetching Binance wallet portfolio: {e}")
        return _wallet_cache["data"] or default_wallet

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

def _link_orders_buy_sell(all_orders: List[Dict[str, Any]], live_prices: Optional[Dict[str, float]] = None) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Match BUY and SELL orders chronologically (FIFO per symbol) so every SELL
    identifies which BUY order(s) it closed, the weighted-average buy price,
    and the exact realized profit/loss in USD and %, and every BUY shows which
    SELL order closed it (or if it remains open in the portfolio).
    """
    from collections import defaultdict

    chronological = [dict(o) for o in all_orders]
    chronological.sort(key=lambda x: str(x.get("timestamp", "")))

    buy_queues: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    closed_cycles: List[Dict[str, Any]] = []

    for order in chronological:
        sym = str(order.get("symbol", ""))
        side = str(order.get("side", "BUY")).upper()
        price = float(order.get("price") or 0.0)
        qty = float(order.get("quantity") or 0.0)
        order["order_value_usd"] = round(price * qty, 2)
        order["buy_price"] = round(price, 4) if side == "BUY" else None
        order["sell_price"] = round(price, 4) if side == "SELL" else None
        order["pnl_usd"] = None
        order["pnl_pct"] = None
        order["linked_order_ids"] = []
        order["linked_text"] = ""
        order["trade_status"] = "OPEN" if side == "BUY" else "UNLINKED_SELL"

        if side == "BUY" and price > 0 and qty > 0:
            order["_rem_qty"] = qty
            order["_matched_sells"] = []
            buy_queues[sym].append(order)
        elif side == "SELL" and price > 0 and qty > 0:
            rem_to_match = qty
            matched_cost_usd = 0.0
            matched_qty = 0.0
            matched_buy_ids: List[Any] = []
            matched_details: List[Dict[str, Any]] = []

            queue = buy_queues[sym]
            while rem_to_match > 1e-8 and queue:
                buy_lot = queue[0]
                take_qty = min(rem_to_match, buy_lot["_rem_qty"])
                b_price = float(buy_lot.get("price") or 0.0)
                lot_cost = take_qty * b_price
                lot_proceeds = take_qty * price
                lot_pnl = lot_proceeds - lot_cost

                matched_cost_usd += lot_cost
                matched_qty += take_qty
                rem_to_match -= take_qty
                buy_lot["_rem_qty"] -= take_qty

                b_id = buy_lot.get("order_id")
                matched_buy_ids.append(b_id)
                matched_details.append({
                    "buy_order_id": b_id,
                    "buy_price": round(b_price, 4),
                    "qty": round(take_qty, 6),
                    "cost_usd": round(lot_cost, 2),
                    "pnl_usd": round(lot_pnl, 4),
                    "buy_timestamp": buy_lot.get("timestamp"),
                })
                buy_lot["_matched_sells"].append({
                    "sell_order_id": order.get("order_id"),
                    "sell_price": price,
                    "qty": take_qty,
                    "pnl_usd": lot_pnl,
                    "sell_timestamp": order.get("timestamp"),
                })

                # Pop lot if >=97% consumed (accounts for Binance stepSize rounding dust)
                if buy_lot["_rem_qty"] <= float(buy_lot.get("quantity") or 0.0) * 0.03:
                    queue.pop(0)

            if matched_qty > 0:
                avg_buy_price = matched_cost_usd / matched_qty
                sell_proceeds_usd = price * matched_qty
                realized_pnl_usd = sell_proceeds_usd - matched_cost_usd
                realized_pnl_pct = ((price - avg_buy_price) / avg_buy_price) * 100.0 if avg_buy_price > 0 else 0.0

                order["trade_status"] = "CLOSED_SELL"
                order["buy_price"] = round(avg_buy_price, 4)
                order["sell_price"] = round(price, 4)
                order["buy_cost_usd"] = round(matched_cost_usd, 2)
                order["sell_value_usd"] = round(sell_proceeds_usd, 2)
                order["pnl_usd"] = round(realized_pnl_usd, 4)
                order["pnl_pct"] = round(realized_pnl_pct, 2)
                order["linked_order_ids"] = matched_buy_ids
                order["matched_details"] = matched_details

                if len(matched_buy_ids) == 1:
                    order["linked_text"] = f"🔗 Cierra Compra #{matched_buy_ids[0]} (a ${avg_buy_price:.2f})"
                else:
                    ids_str = ", ".join(f"#{bid}" for bid in matched_buy_ids)
                    order["linked_text"] = f"🔗 Cierra {len(matched_buy_ids)} Compras ({ids_str})"

                closed_cycles.append({
                    "sell_order_id": order.get("order_id"),
                    "symbol": sym,
                    "timestamp": order.get("timestamp"),
                    "quantity": round(matched_qty, 6),
                    "avg_buy_price": round(avg_buy_price, 4),
                    "sell_price": round(price, 4),
                    "buy_cost_usd": round(matched_cost_usd, 2),
                    "sell_value_usd": round(sell_proceeds_usd, 2),
                    "pnl_usd": round(realized_pnl_usd, 4),
                    "pnl_pct": round(realized_pnl_pct, 2),
                    "linked_buy_ids": matched_buy_ids,
                    "matched_details": matched_details,
                })

    # Finalize BUY rows with their realized or unrealized status
    for order in chronological:
        if str(order.get("side", "")).upper() == "BUY":
            matched_sells = order.pop("_matched_sells", [])
            order.pop("_rem_qty", None)
            b_price = float(order.get("price") or 0.0)
            qty = float(order.get("quantity") or 0.0)
            sym = str(order.get("symbol", ""))

            if matched_sells:
                tot_q = sum(ms["qty"] for ms in matched_sells)
                tot_pnl = sum(ms["pnl_usd"] for ms in matched_sells)
                avg_s_price = sum(ms["sell_price"] * ms["qty"] for ms in matched_sells) / tot_q if tot_q > 0 else 0.0
                s_ids = [ms["sell_order_id"] for ms in matched_sells]
                order["trade_status"] = "SOLD"
                order["sell_price"] = round(avg_s_price, 4)
                order["pnl_usd"] = round(tot_pnl, 4)
                order["pnl_pct"] = round(((avg_s_price - b_price) / b_price) * 100.0, 2) if b_price > 0 else 0.0
                order["linked_order_ids"] = s_ids
                order["linked_text"] = f"🔗 Vendida en Venta #{s_ids[0]} (a ${avg_s_price:.2f})"
            else:
                cur_p = float((live_prices or {}).get(sym, 0.0) or 0.0)
                if cur_p > 0 and b_price > 0:
                    u_pnl = (cur_p - b_price) * qty
                    u_pct = ((cur_p - b_price) / b_price) * 100.0
                    order["sell_price"] = round(cur_p, 4)
                    order["pnl_usd"] = round(u_pnl, 4)
                    order["pnl_pct"] = round(u_pct, 2)
                    order["linked_text"] = f"🟢 En cartera (Actual: ${cur_p:.2f})"
                else:
                    order["linked_text"] = "🟢 En cartera activa"

    chronological.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
    closed_cycles.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
    return chronological, closed_cycles


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

    # 4. SQLite query to get the last orders (merging scalper DB in production)
    recent_trades: List[Dict[str, Any]] = []
    closed_cycles: List[Dict[str, Any]] = []
    try:
        cursor = await db.execute(
            "SELECT order_id, symbol, side, price, quantity, rsi, timestamp FROM orders ORDER BY timestamp DESC LIMIT 10"
        )
        rows = await cursor.fetchall()
        recent_trades = [dict(row) for row in rows]
        api_key = getattr(settings, "BINANCE_API_KEY", None)
        if isinstance(api_key, str) and api_key and "mock" not in api_key.lower():
            import os
            import sqlite3
            seen_ids = {t.get("order_id") for t in recent_trades}
            for extra_db in ("data/vinbot_scalper.db", "data/vinbot_classic.db"):
                if os.path.exists(extra_db):
                    try:
                        with sqlite3.connect(extra_db) as sconn:
                            sconn.row_factory = sqlite3.Row
                            erows = sconn.execute(
                                "SELECT order_id, symbol, side, price, quantity, rsi, timestamp FROM orders ORDER BY timestamp DESC LIMIT 100"
                            ).fetchall()
                            for er in erows:
                                d_er = dict(er)
                                if d_er.get("order_id") not in seen_ids:
                                    recent_trades.append(d_er)
                                    seen_ids.add(d_er.get("order_id"))
                    except Exception:
                        pass
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

    verified_decs = [d for d in all_recent_decisions if d.get("verified")]
    pending_decs = [d for d in all_recent_decisions if not d.get("verified")]
    verified_decs.sort(key=lambda d: d.get("time", ""), reverse=True)
    pending_decs.sort(key=lambda d: (d.get("bars_elapsed", 0), d.get("time", "")), reverse=True)
    # Keep at most 1 pending decision per symbol (closest to completion) + up to 10 verified decisions
    seen_pending_syms = set()
    top_pending = []
    for d in pending_decs:
        s_name = d.get("symbol", "")
        if s_name not in seen_pending_syms:
            top_pending.append(d)
            seen_pending_syms.add(s_name)
    combined_decisions = verified_decs[:10] + top_pending[:4]
    cv_vals = [v.get("cv_accuracy", 0.0) for v in ml_symbols_data.values() if v.get("cv_accuracy", 0.0) > 0]
    live_eval_total = sum(v.get("live_evaluated", 0) for v in ml_symbols_data.values())
    live_corr_total = sum(v.get("live_correct", 0) for v in ml_symbols_data.values())
    vetoes_total = sum(v.get("vetoes_total", 0) for v in ml_symbols_data.values())
    vetoes_saved = sum(v.get("vetoes_saved", 0) for v in ml_symbols_data.values())

    # 5.5 Incorporate 4th Brain (Kronos Foundation Model) telemetry if available
    try:
        from app.services.ml.kronos_client import kronos_client
        for sym in ml_symbols_data.keys():
            k_data = kronos_client.cached_predictions.get(sym)
            if not k_data:
                k_path = os.path.join(model_dir, f"{sym}_kronos.json")
                if os.path.exists(k_path):
                    try:
                        with open(k_path, "r", encoding="utf-8") as f:
                            k_data = json.load(f)
                    except Exception:
                        k_data = None
            if k_data:
                ml_symbols_data[sym]["kronos"] = {
                    "direction": k_data.get("direction", "NEUTRAL"),
                    "confidence": k_data.get("confidence", 0.5),
                    "expected_pct": k_data.get("expected_pct", 0.0),
                    "inference_time_ms": k_data.get("inference_time_ms", 0.0),
                }
    except Exception as e:
        logger.debug(f"DASHBOARD | Error attaching Kronos telemetry: {e}")

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
        "recent_decisions": combined_decisions,
    }

    # 6. Fetch real-time Binance Spot Wallet & Asset Holdings
    wallet = await _fetch_wallet_portfolio()

    # 7. Link BUY and SELL orders (FIFO per symbol) to compute real PnL per trade
    live_prices: Dict[str, float] = {}
    for asset_info in wallet.get("assets", []):
        a_sym = asset_info.get("asset", "")
        if a_sym and a_sym not in ("USDC", "USDT"):
            live_prices[f"{a_sym}USDC"] = float(asset_info.get("price_usd", 0.0) or 0.0)
            live_prices[f"{a_sym}USDT"] = float(asset_info.get("price_usd", 0.0) or 0.0)

    if recent_trades:
        recent_trades, closed_cycles = _link_orders_buy_sell(recent_trades, live_prices)
        recent_trades = recent_trades[:20]

    # Active open positions tracked in RiskManager
    active_positions: Dict[str, Any] = {}
    for sym, pos_data in risk_manager.position_data.items():
        entry_p = risk_manager.entry_prices.get(sym, 0.0)
        curr_q = float(pos_data.get("current_qty", 0.0))
        if entry_p > 0 and curr_q > 0:
            cur_p = float(pos_data.get("current_price", entry_p) or entry_p)
            unrealized_usd = (cur_p - entry_p) * curr_q
            unrealized_pct = ((cur_p - entry_p) / entry_p) * 100.0 if entry_p > 0 else 0.0
            active_positions[sym] = {
                "symbol": sym,
                "entry_price": entry_p,
                "current_price": cur_p,
                "quantity": curr_q,
                "value_usd": round(cur_p * curr_q, 2),
                "unrealized_pnl_usd": round(unrealized_usd, 4),
                "unrealized_pnl_pct": round(unrealized_pct, 2),
                "sl_price": round(float(pos_data.get("sl_price", 0.0)), 4),
                "tp_hits": int(pos_data.get("tp_hits", 0)),
                "entry_time": str(pos_data.get("entry_time", "")),
            }

    scanner_info = {
        "enabled": getattr(settings, "ENABLE_MARKET_SCANNER", False),
        "interval_hours": getattr(settings, "SCANNER_INTERVAL_HOURS", 2),
        "min_volume_usd": getattr(settings, "SCANNER_MIN_VOLUME_USD", 10_000_000.0),
        "top_n": getattr(settings, "SCANNER_TOP_N", 3),
        "window_size": getattr(settings, "SCANNER_WINDOW_SIZE", "1h"),
        "fee_pct": getattr(settings, "EFFECTIVE_FEE_PCT", 0.075),
        "use_bnb": getattr(settings, "USE_BNB_FEE_DISCOUNT", True),
        "round_trip_factor": round(getattr(settings, "ROUND_TRIP_FEE_FACTOR", 1.001501), 6),
    }

    data = {
        "bot_running": bot_running,
        "daily_pnl": round(daily_pnl, 4),
        "accumulated_pnl": round(accumulated_pnl, 4),
        "performance_stats": performance_stats,
        "allowed_to_trade": allowed_to_trade,
        "strategy_mode": settings.TRADING_STRATEGY,
        "project_name": settings.PROJECT_NAME,
        "bot_profile": "SATELLITE (Hot 30%)" if settings.ENABLE_MARKET_SCANNER else "CORE (Majors 70%)",
        "scanner_enabled": settings.ENABLE_MARKET_SCANNER,
        "symbol_regimes": symbol_regimes,
        "symbol_strategies": symbol_strategies,
        "active_positions": active_positions,
        "scanner_info": scanner_info,
        "recent_trades": recent_trades,
        "closed_cycles": closed_cycles,
        "ml_insights": ml_insights,
        "wallet": wallet,
        "broker": getattr(settings, "BROKER_BACKEND", "binance").lower(),
        "broker_env": getattr(settings, "ALPACA_ENV", "paper") if getattr(settings, "BROKER_BACKEND", "binance").lower() == "alpaca" else getattr(settings, "BINANCE_ENV", "testnet"),
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
        trades_list = [dict(row) for row in rows]
        api_key = getattr(settings, "BINANCE_API_KEY", None)
        if isinstance(api_key, str) and api_key and "mock" not in api_key.lower():
            import os
            import sqlite3
            all_orders_for_linking: List[Dict[str, Any]] = []
            seen_ids = set()
            for extra_db in ("data/vinbot_scalper.db", "data/vinbot_classic.db"):
                if os.path.exists(extra_db):
                    try:
                        with sqlite3.connect(extra_db) as sconn:
                            sconn.row_factory = sqlite3.Row
                            erows = sconn.execute(
                                "SELECT order_id, symbol, side, price, quantity, rsi, timestamp FROM orders ORDER BY timestamp ASC"
                            ).fetchall()
                            for er in erows:
                                d_er = dict(er)
                                if d_er.get("order_id") not in seen_ids:
                                    all_orders_for_linking.append(d_er)
                                    seen_ids.add(d_er.get("order_id"))
                    except Exception:
                        pass
            if all_orders_for_linking:
                linked, _ = _link_orders_buy_sell(all_orders_for_linking)
                if date:
                    linked = [t for t in linked if str(t.get("timestamp", "")).startswith(date)]
                return linked
        return trades_list
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


def _extract_fill_price(order: Dict[str, Any], fallback: float) -> float:
    """Extract weighted-average executed fill price from order response."""
    raw_p = order.get("price")
    if raw_p is not None:
        try:
            p_val = float(raw_p)
            if p_val > 0:
                return p_val
        except (ValueError, TypeError):
            pass
    fills = order.get("fills") or []
    if fills:
        try:
            tot_cost = sum(float(f.get("price", 0)) * float(f.get("qty", 0)) for f in fills)
            tot_qty = sum(float(f.get("qty", 0)) for f in fills)
            if tot_qty > 0:
                return tot_cost / tot_qty
        except (ValueError, TypeError):
            pass
    return float(fallback)


@router.post("/position/sell")
async def sell_position(payload: SellPositionRequest, username: str = Depends(verify_session)):
    """Manually execute a market sell order for an active open position on demand."""
    symbol = payload.symbol.strip().upper()
    pos_data = risk_manager.position_data.get(symbol, {})
    qty_to_sell = float(pos_data.get("current_qty", 0.0))
    entry_p = float(risk_manager.entry_prices.get(symbol, 0.0))

    # Fallback to wallet balance if pos_data quantity is zero or missing
    if qty_to_sell <= 0:
        base_asset = symbol.replace("USDC", "").replace("USDT", "").replace("FDUSD", "")
        try:
            bal = await binance_client.get_asset_balance(base_asset)
            qty_to_sell = float(bal.get("free", 0.0))
        except Exception as e:
            logger.warning(f"DASHBOARD | Could not fetch wallet balance for {base_asset}: {e}")

    if qty_to_sell <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No hay posición activa ni saldo disponible para vender en {symbol}."
        )

    try:
        lot_info = await binance_client.get_exchange_info(symbol)
        step_size = float(lot_info.get("stepSize", 0.000001))
        min_qty = float(lot_info.get("minQty", 0.0))
        rounded_qty_str = binance_client.round_step(qty_to_sell, step_size)
        quantity = float(rounded_qty_str)

        if quantity <= 0 or (min_qty > 0 and quantity < min_qty):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La cantidad calculada ({quantity}) no cumple con el tamaño mínimo de Binance ({min_qty})."
            )

        fallback_price = float(pos_data.get("current_price", entry_p) or entry_p or 0.0)
        order = await trading_engine.place_market_order(
            symbol=symbol,
            side="SELL",
            quantity=quantity,
            rsi=None,
            current_price=fallback_price,
            notify=False
        )

        exec_price = _extract_fill_price(order, fallback_price)
        exec_qty = float(order.get("executedQty", quantity))

        if entry_p > 0:
            gross_pnl, total_fees, net_pnl = risk_manager.calculate_net_trade_pnl(entry_p, exec_price, exec_qty)
            net_pnl_pct = (net_pnl / (entry_p * exec_qty)) * 100.0 if (entry_p * exec_qty) > 0 else 0.0
        else:
            gross_pnl, total_fees, net_pnl = 0.0, 0.0, 0.0
            net_pnl_pct = 0.0

        await current_strategy.update_position(symbol, False)
        await risk_manager.clear_entry_price(symbol)
        if net_pnl != 0.0:
            await risk_manager.update_daily_pnl(net_pnl)

        quote_asset = "USDC" if "USDC" in symbol else "USDT"
        try:
            bal_info = await binance_client.get_asset_balance(quote_asset)
            current_bal = float(bal_info.get("free", 0.0))
        except Exception:
            current_bal = 0.0

        await notification_service.notify_trade_closed(
            signal="VENTA_MANUAL",
            symbol=symbol,
            entry_price=entry_p if entry_p > 0 else exec_price,
            exit_price=exec_price,
            qty=exec_qty,
            pnl_pct=round(net_pnl_pct, 2),
            pnl_usd=round(net_pnl, 4),
            daily_pnl=risk_manager.daily_pnl,
            balance=current_bal,
            quote_asset=quote_asset,
            fee_usd=round(total_fees, 4),
        )

        # Invalidate dashboard and wallet caches for immediate refresh
        _cache["timestamp"] = 0.0
        _wallet_cache["timestamp"] = 0.0

        logger.info(
            f"DASHBOARD | Position {symbol} manually sold by user '{username}'. "
            f"Qty: {exec_qty}, Exit Price: {exec_price}, Net PnL: ${net_pnl:.4f}"
        )

        return {
            "status": "success",
            "message": f"Posición de {symbol} vendida con éxito a mercado.",
            "data": {
                "symbol": symbol,
                "order_id": order.get("orderId"),
                "quantity": exec_qty,
                "executed_price": exec_price,
                "gross_pnl": round(gross_pnl, 4),
                "fees": round(total_fees, 4),
                "net_pnl": round(net_pnl, 4),
                "net_pnl_pct": round(net_pnl_pct, 2),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DASHBOARD | Error executing manual sell for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al ejecutar la venta en Binance: {str(e)}"
        )


@router.post("/ai-chat")
async def chat_with_analyst(payload: AIChatRequest, username: str = Depends(verify_session)):
    """Interact in natural language with the local AI Quant Analyst (Ollama / Qwen 2.5 / GTX 1060)."""
    msg = payload.message.strip()
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El mensaje no puede estar vacío."
        )
    from app.services.ai_chat_service import ai_chat_service
    result = await ai_chat_service.ask_analyst(msg, payload.history)
    return result


@router.get("/ai-chat/status")
async def get_ai_chat_status(username: str = Depends(verify_session)):
    """Check local Ollama engine status and GPU model readiness."""
    from app.services.ai_chat_service import ai_chat_service
    return await ai_chat_service.check_ollama_status()


@router.get("/broker/status")
async def get_broker_status(username: str = Depends(verify_session)):
    """Check active broker adapter backend, environment and account overview."""
    try:
        from app.services.brokers import get_broker_adapter
        adapter = get_broker_adapter()
        account = await adapter.get_account()
        backend = getattr(settings, "BROKER_BACKEND", "binance").lower()
        env_mode = getattr(settings, "ALPACA_ENV", "paper") if backend == "alpaca" else getattr(settings, "BINANCE_ENV", "testnet")
        return {
            "status": "success",
            "broker": adapter.broker_name,
            "backend": backend,
            "environment": env_mode,
            "account": account,
        }
    except Exception as e:
        logger.error(f"DASHBOARD | Error checking broker status: {e}")
        return {
            "status": "error",
            "broker": getattr(settings, "BROKER_BACKEND", "binance").lower(),
            "message": str(e),
        }

