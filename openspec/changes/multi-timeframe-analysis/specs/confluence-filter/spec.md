# Confluence Filter

## Purpose

Filtro que evalúa señales basándose en confluencia multi-timeframe antes de generar orden.

## ADDED Requirements

### Requirement: Pre-Trade Confluence Check

El sistema SHALL evaluar confluencia antes de ejecutar cualquier orden.

#### Scenario: Signal passes filter

- **WHEN** señal de estrategia pasa checks Y confluencia >= MIN_CONFLUENCE_LEVEL configurado
- **THEN** el filtro permite la señal con multiplicador de posición

#### Scenario: Signal blocked by filter

- **WHEN** confluencia < MIN_CONFLUENCE_LEVEL
- **THEN** el filtro bloquea la señal Y logged con reason

### Requirement: Dynamic Position Sizing

El sistema SHALL ajustar el tamaño de posición según nivel de confluencia.

#### Scenario: Full position

- **WHEN** confluencia ALTA
- **THEN** position_size = calculated_size * 1.0

#### Scenario: Half position

- **WHEN** confluencia MEDIA
- **THEN** position_size = calculated_size * 0.5

#### Scenario: Quarter position

- **WHEN** confluencia BAJA
- **THEN** position_size = calculated_size * 0.25 (si está habilitado)

### Requirement: Minimum Confluence Configuration

El sistema SHALL permitir configurar el nivel mínimo de confluencia aceptable.

#### Scenario: Strict mode

- **WHEN** MIN_CONFLUENCE_LEVEL = "ALTA"
- **THEN** solo se ejecutan señales con confluencia alta

#### Scenario: Permissive mode

- **WHEN** MIN_CONFLUENCE_LEVEL = "MEDIA"
- **THEN** se aceptan señales con confluencia media o alta

#### Scenario: Disabled

- **WHEN** MULTI_TF_ENABLED = False
- **THEN** se aceptan todas las señales (multiplicador = 1.0)

### Requirement: Confluence Metrics Logging

El sistema SHALL registrar métricas de confluencia para análisis.

#### Scenario: Log confluence metrics

- **WHEN** se evalúa una señal
- **THEN** el log incluye:
  - symbol
  - signal_type
  - confluence_level
  - ema_1h_direction
  - ema_15m_direction
  - position_multiplier
  - blocked: bool