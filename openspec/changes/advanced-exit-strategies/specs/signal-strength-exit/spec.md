# Signal Strength Exit

## Purpose

Implementar exits basados en la fuerza de la señal original de entrada, permitiendo exits anticipados para señales débiles y exits más permisivos para señales fuertes.

## ADDED Requirements

### Requirement: Signal Strength Classification

El sistema SHALL clasificar la señal de entrada (BUY) en categorías de fuerza basadas en qué tan lejos estaba el indicador del umbral de señal.

#### Scenario: Strong signal - RSI deeply oversold

- **WHEN** RSI <= oversold - 10 (ej: RSI <= 20 para oversold de 30)
- **THEN** la señal se clasifica como "STRONG"

#### Scenario: Moderate signal - RSI near threshold

- **WHEN** RSI > oversold - 10 Y RSI <= oversold (ej: RSI entre 20 y 30)
- **THEN** la señal se clasifica como "MODERATE"

#### Scenario: Weak signal - RSI barely oversold

- **WHEN** RSI > oversold - 5 Y RSI <= oversold (ej: RSI entre 25 y 30)
- **THEN** la señal se clasifica como "WEAK"

### Requirement: Strength-Based Exit Timing

El sistema SHALL ajustar el nivel de exit según la clasificación de fuerza de la señal original.

#### Scenario: Strong signal - Let it ride

- **WHEN** signal_strength == "STRONG"
- **THEN** usar estrategia de exit normal (RSI overbought tradicional)

#### Scenario: Moderate signal - Earlier exit trigger

- **WHEN** signal_strength == "MODERATE"
- **THEN** activar exit cuando RSI llegue a overbought - 5 (ej: 65 en lugar de 70)

#### Scenario: Weak signal - Aggressive exit

- **WHEN** signal_strength == "WEAK"
- **THEN** activar exit cuando RSI llegue a overbought - 10 (ej: 60 en lugar de 70) O después de 2 horas

### Requirement: Signal Strength Persistence

El sistema SHALL persistir la clasificación de fuerza de la señal junto con el precio de entrada.

#### Scenario: Position stored

- **WHEN** se abre una posición con una señal BUY
- **THEN** el sistema almacena: entry_price, entry_time, signal_strength classification

#### Scenario: Position retrieved after restart

- **WHEN** se recupera una posición desde persistence después de un reinicio
- **THEN** el sistema también recupera signal_strength para usar en decisiones de exit

### Requirement: Signal Strength Calculation for Other Strategies

El sistema SHALL calcular signal_strength no solo para RSI sino también para otras estrategias.

#### Scenario: Bollinger Bands signal strength

- **WHEN** signal viene de Bollinger Bands (precio toca lower band)
- **THEN** strength se calcula por distancia al lower band: distance_to_lower / bandwidth

#### Scenario: MACD signal strength

- **WHEN** signal viene de MACD (crossover)
- **THEN** strength se calcula por magnitud del histogram en el momento del crossover