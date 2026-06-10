# ML Ensemble

## Purpose

Combinación depredicciones ML con estrategias tradicionales.

## ADDED Requirements

### Requirement: Ensemble Decision

El sistema SHALL combinar ML y estrategia tradicional.

#### Scenario: ML agrees with strategy

- **WHEN** ML prediction == strategy signal
- **THEN** return strategy signal con boost

#### Scenario: ML disagrees

- **WHEN** ML prediction != strategy signal
- **AND** ML confidence > 0.7
- **THEN** return ML prediction (trust ML)

#### Scenario: Low confidence

- **WHEN** ML confidence < 0.5
- **THEN** return strategy signal (trust traditional)

### Requirement: ML Integration in Strategy

El sistema SHALL integrar como filtro en DynamicStrategyProxy.

#### Scenario: ML enabled

- **WHEN** ML_ENABLED = True Y modelo disponible
- **THEN** evaluar predicción ML antes de ejecutar

#### Scenario: ML disabled

- **WHEN** ML_ENABLED = False
- **THEN** usar estrategia tradicional sin ML

## ADDED Requirements

### Requirement: Confidence Adjustment

El sistema SHALL ajustar tamaño de posición según confianza ML.

#### Scenario: High confidence

- **WHEN** ML confidence > 0.8
- **THEN** position_multiplier = 1.2

#### Scenario: Medium confidence

- **WHEN** 0.5 < ML confidence <= 0.8
- **THEN** position_multiplier = 1.0

#### Scenario: Low confidence

- **WHEN** ML confidence <= 0.5
- **THEN** position_multiplier = 0.8