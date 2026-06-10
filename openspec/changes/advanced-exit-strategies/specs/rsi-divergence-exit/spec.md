# RSI Divergence Exit

## Purpose

Utilizar divergencias bajistas RSI como señal de salida anticipada, detectando cuando el precio hace nuevos máximos pero el RSI no confirma (indicando debilidad potencial del movimiento).

## ADDED Requirements

### Requirement: Bearish Divergence Detection

El sistema SHALL detectar divergencias bajistas comparando los últimos 5 candles para identificar cuando el precio hace un higher high pero el RSI hace un lower high.

#### Scenario: Bearish divergence detected

- **WHEN** el precio delúltimo close > precio del close hace 5 candles Y RSI actual < RSI hace 5 candles
- **THEN** el sistema marca una divergencia bajista como detectada

#### Scenario: No divergence

- **WHEN** el precio hace higher high Y RSI hace higher high (confirmación)
- **THEN** NO se genera señal de divergence exit

#### Scenario: Insufficient data

- **WHEN** hay menos de 5 candles de historia
- **THEN** el sistema no puede detectar divergencia y retorna None

### Requirement: Divergence Exit Signal

El sistema SHALL generar señal de SELL cuando se detecte una divergencia bajista y haya una posición abierta.

#### Scenario: Divergence with position

- **WHEN** bearish_divergence_detected == true Y position_open == true
- **THEN** el sistema genera señal de "DIVERGENCE_EXIT" con reason "bearish_divergence"

#### Scenario: Divergence without position

- **WHEN** bearish_divergence_detected == true Y position_open == false
- **THEN** el sistema NO genera señal (la divergecia solo aplica para exits)

### Requirement: Divergence Validation

El sistema SHALL validar que la divergencia sea significativa requiriendo una diferencia mínima del 3% entre los high del precio.

#### Scenario: Significant divergence

- **WHEN** price_high_diff >= 3% Y rsi_high_diff <= -2%
- **THEN** la divergencia se considera válida para señal de exit

#### Scenario: Insignificant divergence

- **WHEN** price_high_diff < 3% O rsi_high_diff > -2%
- **THEN** la divergencia se ignora (no genera señal)

### Requirement: Integration with Risk Manager

El sistema SHALL integrar la verificación de divergence exit en el flujo de risk_manager.check_sl_tp() como una condición adicional de exit.

#### Scenario: Risk manager check

- **WHEN** risk_manager.check_sl_tp() es llamado
- **THEN** el sistema evalúa: SL -> TP levels -> Trailing TP -> Divergence Exit -> RSI Overbought (priority order)