# ML Training Pipeline

## Purpose

Pipeline de entrenamiento del modelo ML con datos históricos.

## ADDED Requirements

### Requirement: Train Model

El sistema SHALL entrenar modelo con datos históricos.

#### Scenario: Successful training

- **WHEN** se llama train(symbol, start_date, end_date)
- **THEN** retorna modelo entrenado Y guarda a archivo

#### Scenario: Training data insufficient

- **WHEN** menos de 1000 samples
- **THEN** lanza excepción

### Requirement: Model Configuration

El sistema SHALL usar Random Forest con parámetros específicos.

#### Scenario: Default config

- **WHEN** se entrena sin configuración
- **AND** n_estimators=100, max_depth=10, min_samples_split=20

### Requirement: Cross Validation

El sistema SHALL validar modelo con cross-validation.

#### Scenario: CV evaluation

- **WHEN** se entrena
- **AND** usa 5-fold CV
- **THEN** reporta accuracy, precision, recall, f1

### Requirement: Model Persistence

El sistema SHALL guardar modelo entrenado.

#### Scenario: Save model

- **WHEN** entrenamiento exitoso
- **AND** guarda a data/ml_models/{symbol}_model.pkl

## ADDED Requirements

### Requirement: Retrain Trigger

El sistema SHALL soportar retraining manual.

#### Scenario: Manual retrain

- **WHEN** se llama retrain(symbol)
- **THEN** re-entrena con datos actualizados