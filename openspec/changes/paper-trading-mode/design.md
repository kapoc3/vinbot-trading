## Context

El sistema actual ejecuta órdenes directamente en Binance. Para validar cambios sin riesgo, necesitamos un modo que simule todo el proceso de trading.

## Goals / Non-Goals

**Goals:**
- Simular ejecución de órdenes (fills, slippage, comisiones)
- Trackear balance y posiciones virtuales
- Logging detallado de decisiones
- Modo híbrido (algunos símbolos paper, otros real)
- Comparación de performance

**Non-Goals:**
- No se conectará realmente a Binance para ejecutar
- No guardará orders en Binance

## Decisions

### D1: Arquitectura

**Decisión**: Ejecutar el mismo flujo pero con orders simuladas en lugar de reales.

**Rationale**: Reutiliza toda la lógica existente, solo cambia la capa de ejecución.

### D2: Slippage Simulation

**Decisión**: Aplicar slippage configurable en simulaciones.

**Rationale**: Más realista que execution a precio exacto.

### D3: Hybrid Mode

**Decisión**: Por símbolo, no global.

**Rationale**: Permite comparar performance real vs paper en mismos símbolos.

## Migration Plan

1. Añadir config de paper mode
2. Modificar trading engine para simular
3. Añadir balance virtual
4. Añadir API de control
5. Testing