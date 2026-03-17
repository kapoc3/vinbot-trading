## Context

Trending markets require a strong filter to ensure the bot is trading in the direction of the dominant move. The RSI Divergence is a "leader" indicator, but can "fake out" in vertical trends. A MACD + MA Cross strategy is a "lagging" but "confirming" system, which is safer for sustained trends.

## Goals / Non-Goals

**Goals:**
- Implement recursive EMA (Exponential Moving Average) calculation.
- Implement MACD (12, 26, 9) calculation.
- Design `MacdMaCrossStrategy` with an EMA 200 trend filter.

**Non-Goals:**
- Implementing a histogram-based divergence yet (only signal crossovers for now).
- Changing risk management parameters specifically for this strategy.

## Decisions

- **EMA Implementation**: We will use the formula `EMA_today = (Price_today * (2 / (N + 1))) + EMA_yesterday * (1 - (2 / (N + 1)))`. For the first value, we will use the SMA of the first N periods.
- **Trend Filter**: The strategy will only allow BUY signals if the current price is above the EMA 200 (Long-term Bullish Trend).
- **Entry Trigger**: MACD line crossing above the Signal line.
- **Exit Trigger**: MACD line crossing below the Signal line or price breaking below a trailing stop (leveraged from existing risk manager).
- **Strategy Selection in Auto Mode**: This strategy will be considered the "Heavy Trend" strategy, possibly running alongside or replacing RSI Divergence when ADX is extremely high (>40).

## Risks / Trade-offs

- **Risk: Late Entries**: As a lagging indicator system, entries will occur after the trend has already started.
  - **Mitigation**: This is acceptable for trend-following; it prioritizes "getting the meat" of the move rather than catching the exact bottom.
- **Trade-off: Historical Data Requirements**: EMA 200 requires at least 200-300 data points to stabilize.
  - **Mitigation**: We must ensure `SymbolData.maxlen` and initial kline loading are sufficient (e.g., 500 klines) when this strategy is active.
