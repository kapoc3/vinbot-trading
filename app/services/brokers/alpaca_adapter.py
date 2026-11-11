import logging
from typing import Dict, Any, List, Optional
from app.services.brokers.base import BaseBrokerAdapter
from app.services.alpaca_client import alpaca_client
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AlpacaAdapter(BaseBrokerAdapter):
    """
    Concrete broker adapter connecting VinBot to Alpaca Markets.
    Supports Equities (Stocks, ETFs) with zero commission and Crypto with native bracket orders.
    """

    @property
    def broker_name(self) -> str:
        return "alpaca"

    async def get_account(self) -> Dict[str, Any]:
        """Fetch and normalize Alpaca account details."""
        try:
            acc = await alpaca_client.get_account()
            equity = float(acc.get("equity", 0.0) or 0.0)
            cash = float(acc.get("cash", 0.0) or 0.0)
            bp = float(acc.get("buying_power", 0.0) or 0.0)
            is_paper = settings.ALPACA_ENV == "paper"

            return {
                "equity_usd": round(equity, 2),
                "cash_usd": round(cash, 2),
                "buying_power_usd": round(bp, 2),
                "currency": "USD",
                "is_paper": is_paper,
                "status": acc.get("status", "ACTIVE"),
                "raw": acc
            }
        except Exception as e:
            logger.error(f"ALPACA_ADAPTER | Failed to get account: {e}")
            return {
                "equity_usd": 0.0,
                "cash_usd": 0.0,
                "buying_power_usd": 0.0,
                "currency": "USD",
                "is_paper": settings.ALPACA_ENV == "paper",
                "status": "OFFLINE",
                "raw": {}
            }

    async def get_wallet_balances(self) -> List[Dict[str, Any]]:
        """Synthesize cash and held positions into a unified wallet breakdown."""
        assets = []
        try:
            acc = await self.get_account()
            cash_usd = acc.get("cash_usd", 0.0)

            # Cash balance
            if cash_usd > 0.01:
                assets.append({
                    "asset": "USD",
                    "free": cash_usd,
                    "locked": 0.0,
                    "total": cash_usd,
                    "price_usd": 1.0,
                    "usd_value": cash_usd,
                    "is_stable": True,
                    "in_bot_position": False,
                    "entry_price": None,
                    "unrealized_pnl_pct": None,
                })

            # Stock / Crypto positions
            positions = await alpaca_client.get_positions()
            for p in positions:
                sym = p.get("symbol", "")
                qty = float(p.get("qty", 0.0) or 0.0)
                cur_p = float(p.get("current_price", 0.0) or 0.0)
                entry_p = float(p.get("avg_entry_price", 0.0) or 0.0)
                mkt_val = float(p.get("market_value", 0.0) or 0.0)
                pnl_pct = float(p.get("unrealized_plpc", 0.0) or 0.0) * 100.0

                assets.append({
                    "asset": sym,
                    "free": qty,
                    "locked": 0.0,
                    "total": qty,
                    "price_usd": cur_p,
                    "usd_value": mkt_val,
                    "is_stable": False,
                    "in_bot_position": True,
                    "entry_price": entry_p,
                    "unrealized_pnl_pct": round(pnl_pct, 2),
                })
        except Exception as e:
            logger.error(f"ALPACA_ADAPTER | Failed to build wallet balances: {e}")

        return assets

    async def get_positions(self) -> List[Dict[str, Any]]:
        """Fetch open positions directly from Alpaca."""
        try:
            raw_pos = await alpaca_client.get_positions()
            normalized = []
            for p in raw_pos:
                qty = float(p.get("qty", 0.0) or 0.0)
                cur_p = float(p.get("current_price", 0.0) or 0.0)
                entry_p = float(p.get("avg_entry_price", 0.0) or 0.0)
                unrealized_pl = float(p.get("unrealized_pl", 0.0) or 0.0)
                unrealized_pct = float(p.get("unrealized_plpc", 0.0) or 0.0) * 100.0
                mkt_val = float(p.get("market_value", 0.0) or 0.0)

                normalized.append({
                    "symbol": p.get("symbol", ""),
                    "qty": qty,
                    "entry_price": entry_p,
                    "current_price": cur_p,
                    "unrealized_pnl_usd": round(unrealized_pl, 4),
                    "unrealized_pnl_pct": round(unrealized_pct, 2),
                    "market_value_usd": round(mkt_val, 2),
                    "side": p.get("side", "long").lower()
                })
            return normalized
        except Exception as e:
            logger.error(f"ALPACA_ADAPTER | Failed to get positions: {e}")
            return []

    async def get_historical_bars(self, symbol: str, interval: str = "1h", limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch historical bars from Alpaca Data API."""
        return await alpaca_client.get_historical_bars(symbol, interval, limit)

    async def get_latest_price(self, symbol: str) -> float:
        """Fetch latest price from Alpaca Data API."""
        return await alpaca_client.get_latest_price(symbol)

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
        """
        Place order on Alpaca.
        If take_profit_price and stop_loss_price are supplied, creates a native server-side bracket order.
        """
        order = await alpaca_client.place_order(
            symbol=symbol,
            side=side,
            qty=quantity,
            order_type=order_type,
            time_in_force=time_in_force,
            take_profit_price=take_profit_price,
            stop_loss_price=stop_loss_price,
            limit_price=limit_price,
        )

        # Standardize return keys for VinBot engine
        return {
            "orderId": order.get("id"),
            "clientOrderId": order.get("client_order_id"),
            "symbol": order.get("symbol"),
            "side": order.get("side", "").upper(),
            "status": order.get("status", "").upper(),
            "executedQty": order.get("filled_qty", "0"),
            "price": order.get("filled_avg_price") or str(limit_price or 0.0),
            "raw": order
        }

    async def cancel_order(self, order_id: Any, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Cancel an order on Alpaca."""
        return await alpaca_client.cancel_order(str(order_id))

    async def close(self):
        await alpaca_client.close()
