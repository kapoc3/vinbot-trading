# Trailing Take Profit

## Purpose

Implementar un sistema de trailing take profit basado en ATR que ajusta automáticamente los niveles de salida según la volatilidad del mercado, permitiendo capturar más ganancias en tendencias fuertes.

## ADDED Requirements

### Requirement: Trailing Take Profit Activation

El sistema SHALL activar el trailing take profit cuando el profit actual alcance un umbral de activación configurable (TRAILING_TP_ACTIVATION_PCT).

#### Scenario: Activation at threshold

- **WHEN** el profit actual (calculated as ((current_price - entry_price) / entry_price) * 100) >= TRAILING_TP_ACTIVATION_PCT
- **THEN** el sistema activa el trailing take profit y establece el nivel inicial de TP al precio actual

#### Scenario: No activation below threshold

- **WHEN** el profit actual < TRAILING_TP_ACTIVATION_PCT
- **THEN** el trailing take profit permanece inactivo y el sistema usa los niveles de TP tradicionales

### Requirement: Dynamic Trailing Level Update

El sistema SHALL actualizar el nivel de trailing take profit cada vez que el precio alcance un nuevo máximo desde la entrada, usando: trailing_level = highest_price - (ATR * TRAILING_TP_ATR_MULTIPLIER).

#### Scenario: Price makes new high

- **WHEN** current_price > highest_price_since_entry Y trailing TP está activo
- **THEN** highest_price se actualiza al current_price Y trailing_level se recalcula

#### Scenario: Price stays below high

- **WHEN** current_price < highest_price_since_entry Y trailing TP está activo
- **THEN** trailing_level permanece sin cambios

### Requirement: Trailing Take Profit Trigger

El sistema SHALL generar señal de SELL cuando el precio caiga por debajo del trailing_level mientras el trailing TP está activo.

#### Scenario: Trailing TP triggered

- **WHEN** trailing TP está activo Y current_price <= trailing_level
- **THEN** el sistema genera señal de "TRAILING_TP" y ejecuta venta al precio de mercado

### Requirement: ATR Calculation for Trailing

El sistema SHALL usar ATR calculado con el período configurado (RSI_PERIOD por defecto 14) para determinar la distancia del trailing stop.

#### Scenario: ATR available

- **WHEN** ATR está disponible para el símbolo
- **THEN** trailing_distance = ATR * TRAILING_TP_ATR_MULTIPLIER

#### Scenario: ATR not available

- **WHEN** ATR no está disponible (menos datos de los necesarios)
- **THEN** el sistema usa un fallback de trailing distance del 1% del precio

## Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| TRAILING_TP_ENABLED | bool | True | Enable/disable trailing TP |
| TRAILING_TP_ATR_MULTIPLIER | float | 2.0 | ATR multiplier for distance |
| TRAILING_TP_ACTIVATION_PCT | float | 1.5 | Profit % to activate trailing |