# Design: Breakout Trading Strategy

## Goals
1. **Capture Early Trends:** Enter a position precisely when the price breaks established multi-period highs/lows.
2. **Volume Filtering:** Ensure breakouts are supported by trading volume (avoiding "fakeouts").
3. **Seamless Integration:** Be a selectable option (`TRADING_STRATEGY="Breakout"`) and be usable by the `Auto` strategy manager.

## Non-Goals
* Replacing Bollinger Bands. (Bollinger is meant for mean reversion during ranging regimes; Donchian Breakout is for the end of the ranging regime).

## Solution Outline
1. **TechnicalIndicators Updates**
   * Provide `calculate_donchian_channel(highs, lows, period=20)`:
     * Upper Band = `max(highs[-period:])`
     * Lower Band = `min(lows[-period:])`
     * Middle Band = `(Upper Band + Lower Band) / 2`
   * Provide volume SMAs within `SymbolData`. When checking a breakout, `current_volume > SMA(volume, 20)` helps confirm genuine interest.

2. **BreakoutStrategy Implementation**
   * Inheriting from our standard strategy concepts.
   * **BUY condition:** `current_close >= donchian_upper_band` AND `current_volume > avg_volume * 1.5` (or some configurable threshold).
   * **SELL condition:** Rely on the global ATR Trailing Stop, OR when the price crosses below the `donchian_middle_band`.

## Trade-offs
* **Fakeouts:** Breakouts notoriously fail sometimes. Relying heavily on volume confirmation mitigates this, but cannot eliminate it. Our global ATR trailing stop is crucial to protect against failed breakouts.
