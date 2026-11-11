import logging
import httpx
from typing import Dict, Any, List, Optional
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AlpacaClient:
    """
    Asynchronous client for Alpaca Markets API v2 (Trading & Market Data).
    Supports US Equities (Stocks, ETFs) with zero commission and Crypto with native bracket orders.
    """

    def __init__(self):
        self._trading_client: Optional[httpx.AsyncClient] = None
        self._data_client: Optional[httpx.AsyncClient] = None

    def _get_headers(self) -> Dict[str, str]:
        return {
            "APCA-API-KEY-ID": settings.ALPACA_API_KEY,
            "APCA-API-SECRET-KEY": settings.ALPACA_SECRET_KEY,
            "Content-Type": "application/json"
        }

    def _get_trading_client(self) -> httpx.AsyncClient:
        if self._trading_client is None or self._trading_client.is_closed:
            base_url = settings.ALPACA_BASE_URL.rstrip("/")
            self._trading_client = httpx.AsyncClient(
                base_url=base_url,
                headers=self._get_headers(),
                timeout=settings.ALPACA_TIMEOUT_SECONDS
            )
        return self._trading_client

    def _get_data_client(self) -> httpx.AsyncClient:
        if self._data_client is None or self._data_client.is_closed:
            base_url = settings.ALPACA_DATA_URL.rstrip("/")
            self._data_client = httpx.AsyncClient(
                base_url=base_url,
                headers=self._get_headers(),
                timeout=settings.ALPACA_TIMEOUT_SECONDS
            )
        return self._data_client

    async def request_trading(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform request against Alpaca Trading API v2."""
        client = self._get_trading_client()
        clean_endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        try:
            res = await client.request(method, clean_endpoint, params=params, json=json_data)
            res.raise_for_status()
            return res.json() if res.content else {}
        except httpx.HTTPStatusError as e:
            logger.error(f"ALPACA_CLIENT | Trading HTTP {e.response.status_code} error on {endpoint}: {e.response.text}")
            raise e
        except Exception as e:
            logger.error(f"ALPACA_CLIENT | Request failed on {endpoint}: {e}")
            raise e

    async def request_data(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform request against Alpaca Market Data API."""
        client = self._get_data_client()
        clean_endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        try:
            res = await client.request(method, clean_endpoint, params=params)
            res.raise_for_status()
            return res.json() if res.content else {}
        except httpx.HTTPStatusError as e:
            logger.error(f"ALPACA_CLIENT | Data HTTP {e.response.status_code} error on {endpoint}: {e.response.text}")
            raise e
        except Exception as e:
            logger.error(f"ALPACA_CLIENT | Data request failed on {endpoint}: {e}")
            raise e

    # ==================== ACCOUNT & POSITIONS ====================

    async def get_account(self) -> Dict[str, Any]:
        """Get account details (equity, cash, buying power, status)."""
        return await self.request_trading("GET", "/v2/account")

    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions held in Alpaca."""
        res = await self.request_trading("GET", "/v2/positions")
        return res if isinstance(res, list) else []

    async def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position for a specific symbol."""
        try:
            return await self.request_trading("GET", f"/v2/positions/{symbol}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise e

    async def close_position(self, symbol: str, qty: Optional[float] = None) -> Dict[str, Any]:
        """Liquidate / sell position on market."""
        params = {"qty": str(qty)} if qty else {}
        return await self.request_trading("DELETE", f"/v2/positions/{symbol}", params=params)

    # ==================== ORDERS ====================

    async def place_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        order_type: str = "market",
        time_in_force: str = "gtc",
        take_profit_price: Optional[float] = None,
        stop_loss_price: Optional[float] = None,
        limit_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Submit an order to Alpaca.
        If take_profit_price and stop_loss_price are specified, creates a native server-side bracket order.
        """
        payload: Dict[str, Any] = {
            "symbol": symbol.upper(),
            "qty": str(qty),
            "side": side.lower(),
            "type": order_type.lower(),
            "time_in_force": time_in_force.lower(),
        }

        if limit_price and order_type.lower() == "limit":
            payload["limit_price"] = str(limit_price)

        # Build native bracket order if SL/TP are provided
        if take_profit_price is not None and stop_loss_price is not None:
            payload["order_class"] = "bracket"
            payload["take_profit"] = {"limit_price": str(round(take_profit_price, 2))}
            payload["stop_loss"] = {"stop_price": str(round(stop_loss_price, 2))}
            logger.info(
                f"ALPACA_CLIENT | Submitting BRACKET order for {symbol}: Side={side}, Qty={qty}, "
                f"TP=${take_profit_price:.2f}, SL=${stop_loss_price:.2f}"
            )

        return await self.request_trading("POST", "/v2/orders", json_data=payload)

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order by ID."""
        return await self.request_trading("DELETE", f"/v2/orders/{order_id}")

    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Fetch order status by ID."""
        return await self.request_trading("GET", f"/v2/orders/{order_id}")

    # ==================== MARKET DATA ====================

    async def get_latest_price(self, symbol: str) -> float:
        """Fetch latest market trade price for stocks or crypto."""
        sym = symbol.upper()
        is_crypto = "/" in sym or "USD" in sym and len(sym) > 5
        try:
            if is_crypto:
                crypto_sym = sym if "/" in sym else f"{sym[:-4]}/{sym[-3:]}"
                res = await self.request_data("GET", "/v1beta3/crypto/us/latest/trades", params={"symbols": crypto_sym})
                trades = res.get("trades", {})
                trade = trades.get(crypto_sym, {})
                return float(trade.get("p", 0.0))
            else:
                res = await self.request_data("GET", f"/v2/stocks/{sym}/trades/latest")
                trade = res.get("trade", {})
                return float(trade.get("p", 0.0))
        except Exception as e:
            logger.error(f"ALPACA_CLIENT | Could not fetch latest price for {symbol}: {e}")
            return 0.0

    async def get_historical_bars(self, symbol: str, interval: str = "1h", limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch historical bars normalized to standard OHLCV."""
        sym = symbol.upper()
        is_crypto = "/" in sym or ("USD" in sym and len(sym) > 5)

        # Map VinBot intervals to Alpaca timeframe format
        tf_map = {
            "1m": "1Min",
            "5m": "5Min",
            "15m": "15Min",
            "1h": "1Hour",
            "1d": "1Day",
        }
        timeframe = tf_map.get(interval, "1Hour")

        try:
            if is_crypto:
                crypto_sym = sym if "/" in sym else f"{sym[:-4]}/{sym[-3:]}"
                res = await self.request_data(
                    "GET",
                    "/v1beta3/crypto/us/bars",
                    params={"symbols": crypto_sym, "timeframe": timeframe, "limit": limit}
                )
                raw_bars = res.get("bars", {}).get(crypto_sym, [])
            else:
                res = await self.request_data(
                    "GET",
                    f"/v2/stocks/{sym}/bars",
                    params={"timeframe": timeframe, "limit": limit}
                )
                raw_bars = res.get("bars", [])

            formatted = []
            for b in raw_bars:
                # Alpaca timestamps are ISO format e.g. "2026-11-10T20:00:00Z"
                from datetime import datetime
                t_str = b.get("t", "")
                epoch_ms = 0
                if t_str:
                    try:
                        dt = datetime.fromisoformat(t_str.replace("Z", "+00:00"))
                        epoch_ms = int(dt.timestamp() * 1000)
                    except Exception:
                        pass

                formatted.append({
                    "time": epoch_ms,
                    "open": float(b.get("o", 0.0)),
                    "high": float(b.get("h", 0.0)),
                    "low": float(b.get("l", 0.0)),
                    "close": float(b.get("c", 0.0)),
                    "volume": float(b.get("v", 0.0))
                })
            return formatted
        except Exception as e:
            logger.error(f"ALPACA_CLIENT | Error fetching bars for {symbol}: {e}")
            return []

    async def close(self):
        """Close clients."""
        if self._trading_client is not None:
            await self._trading_client.aclose()
            self._trading_client = None
        if self._data_client is not None:
            await self._data_client.aclose()
            self._data_client = None


alpaca_client = AlpacaClient()

