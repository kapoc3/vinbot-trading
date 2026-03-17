## Context

The trading bot currently supports manual selection between multiple strategies (RSI, RSI+Divergence). However, each is best suited for different market "regimes" (Trending vs Ranging). This change implements the infrastructure for the bot to automatically detect these regimes and switch its strategy accordingly.

## Goals / Non-Goals

**Goals:**
- Implement a **Regime Classification Engine** using ADX (Average Directional Index) for trend strength and ATR (Average True Range) for volatility.
- Define specific market states: `TRENDING_UP`, `TRENDING_DOWN`, `RANGING`, `HIGH_VOLATILITY`.
- Create a **Dynamic Strategy Manager** that can replace the active strategy instance without restarting the application.
- Visualize the current regime state in the logs and eventually through Prometheus metrics.

**Non-Goals:**
- Integrating advanced Machine Learning or neural networks for regime classification (keeping it math/indicator-based).
- Implementing more than the existing strategies for now (just enabling the *choice* between them).
- Redesigning the entire `main.py` loop - the refactoring should remain focused on the strategy selection logic.

## Decisions

**Decision 1: Use ADX as Primary Trend Strength Indicator**
- **Rationale:** ADX is the industry standard for determining if a market is trending (>25) or ranging (<20) without focusing on direction. It prevents "choppiness" in signal processing.
- **Alternatives:** Simple Moving Average slope (too noisy), standard deviation (only measures dispersion).

**Decision 2: Re-evaluation Frequency (Periodic vs Tick-by-tick)**
- **Rationale:** To avoid a "Whipsaw" effect (rapidly switching strategies back and forth), the bot will evaluate the regime only at the close of a kline (1m or 5m interval) rather than on every price update.
- **Implementation:** The check will be triggered inside the `if is_closed:` block in the kline callback.

## Risks / Trade-offs

- **Risk: Strategy Delay** → A regime change might only be detected after it's partly over.
  - **Mitigation:** Use smaller lookback windows for the regime counters (e.g., ADX 14) to balance sensitivity and stability.
  - **Risk: Signal Conflict** → Switching strategies while a position is already open.
  - **Mitigation:** The bot will "lock" the strategy for a specific symbol if a position is currently open, ensuring the exit logic remains consistent with the entry logic. Once closed, the next trade can use the newly chosen strategy.
