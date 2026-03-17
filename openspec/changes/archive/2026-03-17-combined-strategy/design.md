## Context

The current `VinBot` application relies on a single strategy (`RSIStrategy`) directly reading the RSI value to determine overbought or oversold conditions. A common issue with pure RSI logic is the generation of false signals during strong, prolonged trends where the RSI remains oversold/overbought for long periods. To improve entry confidence, we are implementing a "Combined Strategy" approach, specifically adding an **RSI Divergence Strategy**. This requires mathematical logic to track local price extrema (swing highs/lows) and compare them with corresponding RSI extrema.

## Goals / Non-Goals

**Goals:**
- Implement a math-driven algorithm to find local swing highs and lows for the asset's close prices and the RSI.
- Develop a strategy (`RsiDivergenceStrategy`) that evaluates these points to confirm regular bullish/bearish divergences.
- Abstract the `main.py` strategy loop so it can interchangeably use either the basic `RSIStrategy` or the new `RsiDivergenceStrategy` using an environment variable, like `TRADING_STRATEGY=RsiDivergence`.

**Non-Goals:**
- Building a UI to visualize the divergences.
- Implementing hidden/exaggerated divergences (only focusing on Regular / Classic divergences).
- Refactoring the entire `risk_manager.py` or the `binance_client.py` - the changes will be strictly focused on the indicator and strategy layers.

## Decisions

**Decision 1: Swing Detection Algorithm**
*   **Rationale:** We need to keep track of local extrema. We will use a "window-based" approach. By looking back *N* candles and forward *N* candles from a specific point, we can determine if it is a local high or low.
*   **Alternatives:** Moving Average crossovers (too lagging), ZigZag (prone to repainting).
*   **Implementation:** `TechnicalIndicators` will gain a new static method: `find_divergence(prices, rsis, pivot_length=5)`.

**Decision 2: Strategy Interface Abstraction**
*   **Rationale:** The main loop currently hardcodes the `RSIStrategy`. We need an easy way to swap strategies without rewriting the loop.
*   **Alternatives:** Passing a strategy object around or instantiating different main loops.
*   **Implementation:** A simple factory pattern or Strategy map driven by the `.env` file (via `config.py`) will determine which strategy class is instantiated at startup.

## Risks / Trade-offs

- **Risk**: Finding swing points inherently introduces lag. A "swing low" is only confirmed *after* prices go back up for a few candles. Thus, the divergence signal will fire slightly later than a raw RSI signal.
  - **Mitigation**: Keep the "pivot / lookback window" small (e.g., 3-5 candles) to confirm swings as fast as computationally possible without triggering on mere noise.

- **Risk**: `SymbolData` deque length. The current `max_history` is 100.
  - **Mitigation**: Ensure `max_history` is sufficient to look back far enough to find at least 2 or 3 swing points. 100 1m candles (=1h:40m) should be enough, but if divergence is sought over longer horizons, this might need an increase.
