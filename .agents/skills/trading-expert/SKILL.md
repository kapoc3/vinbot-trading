---
name: trading-expert
description: Trading and financial markets expert. Use when working on trading bots, technical analysis, trading strategies, or financial algorithms.
---

# Trading Expert

Expert in algorithmic trading, technical analysis, risk management, and financial markets.

## When to Use This Skill

- Building trading bots or algorithms
- Implementing technical indicators
- Designing trading strategies
- Risk management systems
- Backtesting and strategy evaluation
- Exchange API integration (Binance, etc.)

## Core Concepts

### Technical Indicators

**RSI (Relative Strength Index)**
```python
def calculate_rsi(prices: list[float], period: int = 14) -> float:
    """Calculate RSI indicator."""
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
```

**Moving Averages (SMA/EMA)**
```python
def calculate_sma(prices: list[float], period: int) -> float:
    """Simple Moving Average."""
    if len(prices) < period:
        return 0
    return sum(prices[-period:]) / period

def calculate_ema(prices: list[float], period: int) -> float:
    """Exponential Moving Average."""
    if len(prices) < period:
        return 0
    multiplier = 2 / (period + 1)
    ema = prices[0]
    for price in prices[1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
    return ema
```

**Bollinger Bands**
```python
def bollinger_bands(prices: list[float], period: int = 20, std_dev: float = 2.0):
    """Calculate Bollinger Bands."""
    sma = calculate_sma(prices, period)
    variance = sum((p - sma) ** 2 for p in prices[-period:]) / period
    std = variance ** 0.5
    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)
    return {'upper': upper, 'middle': sma, 'lower': lower}
```

**ATR (Average True Range)**
```python
def calculate_atr(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> float:
    """Calculate Average True Range for volatility."""
    true_ranges = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i-1]),
            abs(lows[i] - closes[i-1])
        )
        true_ranges.append(tr)

    if len(true_ranges) < period:
        return 0
    return sum(true_ranges[-period:]) / period
```

**MACD**
```python
def calculate_macd(prices: list[float], fast: int = 12, slow: int = 26, signal: int = 9):
    """Calculate MACD indicator."""
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    macd_line = ema_fast - ema_slow

    macd_values = []
    for i in range(slow, len(prices)):
        ema_f = calculate_ema(prices[:i+1], fast)
        ema_s = calculate_ema(prices[:i+1], slow)
        macd_values.append(ema_f - ema_s)

    signal_line = calculate_ema(macd_values, signal) if len(macd_values) >= signal else 0
    histogram = macd_line - signal_line

    return {'macd': macd_line, 'signal': signal_line, 'histogram': histogram}
```

### Trading Strategies

**RSI Strategy**
```python
from dataclasses import dataclass
from typing import Literal

Signal = Literal['BUY', 'SELL', 'HOLD']

@dataclass
class TradingSignal:
    action: Signal
    price: float
    rsi: float
    reason: str

def rsi_strategy(prices: list[float], oversold: float = 30, overbought: float = 70) -> TradingSignal:
    """RSI-based trading strategy."""
    rsi = calculate_rsi(prices)

    if rsi < oversold:
        return TradingSignal('BUY', prices[-1], rsi, f"RSI oversold ({rsi:.2f})")
    elif rsi > overbought:
        return TradingSignal('SELL', prices[-1], rsi, f"RSI overbought ({rsi:.2f})")
    return TradingSignal('HOLD', prices[-1], rsi, f"RSI neutral ({rsi:.2f})")
```

**Bollinger Bands Strategy**
```python
def bollinger_strategy(prices: list[float]) -> TradingSignal:
    """Bollinger Bands mean reversion strategy."""
    bb = bollinger_bands(prices)
    current = prices[-1]

    if current < bb['lower']:
        return TradingSignal('BUY', current, 0, f"Price below lower band ({bb['lower']:.2f})")
    elif current > bb['upper']:
        return TradingSignal('SELL', current, 0, f"Price above upper band ({bb['upper']:.2f})")
    return TradingSignal('HOLD', current, 0, "Price within bands")
```

