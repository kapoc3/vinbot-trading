# Backtest Engine

## Purpose

Motor de ejecución de estrategias contra datos históricos con simulación de trading.

## ADDED Requirements

### Requirement: Backtest Execution

El sistema SHALL ejecutar una estrategia contra datos históricos y retornar lista de trades ejecutados.

#### Scenario: Successful backtest run

- **WHEN** se ejecuta backtest con estrategia RSI, símbolo BTCUSDT, datos históricos de 1 año
- **THEN** el sistema retorna lista de trades con: entry_time, exit_time, entry_price, exit_price, side, pnl, quantity

#### Scenario: Insufficient data

- **WHEN** los datos históricos tienen menos de 100 candles
- **THEN** el sistema lanza excepción indicando datos insuficientes

### Requirement: Strategy Interface

El sistema SHALL soportar cualquier estrategia que implemente la interfaz: analyze(symbol, data) -> "BUY"|"SELL"|None.

#### Scenario: Using existing strategy

- **WHEN** se pasa RSIStrategy al backtest
- **THEN** el engine ejecuta el método analyze de la estrategia para cada candle

#### Scenario: Multiple strategies

- **WHEN** se ejecutan múltiples estrategias en el mismo backtest
- **THEN** cada estrategia se ejecuta independientemente con su propio estado

### Requirement: Trade Simulation

El sistema SHALL simular la ejecución de órdenes con los siguientes comportamientos:

#### Scenario: Market order simulation

- **WHEN** la estrategia genera señal BUY/SELL
- **THEN** el trade se ejecuta al close price del candle actual

#### Scenario: Slippage application

- **WHEN** se ejecuta un trade
- **THEN** se aplica slippage configurable (default 0.1% para majors, 0.2% para alts)
- **AND** el precio de ejecución = precio mercado * (1 + slippage) para buy, (1 - slippage) para sell

#### Scenario: Commission deduction

- **WHEN** se ejecuta un trade
- **THEN** se deduce comisión (default 0.1% para Binance) del PnL

### Requirement: Position Tracking

El sistema SHALL mantener tracking de posiciones durante el backtest igual que en producción.

#### Scenario: Long position

- **WHEN** signal es BUY y no hay posición
- **THEN** se abre posición larga al precio actual

#### Scenario: Position close

- **WHEN** signal es SELL y hay posición abierta
- **THEN** se cierra posición al precio actual

#### Scenario: Multiple signals in same candle

- **WHEN** múltiples señales se generan en el mismo candle
- **THEN** solo se considera la primera señal del candle

### Requirement: Cash and Capital Simulation

El sistema SHALL simular gestión de capital con las siguientes reglas:

#### Scenario: Initial capital

- **WHEN** inicia el backtest
- **THEN** el capital inicial se establece en ALLOCATED_CAPITAL (default $1000)

#### Scenario: Position sizing

- **WHEN** se abre posición
- **THEN** el tamaño se calcula usando RISK_PER_TRADE_PCT y STOP_LOSS_PCT

#### Scenario: Insufficient capital

- **WHEN** el capital disponible es menor al tamaño mínimo requerido
- **THEN** el sistema salta el trade y logged warning

## Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| BACKTEST_INITIAL_CAPITAL | float | 1000.0 | Capital inicial |
| BACKTEST_SLIPPAGE_MAJORS | float | 0.001 | Slippage para majors (0.1%) |
| BACKTEST_SLIPPAGE_ALTS | float | 0.002 | Slippage para alts (0.2%) |
| BACKTEST_COMMISSION | float | 0.001 | Comisión (0.1%) |