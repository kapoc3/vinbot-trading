# ML Prediction

## Purpose

Predicción en tiempo real usando modelo ML entrenado.

## ADDED Requirements

### Requirement: Load Model

El sistema SHALL cargar modelo entrenado desde archivo.

#### Scenario: Load success

- **WHEN** se llama load_model(symbol)
- **AND** modelo existe en data/ml_models/
- **THEN** carga modelo en memoria

#### Scenario: Model not found

- **WHEN** modelo no existe
- **THEN** retorna None (fallback a estrategia tradicional)

### Requirement: Predict

El sistema SHALL predecir señal para datos actuales.

#### Scenario: Successful prediction

- **WHEN** se llama predict(symbol, current_features)
- **AND** modelo cargado
- **THEN** retorna: "BUY", "SELL", "HOLD" o "HOLD" (default)

#### Scenario: Prediction probability

- **WHEN** se llama predict_with_proba(symbol, features)
- **THEN** retorna (signal, confidence) donde confidence es probabilidad

### Requirement: Fallback

El sistema SHALL usar estrategia tradicional si ML no está disponible.

#### Scenario: No model

- **WHEN** modelo no disponible
- **AND** predict() llamado
- **THEN** retorna None (indica fallback a estrategia)

## ADDED Requirements

### Requirement: Caching Predictions

El sistema SHALL cachear predicciones por período.

#### Scenario: Cache hit

- **WHEN** predictionRequesteda en mismo candle
- **AND** respuesta en cache
- **THEN** retorna cached prediction