**MACD Crossover Strategy**
```python
def macd_crossover(prices: list[float]) -> TradingSignal:
    """MACD signal line crossover strategy."""
    macd = calculate_macd(prices)

    if macd['macd'] > macd['signal']:
        return TradingSignal('BUY', prices[-1], macd['macd'], "MACD crossed above signal")
    elif macd['macd'] < macd['signal']:
        return TradingSignal('SELL', prices[-1], macd['macd'], "MACD crossed below signal")
    return TradingSignal('HOLD', prices[-1], macd['macd'], "MACD no crossover")
```

### Market Regime Detection

```python
from enum import Enum

class MarketRegime(Enum):
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"

def detect_regime(prices: list[float], atr_threshold: float = 0.02) -> MarketRegime:
    """Detect market regime using ADX and ATR."""
    atr = calculate_atr(prices, prices, prices)
    atr_percent = atr / prices[-1]

    if atr_percent > atr_threshold:
        return MarketRegime.HIGH_VOLATILITY

    ema_fast = calculate_ema(prices, 9)
    ema_slow = calculate_ema(prices, 21)

    if ema_fast > ema_slow * 1.02:
        return MarketRegime.TRENDING_UP
    elif ema_fast < ema_slow * 0.98:
        return MarketRegime.TRENDING_DOWN
    return MarketRegime.RANGING
```

### Risk Management

**Position Sizing**
```python
def calculate_position_size(
    account_balance: float,
    risk_percent: float,
    entry_price: float,
    stop_loss: float
) -> float:
    """Calculate position size based on risk."""
    risk_amount = account_balance * (risk_percent / 100)
    risk_per_share = abs(entry_price - stop_loss)
    if risk_per_share == 0:
        return 0
    return risk_amount / risk_per_share

def calculate_stop_loss(entry: float, atr: float, multiplier: float = 2.0) -> float:
    """Calculate ATR-based stop loss."""
    return entry - (atr * multiplier)

def calculate_take_profit(entry: float, stop_loss: float, rr_ratio: float = 2.0) -> float:
    """Calculate take profit based on risk-reward ratio."""
    risk = abs(entry - stop_loss)
    return entry + (risk * rr_ratio)
```

**Trailing Stop**
```python
class TrailingStop:
    def __init__(self, atr_multiplier: float = 3.0):
        self.atr_multiplier = atr_multiplier
        self.highest = 0
        self.stop = 0
        self.active = False

    def update(self, price: float, atr: float):
        """Update trailing stop."""
        if not self.active:
            self.highest = price
            self.stop = price - (atr * self.atr_multiplier)
            self.active = True
        else:
            if price > self.highest:
                self.highest = price
                self.stop = price - (atr * self.atr_multiplier)

    def should_trigger(self, price: float) -> bool:
        """Check if trailing stop is triggered."""
        return self.active and price <= self.stop
```

### Backtesting

```python
from dataclasses import dataclass
from typing import List

@dataclass
class Trade:
    entry_price: float
    exit_price: float
    quantity: float
    side: Literal['LONG', 'SHORT']
    pnl: float

@dataclass
class BacktestResult:
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    max_drawdown: float

def run_backtest(
    prices: list[float],
    strategy_fn,
    initial_capital: float = 10000
) -> BacktestResult:
    """Simple backtest engine."""
    trades: List[Trade] = []
    capital = initial_capital
    position = None

    for i in range(20, len(prices)):
        signal = strategy_fn(prices[:i+1])

        if signal.action == 'BUY' and position is None:
            position = {'entry': prices[i], 'size': capital / prices[i]}
        elif signal.action == 'SELL' and position:
            pnl = (prices[i] - position['entry']) * position['size']
            capital += pnl
            trades.append(Trade(
                position['entry'], prices[i], position['size'], 'LONG', pnl
            ))
            position = None

    winning = len([t for t in trades if t.pnl > 0])
    return BacktestResult(
        total_trades=len(trades),
        winning_trades=winning,
        losing_trades=len(trades) - winning,
        win_rate=winning / len(trades) if trades else 0,
        total_pnl=capital - initial_capital,
        max_drawdown=0
    )
```

