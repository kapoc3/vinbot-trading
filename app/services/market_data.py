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
        return await binance_client.request("GET", "/v3/klines", params=params)

    async def stream_klines(self, symbol: str, interval: str, callback: Callable):
        """Stream klines in real-time via WebSocket with reconnection logic."""
        url = f"{self.ws_url}/{symbol.lower()}@kline_{interval}"
        await self._stream_with_reconnect(url, callback)

    async def stream_depth(self, symbol: str, callback: Callable):
        """Stream order book depth in real-time (Requirement: Order Book Depth Tracking)."""
        url = f"{self.ws_url}/{symbol.lower()}@depth"
        await self._stream_with_reconnect(url, callback)

    async def _stream_with_reconnect(self, url: str, callback: Callable):
        """Generic stream with reconnection logic."""
        while True:
            try:
                async with websockets.connect(url) as websocket:
                    logger.info(f"Connected to WebSocket: {url}")
                    async for message in websocket:
                        data = json.loads(message)
                        await callback(data)
            except Exception as e:
                logger.error(f"WebSocket error on {url}: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)

market_service = MarketDataService()
