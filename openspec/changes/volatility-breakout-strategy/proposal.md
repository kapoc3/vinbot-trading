# Proposal: Volatility Breakout Strategy (Donchian Channels)

## The Problem
While our existing strategies are effective during ranging markets (Bollinger Bands) and established trend phases (MACD, RSI Divergence), we lack a strategy specifically designed to capture the **initial breakout explosive move**. When a prolonged period of low volatility finishes, the price typically "bursts" through a support or resistance level, signaling the start of a strong trend. Trend-following indicators like MACD or EMA crossovers often lag during this initial burst.

## The Solution
Implement a **Volatility Breakout Strategy** based on the **Donchian Channel**, paired with a **Volume Confirmation** filter.
The Donchian Channel tracks the highest high and lowest low over a lookback period (e.g., 20 periods). 
* When the price strongly breaks above the upper channel (Highest High of the last 20 periods) and volume is higher than the average, we trigger a BUY signal.
* Given our new dynamic ATR trailing stop handles risk globally, we won't reinvent exits here; we will rely on a simple reversion exit or the trailing stop for protection.

## High-Level Approach
1. **Indicator Addition:** Add `calculate_donchian_channel` (Upper Band, Lower Band, Middle Band) to the `TechnicalIndicators` module. Add volume average calculation to `SymbolData`.
2. **Strategy Creation:** Create a new `BreakoutStrategy` class that implements the standard `analyze` interface.
3. **Integration:** Hook the new strategy into `StrategyManager` and allow it to be selected.
