# Indicator Aggregation

## Purpose

Cálculo unificado de indicadores técnicos a través de todos los timeframes configurados.

## ADDED Requirements

### Requirement: Multi-Timeframe Indicator Calculation

El sistema SHALL calcular indicadores (RSI, EMA, ADX) para cada timeframe activo.

#### Scenario: Calculate RSI for all timeframes

- **WHEN** se llama get_all_rsi(symbol)
- **THEN** retorna diccionario {timeframe: rsi_value} para todos los timeframes activos

#### Scenario: Calculate EMA for all timeframes

- **WHEN** se llama get_all_ema(symbol, period)
- **AND** period = 20 (default)
- **THEN** retorna diccionario {timeframe: ema_value}

### Requirement: Trend Direction per Timeframe

El sistema SHALL determinar la dirección de tendencia por timeframe.

#### Scenario: Uptrend

- **WHEN** precio actual > EMA 20 en timeframe X
- **THEN** trend_direction[X] = "UP"

#### Scenario: Downtrend

- **WHEN** precio actual < EMA 20 en timeframe X
- **THEN** trend_direction[X] = "DOWN"

#### Scenario: Ranging

- **WHEN** precio está dentro de 0.5% de EMA 20
- **THEN** trend_direction[X] = "RANGING"

### Requirement: Cross-Timeframe Analysis

El sistema SHALL identificar cuando todos los timeframes están alineados.

#### Scenario: All aligned bullish

- **WHEN** trend_direction es UP en 1m, 15m, Y 1h
- **THEN** alignment = "STRONG_BULLISH"

#### Scenario: Mixed signals

- **WHEN** 1m=UP, 15m=UP, 1h=DOWN
- **THEN** alignment = "MIXED" (precaución)

#### Scenario: All aligned bearish

- **WHEN** trend_direction es DOWN en todos
- **THEN** alignment = "STRONG_BEARISH"

### Requirement: Indicator Data Export

El sistema SHALL exportar estado de indicadores por timeframe para debugging.

#### Scenario: Export state

- **WHEN** se llama get_indicators_state(symbol)
- **THEN** retorna estructura con:
  - timestamp
  - por cada timeframe: price, rsi, ema_20, adx, trend_direction
  - overall_alignment