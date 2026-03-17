# Proposal: Relative Strength Filter against Bitcoin

## The Problem
In cryptocurrency markets, the vast majority of altcoins are highly correlated with Bitcoin. However, the magnitude of their moves varies wildly. When a technical strategy fires a "BUY" signal for an altcoin, it may just be "floating up" slowly because Bitcoin is rising, rather than displaying independent bullish momentum. Buying weak or lagging assets ties up capital that could be deployed into the market's true leaders, reducing the overall profitability and capital efficiency of the trading system.

## The Solution
Implement a **Relative Strength (RS) Filter**. Before executing an altcoin "BUY" signal, the bot will compare the altcoin's recent price action against Bitcoin's recent price action. We will calculate a synthetic RS metric (e.g., the Rate of Change of the Altcoin vs. the Rate of Change of Bitcoin over a specific lookback period). 
If the altcoin is underperforming Bitcoin (RS < 1 or ROC ratio < 0), the signal is vetoed.

## Core Benefits
- **Capital Efficiency:** Ensures the bot only purchases assets that are outperforming the market benchmark, avoiding "laggards."
- **Win Rate Optimization:** Altcoins showing relative strength often have underlying narrative or fundamental catalysts, granting them stronger follow-through on technical breakouts.
- **Risk Mitigation:** If Bitcoin is rising and an altcoin is flat, the altcoin is fundamentally weak. If Bitcoin eventually dips, that weak altcoin will likely crash disproportionately. The RS filter prevents entry into these fragile assets.
