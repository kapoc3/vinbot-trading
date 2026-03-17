## Context
The bot currently uses the `RSIStrategy` during ranging market conditions (when `MarketRegime` is `RANGING`). While RSI is effective at identifying overbought/oversold levels, it does not account for market volatility. By introducing Bollinger Bands, we can define dynamic support and resistance channels and pair this indicator with RSI to confirm stronger reversal signals in a ranging market. 

## Goals / Non-Goals

**Goals:**
- Implement Bollinger Bands calculation (SMA 20, StdDev 2) efficiently within the indicator toolkit.
- Create a new combination strategy: `BollingerBandsStrategy` that operates primarily during ranging conditions.
- Replace or enhance `RSIStrategy` as the default `Auto` mode strategy for ranging markets.
- Ensure indicator state (running means and variances) is managed accurately without causing memory bloat across the dataset.

**Non-Goals:**
- Changing the primary Trend-following mechanism (`RsiDivergenceStrategy`).
- Adding configuration parameters for Bollinger Band periods and deviations in this iteration (we will hardcode standard 20, 2 values initially to simplify integration, or use class-level constants).

## Decisions

- **Indicator State Management**: To compute standard deviation efficiently inline, we will apply Welford's online algorithm or simply rely on the history sliding window (`deque`) to recalculate standard deviation on the last `20` prices. Given `max_history` is capped (e.g., 200), using `statistics.stdev` on the recent window is sufficiently fast and guarantees correctness without float-drift issues associated with running aggregations.
- **Entry Logic Integration**: The strategy will mandate:
  - Last close crossing under the Lower Bollinger Band.
  - RSI < 30 (Oversold).
  This combined condition yields fewer but higher-probability trades.
- **Auto Mode Replacement**: `BollingerBandsStrategy` will replace the `RSIStrategy` as the active strategy deployed when the `RegimeService` detects a `Ranging` regime.

## Risks / Trade-offs

- **Risk: Whipsaw in High Volatility**: In periods of sudden volatility expansion, Bollinger Bands will widen, potentially trapping the bot in a trade before the system re-classifies the regime to `Trending`. 
  - **Mitigation**: The `RegimeService` already incorporates ATR-based HighVolatility checks to pause entries or force a switch if the market aggressively breaks out.
- **Trade-off: Missed Entries**: The strict requirement of both RSI < 30 and Price < Lower Band might result in fewer filled trades.
  - **Rationale**: In automated trading, capital preservation targets higher Expected Value per trade rather than high trade frequency.
