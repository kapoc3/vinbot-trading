import json
import asyncio
import websockets
import logging
from typing import List, Dict, Any, Callable
from app.core.config import get_settings
from app.services.binance_client import binance_client

settings = get_settings()
logger = logging.getLogger(__name__)

class MarketDataService:
    def __init__(self):
        self.ws_url = settings.BINANCE_WS_URL
        self.active_streams = []

    async def get_historical_klines(self, symbol: str, interval: str, limit: int = 500) -> List[List[Any]]:
        """Get historical klines via REST."""
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        return await binance_client.request("GET", "/api/v3/klines", params=params)

    async def stream_klines(self, symbol: str, interval: str, callback: Callable):
        """Stream klines in real-time via WebSocket with reconnection logic."""
        url = f"{self.ws_url}/{symbol.lower()}@kline_{interval}"
        await self._stream_with_reconnect(url, callback)

    async def stream_depth(self, symbol: str, callback: Callable):
        """Stream order book depth in real-time (Requirement: Order Book Depth Tracking)."""
        url = f"{self.ws_url}/{symbol.lower()}@depth"
        await self._stream_with_reconnect(url, callback)

    async def _stream_with_reconnect(self, url: str, callback: Callable):
        """Generic stream with heartbeat, read-timeout watchdog, and ISP IP-change resilience."""
        backoff = 2
        while True:
            try:
                async with websockets.connect(
                    url,
                    ping_interval=settings.WS_PING_INTERVAL,
                    ping_timeout=settings.WS_PING_TIMEOUT,
                    close_timeout=5,
                ) as websocket:
                    logger.info(f"Connected to WebSocket: {url}")
                    backoff = 2
                    while True:
                        raw_msg = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=settings.WS_READ_TIMEOUT,
                        )
                        data = json.loads(raw_msg)
                        await callback(data)
            except asyncio.CancelledError:
                logger.info(f"WebSocket task cancelled for {url}")
                raise
            except asyncio.TimeoutError:
                logger.warning(
                    f"NETWORK | WebSocket read watchdog triggered on {url} "
                    f"(>{settings.WS_READ_TIMEOUT}s silence; possible ISP IP change). Reconnecting..."
                )
                await binance_client.reset_direct_client()
                await binance_client.sync_time()
                await asyncio.sleep(backoff)
            except Exception as e:
                logger.error(f"WebSocket error on {url}: {e}. Reconnecting in {backoff}s...")
                await binance_client.reset_direct_client()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)

market_service = MarketDataService()
