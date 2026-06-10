---
name: software-architect
description: Software architect expert in VinBot Trading. Use when designing, refactoring, or making architectural decisions for this project.
---

# VinBot Trading Architect

Expert in VinBot Trading architecture, design patterns, and system evolution.

## Project Context

VinBot is an algorithmic trading bot built with FastAPI connecting to Binance. It uses a modular architecture with service-oriented design for trading strategies, risk management, market data, and observability.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI App                             │
│                    (app/main.py - lifespan)                     │
├─────────────────────────────────────────────────────────────────┤
│  API Layer           │  Core Layer        │  Services Layer     │
│  ├── v1/router       │  ├── config        │  ├── binance_client│
│  └── endpoints       │  ├── database      │  ├── trading_engine │
│                      │  ├── observability │  ├── risk_manager   │
│                      │  └── metrics       │  ├── strategy_factory│
│                      │                    │  ├── market_data    │
│                      │                    │  ├── indicators    │
│                      │                    │  ├── notifications │
│                      │                    │  └── persistence   │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Entry Point (app/main.py)
- FastAPI with lifespan context manager
- Background tasks: trading bot, reports, metrics
- WebSocket stream handlers
- Order execution flow

```python
# Flow: WebSocket → dummy_strategy_callback → Risk Check → Strategy → Execute
async def dummy_strategy_callback(data: Dict[str, Any]):
    # 1. Real-time SL/TP/Partial check
    risk_manager.check_sl_tp(symbol, close_price)
    # 2. On kline close: strategy analysis
    strategy_manager.re_evaluate_regime(symbol)
    signal = rsi_strategy.analyze(symbol)
    # 3. Execute order
    trading_engine.place_market_order(symbol, side, quantity)
```

### 2. Strategy Layer (app/services/strategy_factory.py)

**StrategyManager**: Dynamic strategy selection based on market regime
```python
class StrategyManager:
    - rsi_only: RSI-only strategy
    - rsi_divergence: RSI with price divergence
    - bollinger: Bollinger Bands for ranging markets
    - macd_cross: MACD crossovers for trends
    - breakout: Volatility breakout detection

    Auto Mode: Switches strategy based on regime detection
    - TRENDING → MACD Cross (strong) or RSI Divergence (normal)
    - RANGING → Bollinger Bands
    - HIGH_VOLATILITY → RSI Divergence (safer)
```

**DynamicStrategyProxy**: Applies filters before strategy signals
- Trailing stop evaluation
- Volume confirmation (VWAP + OBV)
- BTC directional filter (macro regime)
- Relative strength filter (vs BTC)

### 3. Risk Management (app/services/risk_manager.py)

```python
class RiskManager:
    - Position tracking per symbol
    - Entry price management
    - Stop loss / Take profit
    - Trailing stop (ATR-based)
    - Partial take profit (multi-level)
    - Daily PnL tracking
    - Position sizing (dynamic or fixed)
```

### 4. Market Data (app/services/market_data.py + indicators.py)

```python
class MarketService:
    - WebSocket kline streaming
    - Historical data fetching
    - Symbol data management

class SymbolData:
    - OHLCV data storage
    - Technical indicators: RSI, EMA, ATR, Bollinger, MACD, VWAP, OBV
    - Local extrema for divergence detection
```

### 5. Binance Integration (app/services/binance_client.py)

```python
class BinanceClient:
    - REST API: orders, balance, exchange info
    - WebSocket: stream management
    - Time sync
    - Rate limiting
    - Testnet/Prod switching
```

### 6. Persistence (app/services/persistence.py)

- State recovery after crashes
- Position state persistence
- High watermark persistence

### 7. Observability (app/core/)

- **Prometheus metrics**: RSI, wallet balance, order counts
- **Structured logging**: File + console
- **OpenTelemetry**: Traces via Tempo

## Design Patterns Used

### 1. Singleton Pattern
```python
# Global service instances
binance_client = BinanceClient(...)
risk_manager = RiskManager(...)
strategy_manager = StrategyManager()
```

### 2. Strategy Pattern
```python
# Interchangeable strategies
RSIStrategy(), BollingerBandsStrategy(), MacdMaCrossStrategy()
```

### 3. Proxy Pattern
```python
# DynamicStrategyProxy adds filters before strategy execution
```

### 4. Factory Pattern
```python
# StrategyFactory creates strategy based on config
```

### 5. Observer Pattern
```python
# WebSocket callbacks notify trading engine
```

## Configuration Structure (app/core/config.py)

