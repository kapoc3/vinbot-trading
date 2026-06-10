# ML Feature Engineering

## Purpose

Extracción de features técnicos para entrenamiento y predicción de modelos ML.

## ADDED Requirements

### Requirement: Feature Extraction

El sistema SHALL extraer features técnicos de datos históricos.

#### Scenario: Extract features from klines

- **WHEN** se llama extract_features(klines)
- **THEN** retorna DataFrame con 20 features por candle

#### Scenario: Feature list

- **THEN** features incluyen:
  - rsi_7, rsi_14, rsi_21
  - ema_9, ema_21, ema_50
  - macd_line, macd_signal, macd_hist
  - bb_position (precio relativo a bandas)
  - atr_normalized
  - volume_ratio (vs promedio 20)
  - return_1d, return_3d, return_7d
  - high_low_ratio, close_open_ratio

### Requirement: Handle Insufficient Data

El sistema SHALL retornar None si no hay suficientes datos para calcular features.

#### Scenario: Not enough data

- **WHEN** menos de 50 candles
- **THEN** retorna None

### Requirement: Feature Normalization

El sistema SHALL normalizar features para entrenamiento.

#### Scenario: Normalization

- **WHEN** se prepara dataset para entrenamiento
- **THEN** usa StandardScaler para normalizar

## ADDED Requirements

### Requirement: Label Generation

El sistema SHALL generar labels para entrenamiento.

#### Scenario: Generate labels

- **WHEN** se llama generate_labels(klines, threshold=2.0, horizon=10)
- **AND** price goes up > threshold% in next horizon candles
- **THEN** label = "BUY"
- **AND** price goes down > threshold% in next horizon candles
- **THEN** label = "SELL"
- **AND** otherwise label = "HOLD"