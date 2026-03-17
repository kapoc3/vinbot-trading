# Design: BTC Directional Filter

## Goals
1. Provide a mechanism to completely block new long positions (BUY signals) across all strategies if Bitcoin is in a downtrend.
2. Ensure `BTCUSDT` historical data and real-time streams are always active globally if this filter is enabled.
3. Keep the logic centralized within the `DynamicStrategyProxy` to avoid modifying every individual strategy class.

## Non-Goals
* Implementing a long/short mechanism. The bot remains long-only.
* Creating complex BTC-correlation matrices. This is a simple binary macro filter (Is BTC bullish? Yes/No).

## Solution Outline

1. **Configuration (`app/core/config.py`):**
   * Add `ENABLE_BTC_DIRECTIONAL_FILTER: bool = True`.
   * Add `BTC_DIRECTION_EMA: int = 200` (Default to a longer-term trend EMA, like the 200-period EMA).

2. **Global Data Availability (`app/main.py`):**
   * In the startup loop and `market_service` initialization, check if `ENABLE_BTC_DIRECTIONAL_FILTER` is `True`.
   * If true, forcefully append `"BTCUSDT"` to the list of active tracking symbols internally (if not already present). This ensures we fetch its historical klines and listen to its websocket stream.

3. **Proxy Interceptor (`app/services/strategy_factory.py`):**
   * Within `DynamicStrategyProxy.analyze(symbol)`:
     * If the signal from the underlying strategy is `"BUY"` and `ENABLE_BTC_DIRECTIONAL_FILTER` is `True`:
       * Retrieve `BTCUSDT` indicator data via `market_indicators.get("BTCUSDT")`.
       * Compare the current BTC price against its configured EMA (e.g., EMA 200).
       * If `btc_current_price < btc_ema_200`, log a veto message (e.g., "VETO: Market is bearish (BTC below EMA)") and return `None` instead of `"BUY"`.
     * Note: If the symbol being analyzed *is* `BTCUSDT`, the filter applies to itself as well, essentially meaning the bot will only trade BTC when it's above its own EMA (a common trend-following rule).

4. **Indicator Refinement (`app/services/indicators.py`):**
   * Ensure `get_ema()` or `calculate_ema()` on `SymbolData` is robust enough to pull the specific EMA period required by the config, so we can reliably call `btc_data.get_ema(settings.BTC_DIRECTION_EMA)`.
