# Time-Based Exit

## Purpose

Implementar exits basados en tiempo máximo de posición para evitar que las posiciones se mantengan demasiado tiempo en mercados laterales o sin momentum.

## ADDED Requirements

### Requirement: Maximum Hold Time Enforcement

El sistema SHALL cerrar automáticamente cualquier posición que supere el tiempo máximo configurado (MAX_HOLD_HOURS).

#### Scenario: Position exceeds max hold time

- **WHEN** una posición ha estado abierta por más de MAX_HOLD_HOURS desde la entrada
- **THEN** el sistema genera señal de "TIME_EXIT" y cierra la posición al precio de mercado

#### Scenario: Position within time limit

- **WHEN** una posición ha estado abierta por menos de MAX_HOLD_HOURS
- **THEN** el sistema NO considera time-based exit como señal

### Requirement: Time Tracking Persistence

El sistema SHALL persistir el timestamp de entrada de cada posición para mantener el tracking a través de reinicios del sistema.

#### Scenario: System restart

- **WHEN** el sistema se reinicia Y existe una posición previamente abierta
- **THEN** el sistema recupera el timestamp de entrada desde persistence Y continúa el tracking del tiempo

#### Scenario: New position opened

- **WHEN** se abre una nueva posición (orden BUY ejecutada)
- **THEN** el sistema registra el timestamp actual como entry_time para ese símbolo

### Requirement: Time Exit Cooldown

El sistema SHALL evitar nuevas entradas durante el cooldown configurado después de un time-based exit para evitar over-trading.

#### Scenario: After time exit

- **WHEN** se ejecuta un TIME_EXIT para un símbolo
- **THEN** el sistema activa un cooldown de 15 minutos para ese símbolo donde no se permiten nuevas señales de BUY

#### Scenario: Cooldown expired

- **WHEN** el cooldown ha expirado para un símbolo
- **THEN** el sistema permite nuevas señales de BUY para ese símbolo

### Requirement: Time-Based Exit Logging

El sistema SHALL registrar en logs cada evaluación de time-based exit incluyendo el tiempo transcurrido.

#### Scenario: Time check evaluation

- **WHEN** el risk_manager evalúa condiciones de exit para una posición abierta
- **THEN** el sistema incluye en el log: tiempo_transcurrido_horas, max_permitido, y decisión (exit/no_exit)