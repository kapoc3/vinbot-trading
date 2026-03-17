# Design: VWAP and OBV Integration

## Goals
1. Accurately calculate continuous OBV (On-Balance Volume) and a rolling/session VWAP.
2. Provide a global strict mode where "BUY" signals from any underlying strategy are vetoed if the price is below VWAP or if OBV is declining.
3. Maintain fast execution logic so the indicator additions do not slow the websocket listener.

## Non-Goals
* Re-writing individual momentum strategies. This will act as an independent filter overlay, much like the ATR trailing stop.

## Solution Outline
1. **Mathematical Implementation (`indicators.py`):**
   * **OBV:** `OBV_current = OBV_prev + volume` (if close > prev_close) OR `- volume` (if close < prev_close).
   * **VWAP:** Standard session VWAP usually resets daily. For crypto, a rolling N-period VWAP (e.g., 50 or 100 periods) is often better, or a cumulative VWAP since bot startup. We will implement a rolling window VWAP (`sum(Typical_Price * Volume) / sum(Volume)`) for the last N periods to maintain relevance without arbitrary daily resets. (Typical Price = `(High + Low + Close) / 3`).

2. **Integration (`strategy_factory.py`):**
   * The `DynamicStrategyProxy.analyze` will first run the normal strategy logic to get a signal.
   * If the signal is `BUY`, and `ENABLE_VOLUME_CONFIRMATION` is `True`, it runs a veto check:
     * Check if `current_price` >= `current_vwap`.
     * Check if `current_obv` >= `sma(obv, 20)` (OBV trend is positive).
     * If both pass, allow the `BUY`. If not, veto and return `None`.

3. **Configuration (`config.py`):**
   * Add `ENABLE_VOLUME_CONFIRMATION: bool = False` (Optional boolean to enable these strict checks).
   * Add `VWAP_PERIOD: int = 50`.
