import httpx
import logging
from typing import Dict, Any, Optional
from app.core.config import get_settings
from app.core.security import generate_signature, get_timestamp
import time
from app.core.metrics import binance_api_latency

settings = get_settings()
logger = logging.getLogger(__name__)

class BinanceClient:
    def __init__(self):
        self.api_key = settings.BINANCE_API_KEY
        self.secret_key = settings.BINANCE_SECRET_KEY
        self.time_offset = 0
        self._client: Optional[httpx.AsyncClient] = None
        self.exchange_info: Dict[str, Any] = {}

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=settings.BINANCE_BASE_URL, timeout=10.0)
        return self._client

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

    async def request(
        self, 
        method: str, 
        endpoint: str, 
        params: Dict[str, Any] = {}, 
        signed: bool = False
    ) -> Dict[str, Any]:
        """Base request method with signature and error handling."""
        headers = {"X-MBX-APIKEY": self.api_key}
        
        # Ensure endpoint starts with /api/v3 if not present (to be robust)
        if not endpoint.startswith("/api"):
            if not endpoint.startswith("/"):
                endpoint = f"/api/v3/{endpoint}"
            else:
                endpoint = f"/api{endpoint}"
        elif not endpoint.startswith("/api/v3"):
            # If it starts with /api but not /api/v3 (edge case)
            pass 
        

        if signed:
            params["timestamp"] = self._get_adjusted_timestamp()
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            params["signature"] = generate_signature(query_string, self.secret_key)

        start_time = time.perf_counter()
        try:
            response = await self.client.request(method, endpoint, params=params, headers=headers)
            latency = time.perf_counter() - start_time
            binance_api_latency.labels(endpoint=endpoint, method=method).observe(latency)
            
            # Implementation of task 2.3: Retry logic for -1021
            if response.status_code == 400:
                error_data = response.json()
                if error_data.get("code") == -1021:
                    logger.warning("Timestamp out of window, resyncing time and retrying...")
                    await self.sync_time()
                    return await self.request(method, endpoint, params, signed)
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.text}")
            raise e
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise e

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
        await self.client.aclose()

binance_client = BinanceClient()
