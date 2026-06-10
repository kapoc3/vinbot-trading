# Multi-Timeframe Data Management

## Purpose

Sistema de gestión de datos históricos y en tiempo real para múltiples timeframes.

## ADDED Requirements

### Requirement: Multi-Timeframe Data Fetch

El sistema SHALL obtener datos históricos de múltiples timeframes en paralelo al inicio.

#### Scenario: Fetch multiple timeframes

- **WHEN** se llama fetch_all_timeframes(symbol, [1m, 5m, 15m, 1h])
- **THEN** el sistema descarga datos para cada timeframe en paralelo
- **AND** retorna diccionario con datos por timeframe

#### Scenario: Partial data available

- **WHEN** algunos timeframes tienen errores
- **THEN** el sistema retorna los datos disponibles con warning

### Requirement: Real-time Data Update

El sistema SHALL actualizar datos de todos los timeframes cuando llega un nuevo candle.

#### Scenario: Update on new candle

- **WHEN** llega un nuevo candle en timeframe 1m
- **THEN** el sistema actualiza datos de 1m Y verifica si necesita actualizar timeframes superiores

#### Scenario: Timeframe sync

- **WHEN** el último candle de 15m es más antiguo que el de 1m por más de 15 minutos
- **THEN** el sistema fuerza fetch de datos de 15m

### Requirement: Data Buffer Management

El sistema SHALL mantener un buffer limitado de candles por timeframe para controlar uso de memoria.

#### Scenario: Buffer limit

- **WHEN** el buffer de un timeframe supera MAX_CANDLES (default 500)
- **THEN** el sistema elimina los datos más antiguos

#### Scenario: Data cleanup on symbol removal

- **WHEN** se deja de monitorear un símbolo
- **THEN** el sistema limpia todos los datos de ese símbolo en todos los timeframes

## Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| MULTI_TF_ENABLED | bool | True | Enable multi-timeframe |
| ACTIVE_TIMEFRAMES | str | "1m,15m,1h" | Timeframes a monitorear |
| MAX_CANDLES_PER_TF | int | 500 | Buffer size per timeframe |