### Exchange Integration (Binance)

```python
import aiohttp
import hashlib
import time
from typing import Optional

class BinanceClient:
    def __init__(self, api_key: str, secret_key: str, testnet: bool = True):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://testnet.binance.vision/api" if testnet else "https://api.binance.com"
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    def _sign(self, params: str) -> str:
        return hmac.new(
            self.secret_key.encode(),
            params.encode(),
            hashlib.sha256
        ).hexdigest()

    async def place_order(self, symbol: str, side: str, quantity: float) -> dict:
        """Place market order."""
        timestamp = int(time.time() * 1000)
        params = f"symbol={symbol}&side={side}&type=MARKET&quantity={quantity}&timestamp={timestamp}"
        signature = self._sign(params)

        url = f"{self.base_url}/v3/order?"
        headers = {"X-MBX-APIKEY": self.api_key}

        async with self.session.post(url + params + f"&signature={signature}", headers=headers) as resp:
            return await resp.json()

    async def get_balance(self, asset: str) -> float:
        """Get account balance."""
        timestamp = int(time.time() * 1000)
        params = f"timestamp={timestamp}"
        signature = self._sign(params)

        url = f"{self.base_url}/v3/account?{params}&signature={signature}"
        headers = {"X-MBX-APIKEY": self.api_key}

        async with self.session.get(url, headers=headers) as resp:
            data = await resp.json()
            return float([b for b in data['balances'] if b['asset'] == asset][0]['free'])
```

### Order Types

```python
from enum import Enum
from dataclasses import dataclass

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"

class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

@dataclass
class Order:
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None

def create_stop_loss_order(entry: float, stop_percent: float = 0.02) -> Order:
    """Create stop loss order."""
    return Order(
        symbol="BTCUSDT",
        side=OrderSide.SELL,
        order_type=OrderType.STOP_LOSS,
        quantity=0,
        stop_price=entry * (1 - stop_percent)
    )
```

## Strategy Patterns

**Dynamic Strategy Selection**
```python
class StrategySelector:
    def __init__(self):
        self.strategies = {
            'trending_up': rsi_divergence_strategy,
            'trending_down': macd_crossover,
            'ranging': bollinger_strategy,
            'high_volatility': volatility_breakout
        }

    def select(self, regime: MarketRegime):
        return self.strategies.get(regime, rsi_strategy)
```

**Signal Aggregation**
```python
def aggregate_signals(signals: List[TradingSignal]) -> TradingSignal:
    """Combine multiple strategy signals."""
    buy_count = sum(1 for s in signals if s.action == 'BUY')
    sell_count = sum(1 for s in signals if s.action == 'SELL')

    if buy_count > sell_count:
        return TradingSignal('BUY', signals[-1].price, 0, f"Consensus: {buy_count} BUY signals")
    elif sell_count > buy_count:
        return TradingSignal('SELL', signals[-1].price, 0, f"Consensus: {sell_count} SELL signals")
    return TradingSignal('HOLD', signals[-1].price, 0, "No consensus")
```

## Key Metrics

| Metric | Description |
|--------|-------------|
| Sharpe Ratio | Risk-adjusted return |
| Max Drawdown | Largest peak-to-trough |
| Win Rate | Percentage of profitable trades |
| Profit Factor | Gross profit / gross loss |
| expectancy | Average trade PnL |

## Best Practices

1. **Always use stop loss** - Protect capital
2. **Position sizing** - Never risk more than 1-2% per trade
3. **Diversify** - Multiple strategies/timeframes
4. **Backtest** - Verify strategy before live trading
5. **Paper trade** - Test in real environment first
6. **Risk-reward** - Minimum 2:1 ratio
7. **Log everything** - Track decisions and outcomes

## When Helping

- Ask about the exchange and trading pair
- Check existing strategy implementations
- Consider market conditions and regime
- Prioritize risk management in recommendations