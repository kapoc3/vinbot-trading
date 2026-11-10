import logging
from typing import Dict, Any, List, Optional, Set
from app.core.config import get_settings
from app.services.binance_client import binance_client, BinanceClient

logger = logging.getLogger(__name__)

# Common stablecoins and fiat pegs to exclude from momentum scanning
EXCLUDED_BASE_ASSETS: Set[str] = {
    "USDT", "USDC", "BUSD", "TUSD", "FDUSD", "DAI", "EUR", "GBP", "TRY",
    "BRL", "RUB", "USDP", "AEUR", "AUD", "BIDR", "IDRT", "NGN", "PLN",
    "RON", "UAH", "ZAR", "USTC", "WBTC", "WETH"
}


class MarketScanner:
    """
    Market Scanner Service for VinBot Core-Satellite architecture.
    Queries Binance public rolling window tickers to dynamically discover and rank
    hot momentum cryptocurrencies by unusual volume and price surges.
    """

    def __init__(self, client: Optional[BinanceClient] = None):
        self.client = client or binance_client
        self.settings = get_settings()

    @staticmethod
    def calculate_momentum_score(
        price_change_pct: float,
        quote_volume: float,
        trades_count: int = 0
    ) -> float:
        """
        Momentum score combining price velocity (60%) and liquidity depth (40%).
        Liquidity is normalized against a $50M USD volume benchmark.
        """
        volume_factor = min(1.0, max(0.0, quote_volume / 50_000_000.0))
        score = (price_change_pct * 0.6) + (volume_factor * 40.0)
        return round(score, 4)

    def _get_excluded_symbols(self) -> Set[str]:
        """Fetch symbols configured to be excluded (e.g. Core Bot symbols)."""
        raw = getattr(self.settings, "SCANNER_EXCLUDE_SYMBOLS", "")
        return {s.strip().upper() for s in raw.split(",") if s.strip()}

    async def scan_hot_markets(
        self,
        quote_asset: Optional[str] = None,
        top_n: Optional[int] = None,
        min_volume: Optional[float] = None,
        window_size: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scan Binance rolling tickers for hot momentum candidates.
        Performs ultra-light public request with zero authenticated proxy overhead.
        """
        # Determine defaults
        if quote_asset is None:
            if any("USDC" in s for s in self.settings.TRADING_SYMBOLS.split(",")):
                quote_asset = "USDC"
            else:
                quote_asset = "USDT"

        quote_asset = quote_asset.upper()
        top_n = top_n if top_n is not None else getattr(self.settings, "SCANNER_TOP_N", 3)
        min_vol = min_volume if min_volume is not None else getattr(self.settings, "SCANNER_MIN_VOLUME_USD", 10_000_000.0)
        win_size = window_size or getattr(self.settings, "SCANNER_WINDOW_SIZE", "1h")

        excluded_symbols = self._get_excluded_symbols()

        try:
            tickers = await self.client.get_tickers(window_size=win_size)
        except Exception as e:
            logger.error(f"SCANNER | Error fetching tickers from Binance: {e}")
            return []

        candidates: List[Dict[str, Any]] = []

        for t in tickers:
            symbol = t.get("symbol", "").upper()
            if not symbol.endswith(quote_asset):
                continue

            base_asset = symbol[:-len(quote_asset)]
            if base_asset in EXCLUDED_BASE_ASSETS or symbol in excluded_symbols:
                continue

            try:
                quote_vol = float(t.get("quoteVolume", 0.0))
                price_change = float(t.get("priceChangePercent", 0.0))
                last_price = float(t.get("lastPrice", 0.0))
                trades_cnt = int(t.get("count", 0))
            except (ValueError, TypeError):
                continue

            # Must meet minimum volume threshold and have positive momentum
            if quote_vol < min_vol or price_change <= 0.0:
                continue

            score = self.calculate_momentum_score(price_change, quote_vol, trades_cnt)
            candidates.append({
                "symbol": symbol,
                "base_asset": base_asset,
                "quote_asset": quote_asset,
                "price_change_pct": price_change,
                "quote_volume": quote_vol,
                "last_price": last_price,
                "trades_count": trades_cnt,
                "score": score,
            })

        # Rank candidates by momentum score descending
        candidates.sort(key=lambda x: x["score"], reverse=True)
        top_candidates = candidates[:top_n]

        logger.info(
            f"SCANNER | Scan complete for {quote_asset} ({win_size}): {len(candidates)} qualified, "
            f"top {len(top_candidates)}: {[c['symbol'] for c in top_candidates]}"
        )
        return top_candidates

    def filter_rotation_symbols(
        self,
        current_symbols: List[str],
        scanned_candidates: List[Dict[str, Any]],
        locked_symbols: List[str],
        max_symbols: int,
    ) -> Dict[str, Any]:
        """
        Calculate symbol rotation plan strictly enforcing Position Locking.
        
        Rules:
        1. Any symbol with an open position (locked_symbols) CANNOT be removed until closed.
        2. Fill remaining slots up to max_symbols with top scored candidates.
        3. If slots still remain, preserve existing symbols to avoid unnecessary churn.
        """
        target_symbols: List[str] = []
        locked_set = {s.upper() for s in locked_symbols}

        # 1. Lock in all active position symbols first
        for s in locked_symbols:
            s_clean = s.strip().upper()
            if s_clean and s_clean not in target_symbols:
                target_symbols.append(s_clean)

        # 2. Add top scanned candidates if open slots exist
        for candidate in scanned_candidates:
            if len(target_symbols) >= max_symbols:
                break
            cand_sym = candidate["symbol"].strip().upper()
            if cand_sym not in target_symbols:
                target_symbols.append(cand_sym)

        # 3. If still below max_symbols, backfill with existing symbols to preserve continuity
        for curr in current_symbols:
            if len(target_symbols) >= max_symbols:
                break
            curr_clean = curr.strip().upper()
            if curr_clean and curr_clean not in target_symbols:
                target_symbols.append(curr_clean)

        current_clean = [s.strip().upper() for s in current_symbols if s.strip()]
        symbols_to_add = [s for s in target_symbols if s not in current_clean]
        symbols_to_remove = [s for s in current_clean if s not in target_symbols and s not in locked_set]
        symbols_to_keep = [s for s in current_clean if s in target_symbols or s in locked_set]

        return {
            "target_symbols": target_symbols,
            "to_add": symbols_to_add,
            "to_remove": symbols_to_remove,
            "to_keep": symbols_to_keep,
        }


market_scanner = MarketScanner()

