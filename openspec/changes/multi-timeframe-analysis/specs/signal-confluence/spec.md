# Signal Confirmation

## Purpose

Lógica de confirmación de señales usando timeframes superiores.

## ADDED Requirements

### Requirement: EMA-Based Confirmation

El sistema SHALL usar EMA 20 de timeframes superiores para confirmar dirección de tendencia.

#### Scenario: BUY signal confirmed by higher timeframe

- **WHEN** señal es BUY (RSI < oversold en 1m) Y EMA 20 de 15m está por encima del precio actual
- **THEN** la señal se marca como "CONFIRMED" con nivel MEDIA

#### Scenario: SELL signal confirmed by higher timeframe

- **WHEN** señal es SELL (RSI > overbought en 1m) Y EMA 20 de 15m está por debajo del precio actual
- **THEN** la señal se marca como "CONFIRMED" con nivel MEDIA

#### Scenario: No confirmation

- **WHEN** EMA 20 de timeframe superior está en dirección opuesta a la señal
- **THEN** la señal se marca como "NOT_CONFIRMED" y se rechaza

### Requirement: Multi-Timeframe Confluence

El sistema SHALL evaluar confluencia entre múltiples timeframes.

#### Scenario: High confluence

- **WHEN** EMA 1h Y EMA 15m confirman la señal
- **THEN** nivel de confluencia = ALTA
- **AND** se puede usar posición completa

#### Scenario: Medium confluence

- **WHEN** solo EMA 15m confirma (1h no disponible o neutral)
- **THEN** nivel de confluencia = MEDIA
- **AND** usar 50% del tamaño de posición

#### Scenario: Low confluence

- **WHEN** ningún timeframe superior confirma
- **THEN** nivel de confluencia = BAJA
- **AND** señal rechazada (o usar 25% con stop más ajustado)

### Requirement: Trend Strength Assessment

El sistema SHALL evaluar la fuerza de la tendencia en timeframes superiores usando precio vs EMA.

#### Scenario: Strong trend

- **WHEN** precio está a más de 2% de distancia de EMA 20 en timeframe superior
- **THEN** tendencia es FUERTE

#### Scenario: Weak trend

- **WHEN** precio está a menos de 0.5% de distancia de EMA 20
- **THEN** tendencia es DÉBIL (considerar como ranging)

### Requirement: Confirmation Decision Output

El sistema SHALL retornar estructura con nivel de confirmación y ajuste de posición.

#### Scenario: Confirmation result

- **WHEN** se evalúa confirmación de señal
- **THEN** retornar:
  - confirmed: bool
  - confluence_level: "ALTA" | "MEDIA" | "BAJA"
  - position_multiplier: float (1.0, 0.5, 0.25)
  - reason: str (explicación de la decisión)
  - timeframe_details: dict (estado de cada timeframe)