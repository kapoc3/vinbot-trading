# Dynamic Partial Take Profit

## Purpose

Hacer los niveles de partial take profit dinámicos basándose en la volatilidad del mercado (ATR) para ser más realistas en mercados volátiles y más agresivos en mercados tranquilos.

## ADDED Requirements

### Requirement: Volatility-Adjusted TP Levels

El sistema SHALL ajustar los niveles de partial TP multiplicando los niveles base por un factor de volatilidad.

#### Scenario: High volatility

- **WHEN** ATR_pct (ATR/current_price * 100) > 2.0%
- **THEN** los niveles de TP se multiplican por (1 + (ATR_pct - 2) * 0.3) - ej: para 3% ATR, niveles suben ~30%

#### Scenario: Low volatility

- **WHEN** ATR_pct <= 1.0%
- **THEN** los niveles de TP se multiplican por 0.8 (más agresivos en mercados quietos)

#### Scenario: Normal volatility

- **WHEN** 1.0% < ATR_pct <= 2.0%
- **THEN** se usan los niveles de TP sin modificación

### Requirement: ATR-Based Threshold Calculation

El sistema SHALL calcular los umbrales de TP usando ATR relativo en lugar de porcentajes fijos.

#### Scenario: Calculate dynamic threshold

- **WHEN** se necesita calcular el nivel de TP para un nivel específico (ej: nivel 1)
- **THEN** threshold = entry_price * (1 + (base_pct * volatility_multiplier) / 100)

#### Scenario: Use traditional fallback

- **WHEN** ATR no está disponible (menos de 14 candles)
- **THEN** el sistema usa los niveles tradicionales (PARTIAL_TP_LEVELS sin modificación)

### Requirement: Dynamic Partial TP Persistence

El sistema SHALL persistir los niveles de partial TP calculados dinámicamente para mantener consistencia.

#### Scenario: Save calculated levels

- **WHEN** se abre una posición Y se calculan los niveles de TP dinámicos
- **THEN** el sistema guarda: base_levels, calculated_levels, volatility_at_entry en persistence

#### Scenario: Resume with saved levels

- **WHEN** se recupera una posición de persistence
- **THEN** el sistema usa los niveles calculados guardados (no recalcula, para mantener consistencia)

### Requirement: User-Controlled Volatility Adjustment

El sistema SHALL permitir al usuario habilitar/deshabilitar el ajuste de volatilidad a través de configuración.

#### Scenario: Feature enabled

- **WHEN** DYNAMIC_PARTIAL_TP_ENABLED == True
- **THEN** los niveles de TP se calculan dinámicamente según volatilidad

#### Scenario: Feature disabled

- **WHEN** DYNAMIC_PARTIAL_TP_ENABLED == False
- **THEN** se usan los niveles tradicionales de PARTIAL_TP_LEVELS sin modificación

### Requirement: Volatility Adjustment Visualization

El sistema SHALL registrar en logs los niveles de TP calculados mostrando el ajuste de volatilidad.

#### Scenario: Log dynamic levels

- **WHEN** se establecen los niveles de partial TP para una nueva posición
- **THEN** el log incluye: "Dynamic TP Levels: Base [1.0%, 2.0%, 3.0%] → Adjusted [1.3%, 2.6%, 3.9%] (ATR: 2.5%)"