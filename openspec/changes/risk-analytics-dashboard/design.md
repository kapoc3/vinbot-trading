## Context

El sistema actual no provee métricas de riesgo en tiempo real. Necesitamos un dashboard que exponga estas métricas para monitoreo y toma de decisiones.

## Goals / Non-Goals

**Goals:**
- Calcular y exponer VaR (Value at Risk) 95%
- Trackear drawdown actual y máximo
- Mostrar exposición por símbolo
- Calcular Sharpe ratio histórico
- API para consumo del dashboard

**Non-Goals:**
- No guardará datos históricos de riesgo
- No predecirá riesgo futuro
- No incluirá charting (solo datos)

## Decisions

### D1: VaR Calculation

**Decisión**: Usar método histórico con window de 30 días.

**Rationale**: Simple, no asume distribución normal, estándar en la industria.

### D2: Metrics Update Frequency

**Decisión**: Calcular métricas cada vez que se actualiza el portfolio (no real-time).

**Rationale**: Cálculo de VaR es costoso computacionalmente.

### D3: API Design

**Decisión**: Un solo endpoint /analytics que devuelve todo el dashboard.

**Rationale**: Single request para el dashboard, más eficiente.

## Migration Plan

1. Añadir config de analytics
2. Crear risk metrics calculator
3. Crear position tracker
4. Crear API endpoint
5. Testing