```python
class Settings:
    # Risk Management
    STOP_LOSS_PCT: float = 2.0
    TAKE_PROFIT_PCT: float = 5.0
    ENABLE_TRAILING_STOP: bool = True
    ATR_TRAILING_MULTIPLIER: float = 3.0

    # Strategy Selection
    TRADING_STRATEGY: str = "RsiOnly"  # Auto | RsiOnly | RsiWithDivergence | BollingerBands | MacdMaCross | Breakout

    # Filters
    ENABLE_BTC_DIRECTIONAL_FILTER: bool = True
    ENABLE_RELATIVE_STRENGTH_FILTER: bool = True
    ENABLE_VOLUME_CONFIRMATION: bool = False
```

## Data Flow

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Binance    │───▶│Market Service│───▶│ Symbol Data  │
│   WebSocket │    │  (stream)    │    │ (indicators) │
└──────────────┘    └──────────────┘    └──────────────┘
                                              │
                                              ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Risk Manager│◀───│   Strategy   │◀───│ Dynamic      │
│  (SL/TP)     │    │  (signals)   │    │ StrategyProxy│
└──────────────┘    └──────────────┘    └──────────────┘
       │
       ▼
┌──────────────┐    ┌──────────────┐
│   Binance    │───▶│   Telegram   │
│   Client     │    │  (alerts)    │
└──────────────┘    └──────────────┘
```

## Extension Points

### Adding New Strategy
1. Create `app/services/<strategy>_strategy.py` implementing `analyze(symbol)` → "BUY"|"SELL"|None
2. Add to `StrategyManager.__init__`
3. Register in regime detection logic
4. Add to `TRADING_STRATEGY` config options

### Adding New Indicator
1. Add method to `SymbolData` in `app/services/indicators.py`
2. Use existing OHLCV data
3. Cache computed values

### Adding New Filter
1. Add to `DynamicStrategyProxy.analyze()`
2. Use config flags for enable/disable

### Adding New Exchange
1. Create `app/services/exchange_client.py` implementing same interface as `BinanceClient`
2. Update config to select exchange
3. Refactor client injection

## Common Refactorings

### Extract Strategy Interface
```python
class TradingStrategy(ABC):
    @abstractmethod
    def analyze(self, symbol: str) -> Optional[str]: pass

    @abstractmethod
    async def update_position(self, symbol: str, in_position: bool): pass
```

### Dependency Injection for Testing
```python
# Instead of global singletons
def __init__(binance_client: BinanceClient, risk_manager: RiskManager):
    self.binance = binance_client
    self.risk = risk_manager
```

### Event-Driven Architecture
```python
class TradingEvents(Enum):
    ORDER_FILLED = "order_filled"
    SL_TRIGGERED = "sl_triggered"
    REGIME_CHANGED = "regime_changed"

# Replace direct calls with event emission
event_bus.publish(TradingEvents.ORDER_FILLED, order_data)
```

## Decisions & Trade-offs

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| Singleton services | Simplicity for stateful trading | Harder to test, global state |
| Sync strategy analyze | Simplicity in callback flow | Blocks event loop in complex calcs |
| In-memory + SQLite | Fast access + persistence | Memory limits on many symbols |
| Config-driven strategies | Flexibility | Complexity in config management |
| WebSocket vs REST | Real-time prices | Reconnection handling |

## Code Organization Guidelines

```
app/
├── main.py                 # Entry point, lifespan, background tasks
├── api/
│   └── v1/
│       ├── router.py       # Route aggregation
│       └── endpoints/      # REST endpoints
├── core/
│   ├── config.py          # Settings (single source of truth)
│   ├── database.py        # DB connection
│   ├── observability.py   # OTLP setup
│   └── metrics.py         # Prometheus metrics
└── services/
    ├── binance_client.py   # Exchange API
    ├── trading_engine.py   # Order execution
    ├── risk_manager.py     # Position & risk
    ├── strategy_factory.py# Strategy orchestration
    ├── regime_service.py   # Market regime detection
    ├── indicators.py      # Technical indicators
    ├── market_data.py     # WebSocket streaming
    ├── persistence.py     # State recovery
    └── notifications.py   # Telegram alerts
```

## Testing Strategy

- **Unit**: Strategy logic, indicators, risk calculations
- **Integration**: Binance client, persistence, state recovery
- **Paper Trading**: Full flow with testnet

## When Making Architectural Decisions

1. Consider state management complexity
2. Prioritize observability for debugging live trades
3. Keep config-driven for strategy flexibility
4. Maintain clear boundaries between strategy and execution
5. Ensure state persistence for crash recovery

## This is VinBot-specific

Use this skill when:
- Adding new strategies or indicators
- Refactoring trading flow
- Adding new exchanges
- Designing risk management features
- Planning observability improvements
- Making configuration changes
- Debugging trading issues