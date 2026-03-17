# Design: Dynamic Position Sizing

## Overview
This feature introduces algorithmic quantity sizing into the execution loop, replacing the hardcoded conditional quantities currently in `main.py`.

## Technical Modifications

1.  **Configuration Adjustments (`app/core/config.py`):**
    *   Add `ALLOCATED_CAPITAL: float = 1000.0` (Total synthetic capital to base risk upon. This is safer than querying entire free USDT balance until advanced account sync is built).
    *   Add `RISK_PER_TRADE_PCT: float = 1.0` (Percentage of allocated capital to risk).
    *   Add `ENABLE_DYNAMIC_SIZING: bool = True` to toggle the feature vs fixed fallback logic.

2.  **Risk Manager Math (`app/services/risk_manager.py`):**
    *   Create a dedicated sizing method: `calculate_position_size(symbol: str, entry_price: float, sl_price: float) -> float`.
    *   Implement the Kelly/Risk formulation:
        `capital_at_risk = allocated_capital * (risk_pct / 100.0)`
        `price_risk_per_unit = entry_price - sl_price`
        `if price_risk_per_unit <= 0 : return 0.0`
        `raw_qty = capital_at_risk / price_risk_per_unit`

3.  **Binance API & Lot Size Formatting (`app/services/binance_client.py`):**
    *   Binance enforces strict `LOT_SIZE` filters. A raw calculated quantity like `0.3421591` will bounce with an API error.
    *   We need to query `/v3/exchangeInfo` once on startup, cache the `stepSize` for configured symbols, and write a utility to round down the calculated quantity to the nearest valid step.

4.  **Integration (`app/main.py`):**
    *   When the Strategy returns a `BUY` signal:
        *   Determine the intended entry price (current close).
        *   Determine the intended SL (current price * (1 - STOP_LOSS_PCT/100) or dynamic trailing initialization).
        *   Call `risk_manager.calculate_position_size()` to obtain the raw quantity.
        *   Format quantity against the cached `LOT_SIZE` step.
        *   Place the `place_market_order` with this new dynamic quantity.
