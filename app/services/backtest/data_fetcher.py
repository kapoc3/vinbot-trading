"""
Historical data fetcher for backtesting.
Downloads and caches klines from Binance.
"""
import os
import csv
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

import httpx
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

KLINE_INTERVALS = ["1m", "5m", "15m", "1h", "4h", "1d"]


@dataclass
class Kline:
    """Represents a single kline (candle)."""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int


class HistoricalDataFetcher:
    """Fetches and caches historical kline data from Binance."""

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or settings.BACKTEST_CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
        self.base_url = settings.BINANCE_BASE_URL
        self.max_klines = 1000  # Binance API limit per request

    def _get_cache_path(self, symbol: str, interval: str, start: int, end: int) -> str:
        """Generate cache file path."""
        start_date = datetime.fromtimestamp(start / 1000).strftime("%Y%m%d")
        end_date = datetime.fromtimestamp(end / 1000).strftime("%Y%m%d")
        filename = f"{symbol}_{interval}_{start_date}_{end_date}.csv"
        return os.path.join(self.cache_dir, filename)

    def fetch_klines(
        self,
        symbol: str,
        interval: str = "1h",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000
    ) -> List[Kline]:
        """
        Fetch historical klines from Binance.

        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            interval: Kline interval (1m, 5m, 15m, 1h, 4h, 1d)
            start_date: Start date string (YYYY-MM-DD)
            end_date: End date string (YYYY-MM-DD)
            limit: Number of klines to fetch (max 1000 per request)

        Returns:
            List of Kline objects
        """
        if interval not in KLINE_INTERVALS:
            raise ValueError(f"Invalid interval. Must be one of {KLINE_INTERVALS}")

        # Parse dates to timestamps
        start_ts = int(datetime.strptime(start_date or "2024-01-01", "%Y-%m-%d").timestamp() * 1000)
        end_ts = int(datetime.strptime(end_date or datetime.now().strftime("%Y-%m-%d"), "%Y-%m-%d").timestamp() * 1000)

        # Check cache first
        cache_path = self._get_cache_path(symbol, interval, start_ts, end_ts)
        if os.path.exists(cache_path):
            logger.info(f"Loading {symbol} {interval} from cache: {cache_path}")
            return self._load_from_cache(cache_path)

        # Fetch from Binance
        klines = self._fetch_all_klines(symbol, interval, start_ts, end_ts, limit)

        if klines:
            self._save_to_cache(cache_path, klines)
            logger.info(f"Fetched and cached {len(klines)} klines for {symbol} {interval}")

        return klines

    def _fetch_all_klines(
        self,
        symbol: str,
        interval: str,
        start_ts: int,
        end_ts: int,
        limit: int
    ) -> List[Kline]:
        """Fetch all klines in batches (handling Binance 1000 limit)."""
        all_klines = []
        current_start = start_ts

        async def fetch():
            async with httpx.AsyncClient(timeout=30.0) as client:
                while current_start < end_ts:
                    url = f"{self.base_url}/api/v3/klines"
                    params = {
                        "symbol": symbol,
                        "interval": interval,
                        "startTime": current_start,
                        "endTime": end_ts,
                        "limit": min(limit, self.max_klines)
                    }

                    try:
                        response = await client.get(url, params=params)
                        if response.status_code == 429:
                            # Rate limited - wait and retry
                            retry_after = int(response.headers.get("Retry-After", 5))
                            logger.warning(f"Rate limited, waiting {retry_after}s")
                            time.sleep(retry_after)
                            continue

                        response.raise_for_status()
                        data = response.json()

                        if not data:
                            break

                        klines = [self._parse_kline(k) for k in data]
                        all_klines.extend(klines)

                        # Move start forward
                        current_start = klines[-1].close_time + 1

                        logger.info(f"Fetched {len(klines)} klines, total: {len(all_klines)}")

                    except httpx.HTTPStatusError as e:
                        logger.error(f"HTTP error fetching klines: {e}")
                        break
                    except Exception as e:
                        logger.error(f"Error fetching klines: {e}")
                        break

        # Run sync for now (will be called from async context)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context - need to use run_until_complete differently
                # For simplicity, make a new event loop
                asyncio.run(fetch())
            else:
                loop.run_until_complete(fetch())
        except RuntimeError:
            asyncio.run(fetch())

        return all_klines

    def _parse_kline(self, k: list) -> Kline:
        """Parse a Binance kline response into a Kline object."""
        return Kline(
            timestamp=int(k[0]),
            open=float(k[1]),
            high=float(k[2]),
            low=float(k[3]),
            close=float(k[4]),
            volume=float(k[5]),
            close_time=int(k[6])
        )

    def _load_from_cache(self, cache_path: str) -> List[Kline]:
        """Load klines from CSV cache file."""
        klines = []
        with open(cache_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                klines.append(Kline(
                    timestamp=int(row['timestamp']),
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=float(row['volume']),
                    close_time=int(row['close_time'])
                ))
        return klines

    def _save_to_cache(self, cache_path: str, klines: List[Kline]):
        """Save klines to CSV cache file."""
        with open(cache_path, 'w', newline='') as f:
            fieldnames = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for k in klines:
                writer.writerow({
                    'timestamp': k.timestamp,
                    'open': k.open,
                    'high': k.high,
                    'low': k.low,
                    'close': k.close,
                    'volume': k.volume,
                    'close_time': k.close_time
                })

    def get_klines_as_dataframe(self, klines: List[Kline]):
        """Convert klines to pandas DataFrame."""
        try:
            import pandas as pd
            data = [{
                'timestamp': k.timestamp,
                'open': k.open,
                'high': k.high,
                'low': k.low,
                'close': k.close,
                'volume': k.volume
            } for k in klines]
            return pd.DataFrame(data)
        except ImportError:
            logger.warning("pandas not installed, returning list")
            return klines