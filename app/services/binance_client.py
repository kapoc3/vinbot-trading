import httpx
import logging
from typing import Dict, Any, Optional
from app.core.config import get_settings
from app.core.security import generate_signature, get_timestamp

settings = get_settings()
logger = logging.getLogger(__name__)

class BinanceClient:
    def __init__(self):
        self.base_url = settings.BINANCE_BASE_URL
        self.api_key = settings.BINANCE_API_KEY
        self.secret_key = settings.BINANCE_SECRET_KEY
        self.time_offset = 0
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    async def sync_time(self):
        """Sync local time with Binance server time."""
        try:
            response = await self.client.get("/v3/time")
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
        
        if signed:
            params["timestamp"] = self._get_adjusted_timestamp()
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            params["signature"] = generate_signature(query_string, self.secret_key)

        try:
            response = await self.client.request(method, endpoint, params=params, headers=headers)
            
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

    async def close(self):
        await self.client.aclose()

binance_client = BinanceClient()
