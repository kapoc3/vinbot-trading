import logging
from typing import Dict, Any, List, Optional
from app.services.brokers.base import BaseBrokerAdapter
from app.services.binance_client import binance_client
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

STABLECOINS = {"USDC", "USDT", "FDUSD", "BUSD", "DAI", "TUSD"}


class BinanceAdapter(BaseBrokerAdapter):
    """Concrete broker adapter wrapping Binance Spot API."""

    @property
    def broker_name(self) -> str:
        return "binance"

    async def get_account(self) -> Dict[str, Any]:
        """Fetch Binance Spot account details normalized."""
        try:
            account = await binance_client.request("GET", "/api/v3/account", signed=True)
            balances = account.get("balances", []) if isinstance(account, dict) else []
            free_usd = 0.0
            for b in balances:
                asset = str(b.get("asset", "")).upper()
                if asset in STABLECOINS:
                    free_usd += float(b.get("free", 0.0) or 0.0)

            return {
                "equity_usd": free_usd,
                "cash_usd": free_usd,
                "buying_power_usd": free_usd,
                "currency": "USDC",
                "is_paper": settings.BINANCE_ENV == "mock",
                "status": "ACTIVE" if account.get("canTrade", True) else "RESTRICTED",
                "raw": account
            }
        except Exception as e:
            logger.error(f"BINANCE_ADAPTER | Error getting account: {e}")
            return {
                "equity_usd": 0.0,
                "cash_usd": 0.0,
                "buying_power_usd": 0.0,
                "currency": "USDC",
                "is_paper": settings.BINANCE_ENV == "mock",
                "status": "OFFLINE",
                "raw": {}
            }

    async def get_wallet_balances(self) -> List[Dict[str, Any]]:
        """Fetch spot balances from Binance and compute USD valuations."""
        from app.api.v1.endpoints.dashboard import _fetch_wallet_portfolio
        wallet = await _fetch_wallet_portfolio()
        return wallet.get("assets", [])

    async def get_positions(self) -> List[Dict[str, Any]]:
        """Fetch active positions tracked in RiskManager."""
        from app.services.risk_manager import risk_manager
        positions = []
        for sym, pos_data in risk_manager.position_data.items():
            entry_p = float(risk_manager.entry_prices.get(sym, 0.0))
            curr_q = float(pos_data.get("current_qty", 0.0))
            if entry_p > 0 and curr_q > 0:
                cur_p = float(pos_data.get("current_price", entry_p) or entry_p)
                unrealized_usd = (cur_p - entry_p) * curr_q
                unrealized_pct = ((cur_p - entry_p) / entry_p) * 100.0 if entry_p > 0 else 0.0
                positions.append({
                    "symbol": sym,
                    "qty": curr_q,
                    "entry_price": entry_p,
                    "current_price": cur_p,
                    "unrealized_pnl_usd": round(unrealized_usd, 4),
                    "unrealized_pnl_pct": round(unrealized_pct, 2),
                    "market_value_usd": round(cur_p * curr_q, 2),
                    "side": "long"
                })
        return positions

    async def get_historical_bars(self, symbol: str, interval: str = "1h", limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch historical klines from Binance and normalize to standard OHLCV dicts."""
        from app.services.market_data import market_service
        klines = await market_service.get_historical_klines(symbol.upper(), interval, limit)
        formatted = []
        for k in klines or []:
            formatted.append({
                "time": int(k[0]),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5])
            })
        return formatted

    async def get_latest_price(self, symbol: str) -> float:
        """Fetch current ticker price from Binance."""
        try:
            res = await binance_client.request("GET", "/api/v3/ticker/price", params={"symbol": symbol.upper()})
            return float(res.get("price", 0.0))
        except Exception as e:
            logger.error(f"BINANCE_ADAPTER | Failed to get latest price for {symbol}: {e}")
            return 0.0

    async def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "MARKET",
        time_in_force: str = "gtc",
        take_profit_price: Optional[float] = None,
        stop_loss_price: Optional[float] = None,
        limit_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Place standard market/limit order on Binance Spot."""
        from app.services.trading_engine import trading_engine
        return await trading_engine.place_market_order(
            symbol=symbol.upper(),
            side=side.upper(),
            quantity=quantity,
            notify=True
        )

    async def cancel_order(self, order_id: Any, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Cancel an order on Binance."""
        from app.services.trading_engine import trading_engine
        return await trading_engine.cancel_order(symbol=symbol.upper() if symbol else "BTCUSDC", order_id=int(order_id))

    async def close(self):
        await binance_client.close()

