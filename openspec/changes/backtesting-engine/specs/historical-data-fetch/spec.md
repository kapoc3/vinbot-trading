# Historical Data Fetch

## Purpose

Sistema de descarga y gestión de datos históricos de Binance para backtesting.

## ADDED Requirements

### Requirement: Fetch Historical Klines

El sistema SHALL descargar datos históricos de klines (candles) de la API de Binance para un símbolo, timeframe y rango de fechas específico.

#### Scenario: Fetch successful

- **WHEN** se llama a fetch_historical_klines(symbol="BTCUSDT", timeframe="1h", start_date="2024-01-01", end_date="2024-12-31")
- **THEN** el sistema retorna una lista de klines con campos: open_time, open, high, low, close, volume, close_time

#### Scenario: Network error

- **WHEN** la API de Binance retorna error de red
- **THEN** el sistema lanza excepción con mensaje descriptivo y permite retry

#### Scenario: Rate limit

- **WHEN** Binance retorna 429 (Too Many Requests)
- **THEN** el sistema espera el tiempo especificado en el header Retry-After y reintenta

### Requirement: Data Caching

El sistema SHALL guardar los datos descargados en cache local para evitar descargas repetidas.

#### Scenario: Cache hit

- **WHEN** se solicita datos que ya existen en cache (mismo símbolo, timeframe, rango)
- **THEN** el sistema retorna datos desde cache sin llamar a API

#### Scenario: Cache miss

- **WHEN** los datos no existen en cache
- **THEN** el sistema descarga de Binance y guarda en cache

### Requirement: Cache Storage Format

El sistema SHALL almacenar datos en formato CSV en directorio configurable (default: data/backtest_cache/).

#### Scenario: Cache file format

- **WHEN** se guarda un cache de klines
- **THEN** el archivo se guarda como {symbol}_{timeframe}_{start}_{end}.csv con headers: timestamp,open,high,low,close,volume

### Requirement: Multiple Timeframes Support

El sistema SHALL soportar múltiples timeframes: 1m, 5m, 15m, 1h, 4h, 1d.

#### Scenario: Different timeframes

- **WHEN** se solicita timeframe válido (1m, 5m, 15m, 1h, 4h, 1d)
- **THEN** el sistema retorna datos en el timeframe solicitado

#### Scenario: Invalid timeframe

- **WHEN** se solicita timeframe no válido
- **THEN** el sistema lanza excepción con error clear

## Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| BACKTEST_CACHE_DIR | str | "data/backtest_cache" | Directorio para cache |
| MAX_KLINES_PER_REQUEST | int | 1000 | Máx candles por request |
| CACHE_ENABLED | bool | True | Habilitar cache |