import httpx
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from app.core.config import get_settings
from app.core.security import generate_signature, get_timestamp
import time
from app.core.metrics import (
    binance_api_latency,
    binance_active_proxy_index,
    binance_proxy_failovers_total,
)

settings = get_settings()
logger = logging.getLogger(__name__)


def _mask_proxy_url(proxy_url: str) -> str:
    """Mask credentials in proxy URL for safe logging."""
    try:
        parsed = urlparse(proxy_url)
        if parsed.hostname and parsed.port:
            return f"{parsed.scheme}://***@{parsed.hostname}:{parsed.port}"
    except Exception:
        pass
    return "proxy://***"


class BinanceClient:
    def __init__(self, proxy_urls: Optional[List[str]] = None):
        self.api_key = settings.BINANCE_API_KEY
        self.secret_key = settings.BINANCE_SECRET_KEY
        self.time_offset = 0
        self._client: Optional[httpx.AsyncClient] = None
        self._proxy_clients: Dict[str, httpx.AsyncClient] = {}
        self.exchange_info: Dict[str, Any] = {}

        raw_proxies = proxy_urls if proxy_urls is not None else [
            p.strip() for p in settings.BINANCE_PROXY_URLS.split(",") if p.strip()
        ]
        self.proxy_urls: List[str] = raw_proxies
        self._active_proxy_idx: int = 0

        if self.proxy_urls:
            binance_active_proxy_index.set(0)
            masked = [_mask_proxy_url(p) for p in self.proxy_urls]
            logger.info(
                f"NETWORK | Smart Split-Routing initialized with {len(self.proxy_urls)} static proxies: {masked} "
                f"(signed_only={settings.BINANCE_PROXY_SIGNED_ONLY})"
            )
        else:
            binance_active_proxy_index.set(-1)

    def _create_async_client(self, proxy_url: Optional[str] = None) -> httpx.AsyncClient:
        """Create an httpx.AsyncClient with retry transport and short keep-alive for IP resilience."""
        transport = httpx.AsyncHTTPTransport(retries=2)
        limits = httpx.Limits(max_keepalive_connections=10, max_connections=20, keepalive_expiry=30.0)
        kwargs: Dict[str, Any] = {
            "base_url": settings.BINANCE_BASE_URL,
            "timeout": 10.0,
            "transport": transport,
            "limits": limits,
        }
        if proxy_url:
            kwargs["proxy"] = proxy_url
        return httpx.AsyncClient(**kwargs)

    @property
    def client(self) -> httpx.AsyncClient:
        """Direct client (or primary proxy client if BINANCE_PROXY_SIGNED_ONLY is False)."""
        if self._client is None:
            if self.proxy_urls and not settings.BINANCE_PROXY_SIGNED_ONLY:
                self._client = self._create_async_client(self.proxy_urls[self._active_proxy_idx])
            else:
                self._client = self._create_async_client(None)
        return self._client

    def _get_proxy_client(self, proxy_url: str) -> httpx.AsyncClient:
        """Get or create an AsyncClient bound to a specific static proxy URL."""
        if proxy_url not in self._proxy_clients:
            self._proxy_clients[proxy_url] = self._create_async_client(proxy_url)
        return self._proxy_clients[proxy_url]

    def _rotate_proxy(self) -> Optional[str]:
        """Rotate to the next static proxy in the failover list."""
        if not self.proxy_urls:
            return None
        old_idx = self._active_proxy_idx
        self._active_proxy_idx = (self._active_proxy_idx + 1) % len(self.proxy_urls)
        new_proxy = self.proxy_urls[self._active_proxy_idx]
        binance_active_proxy_index.set(self._active_proxy_idx)
        binance_proxy_failovers_total.inc()
        logger.warning(
            f"NETWORK | Failover rotating static proxy [{old_idx} -> {self._active_proxy_idx}]: "
            f"{_mask_proxy_url(new_proxy)}"
        )
        return new_proxy

    async def reset_direct_client(self):
        """Recycle direct HTTP client connection pool after a local ISP IP change."""
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:
                pass
            self._client = None

    async def sync_time(self):
        """Sync local time with Binance server time."""
        try:
            response = await self.client.get("/api/v3/time")
            response.raise_for_status()
            server_time = response.json()["serverTime"]
            local_time = get_timestamp()
            self.time_offset = server_time - local_time
            logger.info(f"Time synced. Offset: {self.time_offset}ms")
        except Exception as e:
            logger.error(f"Failed to sync time: {e}")

    def _get_adjusted_timestamp(self) -> int:
        return get_timestamp() + self.time_offset

    def _should_use_proxy(self, signed: bool) -> bool:
        """Determine whether this request should route via the static proxy pool."""
        if not self.proxy_urls:
            return False
        if signed:
            return True
        return not settings.BINANCE_PROXY_SIGNED_ONLY

    async def request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None, 
        signed: bool = False,
        _retry_time_sync: bool = True
    ) -> Dict[str, Any]:
        """Base request method with Smart Split-Routing, static proxy failover, and -1021 resync."""
        headers = {"X-MBX-APIKEY": self.api_key}
        current_params = params.copy() if params else {}
        
        if not endpoint.startswith("/api"):
            if endpoint.startswith("/v3"):
                endpoint = f"/api{endpoint}"
            else:
                endpoint = f"/api/v3/{endpoint.lstrip('/')}"
        
        if signed:
            current_params["timestamp"] = self._get_adjusted_timestamp()
            current_params["recvWindow"] = 10000
            query_string = "&".join([f"{k}={v}" for k, v in current_params.items()])
            current_params["signature"] = generate_signature(query_string, self.secret_key)

        use_proxy = self._should_use_proxy(signed)
        attempts = len(self.proxy_urls) if use_proxy else 1
        last_error: Optional[Exception] = None

        for attempt in range(attempts):
            active_client: httpx.AsyncClient
            route_label = "DIRECT"
            if use_proxy:
                proxy_url = self.proxy_urls[self._active_proxy_idx]
                active_client = self._get_proxy_client(proxy_url)
                route_label = _mask_proxy_url(proxy_url)
            else:
                active_client = self.client

            start_time = time.perf_counter()
            try:
                response = await active_client.request(method, endpoint, params=current_params, headers=headers)
                latency = time.perf_counter() - start_time
                binance_api_latency.labels(endpoint=endpoint, method=method).observe(latency)

                # Retry logic for -1021 (Timestamp out of recvWindow)
                if response.status_code == 400 and _retry_time_sync:
                    error_data = response.json()
                    if error_data.get("code") == -1021:
                        logger.warning("Timestamp out of window, resyncing time and retrying...")
                        await self.sync_time()
                        return await self.request(method, endpoint, params, signed, _retry_time_sync=False)

                # Rotate proxy on geo-block (451), IP auth error (-2015 on 401/403), or bad gateway (502/503/504)
                if use_proxy and response.status_code in (451, 502, 503, 504) and len(self.proxy_urls) > 1:
                    logger.warning(f"NETWORK | HTTP {response.status_code} via {route_label}, rotating proxy...")
                    self._rotate_proxy()
                    continue

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error ({route_label}): {e.response.text}")
                raise e
            except httpx.RequestError as e:
                last_error = e
                logger.warning(f"NETWORK | Transport error on {endpoint} via {route_label}: {e}")
                if use_proxy and len(self.proxy_urls) > 1:
                    self._rotate_proxy()
                    # Recompute timestamp/signature if signed before next attempt
                    if signed:
                        current_params.pop("signature", None)
                        current_params["timestamp"] = self._get_adjusted_timestamp()
                        query_string = "&".join([f"{k}={v}" for k, v in current_params.items()])
                        current_params["signature"] = generate_signature(query_string, self.secret_key)
                    continue
                elif not use_proxy:
                    # Local ISP IP may have changed; reset direct connection pool
                    await self.reset_direct_client()
                    raise e
            except Exception as e:
                logger.error(f"Request error ({route_label}): {e}")
                raise e

        if last_error:
            raise last_error
        raise RuntimeError(f"Failed request to {endpoint}")

    async def get_exchange_info(self, symbol: str) -> Dict[str, Any]:
        """Fetch and cache LOT_SIZE for a symbol."""
        if symbol not in self.exchange_info:
            logger.info(f"Fetching exchange info for {symbol}...")
            data = await self.request("GET", "/api/v3/exchangeInfo", params={"symbol": symbol})
            symbol_data = next((s for s in data["symbols"] if s["symbol"] == symbol), None)
            if symbol_data:
                lot_size = next((f for f in symbol_data["filters"] if f["filterType"] == "LOT_SIZE"), None)
                if lot_size:
                    self.exchange_info[symbol] = lot_size
        return self.exchange_info.get(symbol, {})
    
    async def get_asset_balance(self, asset: str) -> Dict[str, str]:
        """Fetch balance for a specific asset."""
        account = await self.request("GET", "/api/v3/account", signed=True)
        balances = account.get("balances", [])
        asset_bal = next((b for b in balances if b["asset"] == asset.upper()), {"free": "0.0", "locked": "0.0"})
        return asset_bal

    @staticmethod
    def round_step(quantity: float, step_size: float) -> str:
        """Truncate quantity to the nearest valid step size for Binance, correctly handling scientific notation."""
        from decimal import Decimal, ROUND_DOWN
        
        # Convert to Decimal for precision
        q = Decimal(str(quantity))
        s = Decimal(str(step_size))
        
        # Calculate quantity as a multiple of step_size
        rounded = (q / s).quantize(Decimal('1'), rounding=ROUND_DOWN) * s
        
        # Determine number of decimal places for formatting
        s_norm = s.normalize()
        exponent = s_norm.as_tuple().exponent
        if isinstance(exponent, int) and exponent < 0:
            precision = abs(exponent)
        else:
            precision = 0
            
        return f"{rounded:.{precision}f}"

    async def close(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        for client in self._proxy_clients.values():
            try:
                await client.aclose()
            except Exception:
                pass
        self._proxy_clients.clear()

binance_client = BinanceClient()
