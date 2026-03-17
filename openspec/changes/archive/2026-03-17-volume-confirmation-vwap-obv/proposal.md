# Proposal: Volume Confirmation via VWAP & OBV

## The Problem
Many trading strategies (RSI, Bollinger, MACD) evaluate price movement and momentum, but they can be tricked by low-volume manipulation or temporary illiquidity (fakeouts). A MACD crossover or a Bollinger Band breach without significant trading volume means institutional players aren't behind the move, making it highly susceptible to reversal. 

## The Solution
Introduce **Volume Confirmation Checks** based on two essential indicators:
1. **VWAP (Volume Weighted Average Price):** Indicates the true average price participants paid for an asset over a given timeframe. Price > VWAP suggests true accumulation/bullish control.
2. **OBV (On-Balance Volume):** A cumulative indicator that adds volume on up days and subtracts volume on down days. A rising OBV curve confirms a bullish price trend.

By requiring volume confirmation, the bot will filter out weak signals and only enter trades when the "smart money" is participating.

## High-Level Approach
1. **Core Indicators Update:** Add VWAP and OBV calculation logic to `app/services/indicators.py`.
2. **Data Model Updates:** Expand `SymbolData` to retain VWAP and OBV state across ticks.
3. **Strategy Enforcement:** We can adapt existing strategies (like MACD or Breakout) to optionally require volume confirmation before returning a "BUY" signal, or we can make the `DynamicStrategyProxy` enforce a global VWAP > Price filter for specific market regimes. For maximum flexibility and backward compatibility, we will introduce a global configuration to force VWAP/OBV confirmation on strategy signals inside `DynamicStrategyProxy`.

## Impact
- `app/services/indicators.py`: Need robust accumulators for VWAP and OBV.
- `app/services/strategy_factory.py`: Add an optional global volume filter in `DynamicStrategyProxy.analyze`.
- Extends the `SymbolData` class.
