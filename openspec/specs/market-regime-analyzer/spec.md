# Capability: Market Regime Analyzer

## Requirements
- The system SHALL calculate the ADX (Average Directional Index) to determine trend strength.
- The system SHALL calculate the ATR (Average True Range) to monitor market volatility.
- The system MUST classify the market into three states: `Trending` (ADX > 25), `Ranging` (ADX < 20), and `HighVolatility`.
- The system MUST implement hysteresis to prevent frequent strategy switching (flapping) when ADX is between 20 and 25.
