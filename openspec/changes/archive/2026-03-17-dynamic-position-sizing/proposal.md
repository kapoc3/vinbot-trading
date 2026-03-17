# Proposal: Risk-Based Dynamic Position Sizing

## The Problem
Currently, the bot executes trades with hardcoded, static quantities (e.g., `0.01` for BTC pairs, `0.1` for everything else). This is highly inefficient and dangerous. A static size completely ignores the varying volatility of different assets and market conditions. A trade with a 2% stop-loss has wildly different nominal risk than a trade with a 10% stop-loss if the position size remains identical.

## The Solution
Implement **Dynamic Position Sizing (Risk-Based Sizing)**. The bot will calculate the exact quantity to purchase based on:
1.  **Account Balance:** How much capital is available (or arbitrarily allocated).
2.  **Risk Percentage:** What percentage of total capital we are willing to lose per trade (e.g., 1%).
3.  **Stop-Loss Distance:** The nominal distance between the entry price and the initial stop-loss price.

**Formula:**
`Risk Amount = Account Balance * Risk %`
`Position Size = Risk Amount / (Entry Price - Stop Loss Price)`

## Core Benefits
- **Risk Normalization:** Every setup, regardless of asset or volatility, carries exactly the same defined monetary risk for the portfolio (e.g., -$20 max loss).
- **Compounding:** As the account balance grows from successful trades, the absolute profits automatically scale up if we switch from allocated capital to real query balance later.
- **Capital Efficiency:** Eliminates "guesswork" sizes that either under-utilize free cash or over-leverage the account.
